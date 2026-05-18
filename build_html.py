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
DATA_PUBS  = REPO_ROOT / "data" / "serpapi" / "serpapi.json"
DATA_METR  = REPO_ROOT / "data" / "serpapi" / "metrics.json"
DATA_DOIS  = REPO_ROOT / "data" / "serpapi" / "dois.json"
PUBS_HTML  = REPO_ROOT / "publications.html"
INDEX_HTML = REPO_ROOT / "index.html"
THEME_CFG  = REPO_ROOT / "theme.config.js"

ORG_BASE   = "https://scholarlybrightminds.github.io"

# Altmetric embed CDN — referenced once in publications.html <head>.
# Loading the script async makes the badge zero-cost for first paint.
ALTMETRIC_EMBED_SRC = "https://d1bxh8uas1mnw7.cloudfront.net/assets/embed.js"


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


def render_article(p: dict, doi: str | None = None) -> str:
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

    # Stats row: Altmetric donut + citation chip + year chip + DOI link.
    # Each chip is omitted gracefully when the underlying value is missing.
    stats_parts: list[str] = []

    if doi:
        doi_safe = escape(doi)
        # data-hide-no-mentions="true" tells Altmetric's embed script to remove
        # the badge entirely when no mentions exist for the DOI — avoids the
        # placeholder "?" donut that otherwise clutters the stats row.
        stats_parts.append(
            f'<div class="pub-altmetric altmetric-embed" '
            f'data-badge-type="donut" data-doi="{doi_safe}" '
            f'data-hide-no-mentions="true" '
            f'title="Altmetric attention score — click for the full mention breakdown"></div>'
        )

    if cites:
        stats_parts.append(
            f'<span class="pub-stat pub-stat-cites" title="Google Scholar citations">'
            f'<span class="pub-stat-icon" aria-hidden="true">&#9733;</span>'
            f'<span class="pub-stat-num">{cites}</span>'
            f'<span class="pub-stat-label">citation{"s" if cites != 1 else ""}</span>'
            f'</span>'
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

    return f"""        <article class="pub-item">
            <h3 class="pub-title"><a{link_attr}>{title}</a></h3>
            <p class="pub-authors">{authors}</p>
            {venue_block}
            {stats_block}
        </article>"""


def render_articles_block(pubs: list[dict], dois: dict) -> str:
    if not pubs:
        return '        <p class="pub-loading">No publications found.</p>'
    rendered = []
    for p in pubs:
        info = dois.get(_pub_doi_key(p)) or {}
        doi = info.get("doi") or None
        rendered.append(render_article(p, doi=doi))
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
        "name": f"Publications — {full_name}",
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
def _ensure_altmetric_script(html: str) -> str:
    """Idempotently inject the Altmetric embed.js script into <head> if absent.
    Placed just before </head> so it doesn't block the document parse."""
    if ALTMETRIC_EMBED_SRC in html:
        return html
    snippet = (
        f'<script async src="{ALTMETRIC_EMBED_SRC}" '
        f'data-altmetric-embed="scholarlybrightminds"></script>\n'
    )
    return html.replace("</head>", snippet + "</head>", 1)


def patch_publications_html(pubs: list[dict], metrics: dict, dois: dict, ident: dict) -> None:
    if not PUBS_HTML.exists():
        print(f"[FAIL] {PUBS_HTML} missing")
        sys.exit(1)
    html = PUBS_HTML.read_text(encoding="utf-8")
    orig = html

    # 0. Make sure the Altmetric embed script is in <head> (one-time, idempotent).
    html = _ensure_altmetric_script(html)

    # 1. Replace article list inner content
    articles = render_articles_block(pubs, dois)
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
    resolved_dois = sum(1 for v in dois.values() if v.get("doi"))
    print(f"[build_html] loaded {len(pubs)} publications, "
          f"{resolved_dois} DOIs, metrics keys: {list(metrics.keys())}")
    patch_publications_html(pubs, metrics, dois, ident)
    patch_index_chips(pubs, metrics)
    print("[build_html] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
