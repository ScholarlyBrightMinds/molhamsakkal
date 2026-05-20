#!/usr/bin/env python3
"""
build_html.py — Server-side renderer for SEO.

Runs after serpapi_fetcher.py inside the GitHub Actions workflow. Reads the
freshly-fetched data/serpapi/{serpapi,metrics}.json and bakes the publication
list + headline metrics into the static HTML files BEFORE git commit. Result:
Google's first crawl pass sees real publication titles and citation counts in
the served HTML, instead of empty divs that get filled by JS after page load.

What it touches (idempotent — safe to re-run):
  - publications.html
      * Replaces the inner content of <section id="list-articles">…</section>
        with real <article> blocks per publication.
      * Updates the <span id="m-total"> / m-cites / m-h text content.
      * Replaces the entire <script id="publications-jsonld"> block with the
        full Schema.org CollectionPage + ItemList of ScholarlyArticle JSON-LD.
  - index.html
      * Updates the first chip in the hero (the one with the publication +
        citation count) so the static HTML shows current metrics.

Markers / IDs the script looks for (do not rename without updating here):
  - <section id="list-articles" …>…</section>
  - <span id="m-total">, <span id="m-cites">, <span id="m-h">
  - <script type="application/ld+json" id="publications-jsonld">…</script>
  - In index.html: chips: [ { label: "<N> Publications · <M> Citations" }, …

Run locally:  python build_html.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent
DATA_PUBS    = REPO_ROOT / "data" / "serpapi" / "serpapi.json"
DATA_METR    = REPO_ROOT / "data" / "serpapi" / "metrics.json"
DATA_DOIS    = REPO_ROOT / "data" / "serpapi" / "dois.json"
DATA_TLDRS   = REPO_ROOT / "data" / "tldrs.json"
DATA_OPENALX = REPO_ROOT / "data" / "openalex" / "openalex.json"
PUBS_HTML  = REPO_ROOT / "publications.html"
INDEX_HTML = REPO_ROOT / "index.html"
THEME_CFG  = REPO_ROOT / "theme.config.js"

ORG_BASE   = "https://scholarlybrightminds.github.io"

# Altmetric embed CDN — paywalled since 2025-11-10 (unauthenticated calls
# return HTTP 403). Kept as a constant so _strip_altmetric_script can find
# and remove any leftover loader tag from a previous build.
ALTMETRIC_EMBED_SRC = "https://d1bxh8uas1mnw7.cloudfront.net/assets/embed.js"

# Dimensions Badge — by Digital Science (same parent as Altmetric).
# Free, no API key needed. Renders citation impact + recommendations +
# mentions as a circular donut. Replacement for Altmetric until that key
# arrives and we wire up a server-side prefetch.
DIMENSIONS_EMBED_SRC = "https://badge.dimensions.ai/badge.js"


# ─────────────────────────────────────────────────────────────────────────
# Per-member identity (self-configuring from theme.config.js + repo name)
# ─────────────────────────────────────────────────────────────────────────
def _grab(text: str, field: str) -> str | None:
    m = re.search(rf'{field}\s*:\s*"([^"]*)"', text)
    return m.group(1) if m else None


def load_identity() -> dict:
    """Read per-member identity from theme.config.js + repo folder name.
    Returns a dict the renderers can use without any hardcoded names."""
    repo_name = REPO_ROOT.name
    site_base = f"{ORG_BASE}/{repo_name}"
    full_name = repo_name
    scholar = orcid = ""
    if THEME_CFG.exists():
        text = THEME_CFG.read_text(encoding="utf-8")
        # First match wins for each — theme.config.js has nested blocks but the
        # values we want are unique enough across the file.
        m_full = re.search(r'fullName\s*:\s*"([^"]*)"', text)
        if m_full:
            full_name = m_full.group(1)
        m_scholar = re.search(r'scholar\s*:\s*"([^"]*)"', text)
        if m_scholar:
            scholar = m_scholar.group(1)
        m_orcid = re.search(r'orcid\s*:\s*"([^"]*)"', text)
        if m_orcid:
            orcid = m_orcid.group(1)
    same_as = []
    if scholar:
        same_as.append(f"https://scholar.google.com/citations?user={scholar}&hl=en")
    if orcid:
        same_as.append(f"https://orcid.org/{orcid}")
    return {
        "repo_name": repo_name,
        "site_base": site_base,
        "full_name": full_name,
        "scholar":   scholar,
        "orcid":     orcid,
        "same_as":   same_as,
    }


# ─────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────
def load_publications() -> list[dict]:
    if not DATA_PUBS.exists():
        print(f"[WARN] {DATA_PUBS} missing — nothing to render.")
        return []
    with DATA_PUBS.open(encoding="utf-8") as f:
        pubs = json.load(f)
    pubs.sort(key=lambda p: int(p.get("year") or 0), reverse=True)
    return pubs


def load_metrics() -> dict:
    if not DATA_METR.exists():
        return {}
    with DATA_METR.open(encoding="utf-8") as f:
        return json.load(f)


def load_dois() -> dict:
    """dois.json keyed by pub_key (hash of scholar link) -> {doi, confidence, ...}.
    See enrich_dois.py for the matching pipeline that produces this file."""
    if not DATA_DOIS.exists():
        return {}
    with DATA_DOIS.open(encoding="utf-8") as f:
        return json.load(f)


def load_tldrs() -> dict:
    """tldrs.json keyed by DOI -> {tldr, topics}. `topics` is a space-separated
    list of filter codes (ml, llms, review, pharm, thesis). Keys starting with
    '_' are ignored (used for inline documentation in the file)."""
    if not DATA_TLDRS.exists():
        return {}
    try:
        with DATA_TLDRS.open(encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARN] tldrs.json could not be parsed: {e}")
        return {}
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def load_openalex_cites() -> dict:
    """Return DOI -> list of {year, cited_by_count} from data/openalex/openalex.json.
    DOIs are normalised (lower-case, leading https://doi.org/ stripped) so the
    keys line up with what enrich_dois.py produces."""
    if not DATA_OPENALX.exists():
        return {}
    try:
        with DATA_OPENALX.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARN] openalex.json could not be parsed: {e}")
        return {}
    out: dict[str, list[dict]] = {}
    for w in data.get("works", []):
        doi = (w.get("doi") or "").strip().lower()
        if not doi:
            continue
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        history = w.get("counts_by_year") or []
        if history:
            out[doi] = sorted(history, key=lambda r: int(r.get("year") or 0))
    return out


def _render_sparkline(history: list[dict]) -> str:
    """Inline SVG sparkline of yearly citation counts.

    Produces a 72x22 viewBox polyline plus end-dot. Single-year papers get a
    single dot (no polyline). Zero-history papers get an empty string."""
    if not history:
        return ""
    years  = [int(r.get("year") or 0) for r in history]
    counts = [int(r.get("cited_by_count") or 0) for r in history]
    if not any(counts):
        return ""

    w, h, pad = 72, 22, 3
    inner_w = w - 2 * pad
    inner_h = h - 2 * pad

    cmax = max(counts) or 1
    if len(history) == 1:
        # Single-year papers — show a baseline + dot in the middle of the
        # canvas so the chip reads as "one year of data" rather than
        # ambiguously plotted at an edge.
        x = w / 2
        y = h / 2
        title = f"{years[0]}: {counts[0]} cite{'s' if counts[0] != 1 else ''}"
        return (
            f'<svg class="pub-spark" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title>'
            f'<line class="pub-spark-line" x1="{pad}" y1="{y:.1f}" '
            f'x2="{w - pad}" y2="{y:.1f}" '
            f'stroke-dasharray="2 2" opacity="0.5"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="pub-spark-dot"/>'
            f'</svg>'
        )

    span = max(years) - min(years) or 1
    pts = []
    for yr, c in zip(years, counts):
        px = pad + ((yr - min(years)) / span) * inner_w
        py = h - pad - (c / cmax) * inner_h
        pts.append(f"{px:.1f},{py:.1f}")
    polyline = " ".join(pts)
    end_x, end_y = pts[-1].split(",")
    total = sum(counts)
    breakdown = " · ".join(f"{y}: {c}" for y, c in zip(years, counts))
    title = f"Citations by year ({total} total) — {breakdown}"

    # Build area-under-curve as a soft fill for visual weight on dense histories
    area_pts = (
        f"{pad:.1f},{h - pad:.1f} " + polyline +
        f" {(pad + inner_w):.1f},{h - pad:.1f}"
    )
    return (
        f'<svg class="pub-spark" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{escape(title)}">'
        f'<title>{escape(title)}</title>'
        f'<polygon class="pub-spark-area" points="{area_pts}"/>'
        f'<polyline class="pub-spark-line" points="{polyline}"/>'
        f'<circle cx="{end_x}" cy="{end_y}" r="2.2" class="pub-spark-dot"/>'
        f'</svg>'
    )


# Heuristic topic fallback for publications without a DOI-keyed entry in
# tldrs.json. Run against the title (lower-cased). The first match wins.
_TOPIC_HEURISTICS = [
    ("ml",    ["machine learning", "automl", "autogluon", "fingerprint", "cheminformatics",
               "graph", "neural network", "deep learning", "ensemble"]),
    ("llms",  ["language model", "llm", "chatgpt", "transformer", "gpt"]),
    ("review",["review", "introduction to", "insights into", "barriers", "perspectives"]),
    ("pharm", ["pharmacy", "pharmacist", "rosmarinus", "essential oil", "covid",
               "allergic", "osce", "online learning"]),
]


def _infer_topics(title: str) -> str:
    """Best-effort topic tag for a paper missing from tldrs.json."""
    t = (title or "").lower()
    tags = []
    for tag, keywords in _TOPIC_HEURISTICS:
        if any(k in t for k in keywords):
            tags.append(tag)
    return " ".join(tags) if tags else "other"


def _pub_doi_key(pub: dict) -> str:
    """Mirror of enrich_dois.pub_key() — keep these two in sync."""
    import hashlib
    link = (pub.get("link") or "").strip()
    if link:
        return hashlib.sha1(link.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
    fallback = (pub.get("title") or "") + "|" + str(pub.get("year") or "")
    return hashlib.sha1(fallback.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────
# Render: per-publication <article> blocks (for #list-articles section)
# ─────────────────────────────────────────────────────────────────────────
def _journal_name_from_venue(venue: str) -> str:
    """SerpAPI's `venue` is the full citation string, e.g.
        'Journal of Medical Economics 27 (1), 304-308, 2024'
    Strip everything from the first volume-like token onward to get just the
    journal name. Fall back to the original venue if no pattern matches.
    """
    if not venue:
        return ""
    # First numeric token (volume) — drop it and everything after
    m = re.split(r'\s+\d+\s*[(,]', venue, maxsplit=1)
    name = m[0].strip().rstrip(",")
    return name or venue.strip()


def render_article(
    p: dict,
    doi: str | None = None,
    tldr_info: dict | None = None,
    cite_history: list[dict] | None = None,
) -> str:
    title    = escape(p.get("title", "").strip() or "Untitled")
    authors  = escape(p.get("authors", "").strip())
    venue    = (p.get("venue") or p.get("publication") or "").strip()
    venue_e  = escape(venue)
    year_raw = str(p.get("year") or "").strip()
    year     = escape(year_raw)
    cites    = int(p.get("cited_by") or 0)
    link     = p.get("link") or ""
    if link and not link.startswith(("http://", "https://")):
        link = ""
    link_attr = f' href="{escape(link)}" target="_blank" rel="noopener noreferrer"' if link else ""

    # Topic + TLDR (Tier-1 plain-language summary). Data attrs drive the
    # filter buttons; the <p class="pub-tldr"> block is what readers see.
    info = tldr_info or {}
    topics = info.get("topics") or _infer_topics(p.get("title", ""))
    tldr_html = (
        f'<p class="pub-tldr">{escape(info["tldr"])}</p>'
        if info.get("tldr") else ""
    )
    data_attrs = (
        f' data-year="{year}"' if year else ""
    ) + (
        f' data-topic="{escape(topics)}"' if topics else ""
    )

    # Stats row: Dimensions donut, Scholar citation chip, year chip,
    # DOI link. Each chip is omitted gracefully when the value is missing.
    stats_parts: list[str] = []

    if doi:
        doi_safe = escape(doi)
        # Dimensions Badge by Digital Science. Free, no API key, renders
        # for every DOI Dimensions has indexed.
        #   small_circle: ~32px circular donut
        #   hover-right:  mention/citation legend appears to the right on hover
        stats_parts.append(
            f'<span class="pub-dimensions __dimensions_badge_embed__" '
            f'data-doi="{doi_safe}" '
            f'data-style="small_circle" '
            f'data-legend="hover-right" '
            f'title="Dimensions citation impact (click for details)"></span>'
        )

    if cites:
        stats_parts.append(
            f'<span class="pub-stat pub-stat-cites" title="Google Scholar citations">'
            f'<span class="pub-stat-icon" aria-hidden="true">&#9733;</span>'
            f'<span class="pub-stat-num">{cites}</span>'
            f'<span class="pub-stat-label">citation{"s" if cites != 1 else ""}</span>'
            f'</span>'
        )

    spark_svg = _render_sparkline(cite_history or [])
    if spark_svg:
        stats_parts.append(
            f'<span class="pub-stat pub-stat-spark" '
            f'title="Yearly citation trend (OpenAlex)">{spark_svg}</span>'
        )

    if year:
        stats_parts.append(
            f'<span class="pub-stat pub-stat-year" title="Year of publication">'
            f'<span class="pub-stat-icon" aria-hidden="true">&#128197;</span>'
            f'<span class="pub-stat-num">{year}</span>'
            f'</span>'
        )

    if doi:
        doi_safe = escape(doi)
        stats_parts.append(
            f'<a class="pub-stat pub-stat-doi" '
            f'href="https://doi.org/{doi_safe}" target="_blank" rel="noopener noreferrer" '
            f'title="Open at publisher via DOI">'
            f'<span class="pub-stat-icon" aria-hidden="true">&#128279;</span>'
            f'<span class="pub-stat-label">DOI</span>'
            f'</a>'
        )

    stats_block = (
        '<div class="pub-meta">\n            '
        + "\n            ".join(stats_parts)
        + '\n        </div>'
        if stats_parts else '<div class="pub-meta"></div>'
    )
    venue_block = f'<p class="pub-venue">{venue_e}</p>' if venue_e else ""

    return f"""        <article class="pub-item"{data_attrs}>
            <h3 class="pub-title"><a{link_attr}>{title}</a></h3>
            <p class="pub-authors">{authors}</p>
            {tldr_html}
            {venue_block}
            {stats_block}
        </article>"""


def render_articles_block(pubs: list[dict], dois: dict, tldrs: dict, oa_cites: dict) -> str:
    if not pubs:
        return '        <p class="pub-loading">No publications found.</p>'
    rendered = []
    for p in pubs:
        doi_info = dois.get(_pub_doi_key(p)) or {}
        doi = doi_info.get("doi") or None
        tldr_info = tldrs.get(doi) if doi else None
        cite_history = oa_cites.get((doi or "").lower()) if doi else None
        rendered.append(render_article(
            p, doi=doi, tldr_info=tldr_info, cite_history=cite_history
        ))
    return "\n".join(rendered)


# ─────────────────────────────────────────────────────────────────────────
# Render: Schema.org JSON-LD block for publications.html
# ─────────────────────────────────────────────────────────────────────────
def render_jsonld(pubs: list[dict], dois: dict, ident: dict) -> str:
    site_base = ident["site_base"]
    full_name = ident["full_name"]
    items = []
    for i, p in enumerate(pubs, start=1):
        venue_raw = (p.get("venue") or p.get("publication") or "").strip()
        journal   = _journal_name_from_venue(venue_raw)
        article = {
            "@type": "ScholarlyArticle",
            "name": p.get("title", "").strip(),
            "headline": p.get("title", "").strip(),
            "datePublished": str(p.get("year") or ""),
            "author": [{"@type": "Person", "name": a.strip()}
                          for a in (p.get("authors") or "").split(",")
                          if a.strip()],
        }
        if journal:
            article["isPartOf"] = {"@type": "Periodical", "name": journal}
        if p.get("link"):
            article["url"] = p["link"]
        # Surface DOI as both identifier and sameAs — Google + Crossref prefer this.
        info = dois.get(_pub_doi_key(p)) or {}
        doi = info.get("doi")
        if doi:
            article["identifier"] = {"@type": "PropertyValue", "propertyID": "doi", "value": doi}
            article["sameAs"] = f"https://doi.org/{doi}"
        cites = int(p.get("cited_by") or 0)
        if cites:
            article["interactionStatistic"] = {
                "@type": "InteractionCounter",
                "interactionType": "https://schema.org/CitationAction",
                "userInteractionCount": cites
            }
        items.append({"@type": "ListItem", "position": i, "item": article})

    payload = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "url": f"{site_base}/publications.html",
        "name": f"Publications · {full_name}",
        "isPartOf": {
            "@type": "WebSite",
            "url": f"{site_base}/"
        },
        "about": {
            "@type": "Person",
            "@id": f"{site_base}/#person",
            "name": full_name,
            "sameAs": ident["same_as"],
        },
        "mainEntity": {
            "@type": "ItemList",
            "name": f"Peer-reviewed publications by {full_name}",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(items),
            "itemListElement": items
        }
    }
    return ('<script type="application/ld+json" id="publications-jsonld">\n'
            + json.dumps(payload, indent=2, ensure_ascii=False)
            + "\n</script>")


# ─────────────────────────────────────────────────────────────────────────
# Patch: publications.html
# ─────────────────────────────────────────────────────────────────────────
def _strip_altmetric_script(html: str) -> str:
    """Remove the Altmetric embed.js loader if a previous build left it in
    <head>. Altmetric's free badges API was paywalled on 2025-11-10 and now
    returns HTTP 403 for unauthenticated callers, so loading this script
    only produces console errors and no rendered badges. Re-enable once
    we have a registered Altmetric API key AND a server-side prefetch
    pipeline (so the key isn't exposed in page source)."""
    return re.sub(
        r'\s*<script[^>]*' + re.escape(ALTMETRIC_EMBED_SRC) + r'[^>]*></script>',
        '',
        html
    )


def _ensure_dimensions_script(html: str) -> str:
    """Idempotently inject the Dimensions Badge loader into <head>."""
    snippet = f'<script async src="{DIMENSIONS_EMBED_SRC}" charset="utf-8"></script>'
    if DIMENSIONS_EMBED_SRC in html:
        return html
    return html.replace("</head>", snippet + "\n</head>", 1)


def patch_publications_html(
    pubs: list[dict],
    metrics: dict,
    dois: dict,
    tldrs: dict,
    oa_cites: dict,
    ident: dict,
) -> None:
    if not PUBS_HTML.exists():
        print(f"[FAIL] {PUBS_HTML} missing")
        sys.exit(1)
    html = PUBS_HTML.read_text(encoding="utf-8")
    orig = html

    # 0. Strip the broken Altmetric loader (paywalled 2025-11-10) and inject
    #    the Dimensions Badge loader in its place.
    html = _strip_altmetric_script(html)
    html = _ensure_dimensions_script(html)

    # 1. Replace article list inner content
    articles = render_articles_block(pubs, dois, tldrs, oa_cites)
    pattern = re.compile(
        r'(<section id="list-articles"[^>]*>)(.*?)(</section>)',
        re.DOTALL
    )
    html = pattern.sub(rf'\1\n{articles}\n        \3', html)

    # 2. Replace metrics span text content
    total = str(metrics.get("total_documents") or len(pubs) or "—")
    cites = str(metrics.get("total_citations")
                  or sum(int(p.get("cited_by") or 0) for p in pubs) or "—")
    hidx  = str(metrics.get("h_index") or "—")
    html = re.sub(r'(<span id="m-total">)[^<]*(</span>)',  rf'\g<1>{total}\g<2>', html)
    html = re.sub(r'(<span id="m-cites">)[^<]*(</span>)',  rf'\g<1>{cites}\g<2>', html)
    html = re.sub(r'(<span id="m-h">)[^<]*(</span>)',      rf'\g<1>{hidx}\g<2>',  html)

    # 3. Replace JSON-LD script block (idempotent — match by id)
    new_jsonld = render_jsonld(pubs, dois, ident)
    jsonld_pattern = re.compile(
        r'<script type="application/ld\+json" id="publications-jsonld">.*?</script>',
        re.DOTALL
    )
    html = jsonld_pattern.sub(new_jsonld, html)

    if html != orig:
        PUBS_HTML.write_text(html, encoding="utf-8")
        resolved = sum(1 for p in pubs if dois.get(_pub_doi_key(p), {}).get("doi"))
        print(f"[OK] publications.html: {len(pubs)} articles, {resolved} with DOI badges, "
              f"{total} pubs, {cites} cites, h={hidx}")
    else:
        print("[OK] publications.html: no changes (already up to date)")


# ─────────────────────────────────────────────────────────────────────────
# Patch: index.html — first chip in theme.config.js gets live metrics
# ─────────────────────────────────────────────────────────────────────────
def patch_index_chips(pubs: list[dict], metrics: dict) -> None:
    """Patch the metric-bearing chips in theme.config.js. Two chips currently
    auto-update from each Monday's SerpApi fetch:
      1. "<N> Publications · <M> Citations"  ← total docs + citation count
      2. "h-index <N>"                       ← Scholar h-index

    Hardcoded chips ("4× Corresponding Author", awards, education) are left
    alone — they don't change with citation data."""
    cfg = REPO_ROOT / "theme.config.js"
    if not cfg.exists():
        return
    text = cfg.read_text(encoding="utf-8")
    orig = text
    changed: list[str] = []

    total = metrics.get("total_documents") or len(pubs)
    cites = (metrics.get("total_citations")
              or sum(int(p.get("cited_by") or 0) for p in pubs))
    hidx  = metrics.get("h_index")

    # Chip 1: Publications · Citations
    if total:
        new_label = f"{total} Publications · {cites} Citations"
        pat1 = re.compile(
            r'(\{\s*label:\s*")(\d+\s+Publications\s+·\s+\d+\s+Citations)(")',
        )
        new_text = pat1.sub(rf'\g<1>{new_label}\g<3>', text, count=1)
        if new_text != text:
            changed.append(f'pubs+cites="{new_label}"')
            text = new_text

    # Chip 2: h-index
    if hidx:
        new_label = f"h-index {hidx}"
        pat2 = re.compile(
            r'(\{\s*label:\s*")(h-index\s+\d+)(")',
        )
        new_text = pat2.sub(rf'\g<1>{new_label}\g<3>', text, count=1)
        if new_text != text:
            changed.append(f'h-index="{new_label}"')
            text = new_text

    if text != orig:
        cfg.write_text(text, encoding="utf-8")
        print(f"[OK] theme.config.js chips updated: {', '.join(changed)}")
    else:
        print("[OK] theme.config.js chips: no change (already current)")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    print(f"[build_html] starting at {datetime.now(timezone.utc).isoformat()}")
    ident = load_identity()
    print(f"[build_html] identity: {ident['full_name']} @ {ident['site_base']}")
    pubs = load_publications()
    metrics = load_metrics()
    dois = load_dois()
    tldrs = load_tldrs()
    oa_cites = load_openalex_cites()
    resolved_dois = sum(1 for v in dois.values() if v.get("doi"))
    print(f"[build_html] loaded {len(pubs)} publications, "
          f"{resolved_dois} DOIs, {len(tldrs)} TLDRs, "
          f"{len(oa_cites)} OpenAlex cite histories, "
          f"metrics keys: {list(metrics.keys())}")
    patch_publications_html(pubs, metrics, dois, tldrs, oa_cites, ident)
    patch_index_chips(pubs, metrics)
    print("[build_html] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
