#!/usr/bin/env python3
"""
build_html.py — Server-side renderer for SEO.

Runs after serpapi_fetcher.py inside the GitHub Actions workflow. Reads the
freshly-fetched data/serpapi/{serpapi,metrics}.json and bakes the publication
list + headline metrics + Schema.org JSON-LD into the static HTML files
BEFORE git commit. Result: Google's first crawl pass sees real publication
titles and citation counts in the served HTML, instead of empty divs.
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
PUBS_HTML  = REPO_ROOT / "publications.html"
SITE_BASE  = "https://scholarlybrightminds.github.io/molhamsakkal"


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


def _journal_name_from_venue(venue: str) -> str:
    if not venue:
        return ""
    m = re.split(r'\s+\d+\s*[(,]', venue, maxsplit=1)
    name = m[0].strip().rstrip(",")
    return name or venue.strip()


def render_article(p: dict) -> str:
    title    = escape(p.get("title", "").strip() or "Untitled")
    authors  = escape(p.get("authors", "").strip())
    venue    = (p.get("venue") or p.get("publication") or "").strip()
    venue_e  = escape(venue)
    cites    = int(p.get("cited_by") or 0)
    link     = p.get("link") or ""
    if link and not link.startswith(("http://", "https://")):
        link = ""
    link_attr = f' href="{escape(link)}" target="_blank" rel="noopener noreferrer"' if link else ""
    cites_block = (
        f'<span class="pub-cites">{cites} citation{"s" if cites != 1 else ""}</span>'
        if cites else ""
    )
    venue_block = f'<p class="pub-venue">{venue_e}</p>' if venue_e else ""
    return f"""        <article class="pub-item">
            <h3 class="pub-title"><a{link_attr}>{title}</a></h3>
            <p class="pub-authors">{authors}</p>
            {venue_block}
            <div class="pub-meta">{cites_block}</div>
        </article>"""


def render_articles_block(pubs: list[dict]) -> str:
    if not pubs:
        return '        <p class="pub-loading">No publications found.</p>'
    return "\n".join(render_article(p) for p in pubs)


def render_jsonld(pubs: list[dict]) -> str:
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
        "url": f"{SITE_BASE}/publications.html",
        "name": "Publications — Molham Sakkal",
        "isPartOf": {"@type": "WebSite", "url": f"{SITE_BASE}/"},
        "about": {
            "@type": "Person",
            "@id": f"{SITE_BASE}/#person",
            "name": "Molham Sakkal",
            "sameAs": [
        "https://scholar.google.com/citations?user=JO1OQj8AAAAJ&hl=en",
        "https://orcid.org/0000-0001-6081-1284"
            ]
        },
        "mainEntity": {
            "@type": "ItemList",
            "name": "Peer-reviewed publications by Molham Sakkal",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(items),
            "itemListElement": items
        }
    }
    return ('<script type="application/ld+json" id="publications-jsonld">\n'
            + json.dumps(payload, indent=2, ensure_ascii=False)
            + "\n</script>")


def patch_publications_html(pubs: list[dict], metrics: dict) -> None:
    if not PUBS_HTML.exists():
        print(f"[FAIL] {PUBS_HTML} missing")
        sys.exit(1)
    html = PUBS_HTML.read_text(encoding="utf-8")
    orig = html

    articles = render_articles_block(pubs)
    pattern = re.compile(
        r'(<section id="list-articles"[^>]*>)(.*?)(</section>)',
        re.DOTALL,
    )
    html = pattern.sub(rf'\1\n{articles}\n        \3', html)

    total = str(metrics.get("total_documents") or len(pubs) or "—")
    cites = str(metrics.get("total_citations")
                  or sum(int(p.get("cited_by") or 0) for p in pubs) or "—")
    hidx  = str(metrics.get("h_index") or "—")
    html = re.sub(r'(<span id="m-total">)[^<]*(</span>)',  rf'\g<1>{total}\g<2>', html)
    html = re.sub(r'(<span id="m-cites">)[^<]*(</span>)',  rf'\g<1>{cites}\g<2>', html)
    html = re.sub(r'(<span id="m-h">)[^<]*(</span>)',      rf'\g<1>{hidx}\g<2>',  html)

    new_jsonld = render_jsonld(pubs)
    jsonld_pattern = re.compile(
        r'<script type="application/ld\+json" id="publications-jsonld">.*?</script>',
        re.DOTALL,
    )
    html = jsonld_pattern.sub(new_jsonld, html)

    if html != orig:
        PUBS_HTML.write_text(html, encoding="utf-8")
        print(f"[OK] publications.html: {len(pubs)} articles, {total} pubs, {cites} cites, h={hidx}")
    else:
        print("[OK] publications.html: no changes (already up to date)")


def patch_index_chips(pubs: list[dict], metrics: dict) -> None:
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

    if total:
        new_label = f"{total} Publications · {cites} Citations"
        pat1 = re.compile(r'(\{\s*label:\s*")(\d+\s+Publications\s+·\s+\d+\s+Citations)(")')
        new_text = pat1.sub(rf'\g<1>{new_label}\g<3>', text, count=1)
        if new_text != text:
            changed.append(f'pubs+cites="{new_label}"')
            text = new_text

    if hidx:
        new_label = f"h-index {hidx}"
        pat2 = re.compile(r'(\{\s*label:\s*")(h-index\s+\d+)(")')
        new_text = pat2.sub(rf'\g<1>{new_label}\g<3>', text, count=1)
        if new_text != text:
            changed.append(f'h-index="{new_label}"')
            text = new_text

    if text != orig:
        cfg.write_text(text, encoding="utf-8")
        print(f"[OK] theme.config.js chips updated: {', '.join(changed)}")
    else:
        print("[OK] theme.config.js chips: no change")


def main() -> int:
    print(f"[build_html] starting at {datetime.now(timezone.utc).isoformat()}")
    pubs = load_publications()
    metrics = load_metrics()
    print(f"[build_html] loaded {len(pubs)} publications, metrics keys: {list(metrics.keys())}")
    patch_publications_html(pubs, metrics)
    patch_index_chips(pubs, metrics)
    print("[build_html] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
