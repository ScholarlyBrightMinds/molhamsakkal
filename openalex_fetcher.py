#!/usr/bin/env python3
"""OpenAlex fetcher.

OpenAlex is a free, open scholarly graph (https://openalex.org/) — no API
key, no rate limit for politely-tagged callers. We use it to gather
researcher-level metrics that complement ORCID (which gives editorial
activity) and Scholar (which gives the publication list):

  • Verified citation counts per work and per author
  • Concept tags (Computer Science → AI → Drug discovery, etc.) with
    inferred level + score — useful for a "research topics" chip set
  • Open-access status per work — counts how many of the publications
    are OA, which is a meaningful signal in modern academic profiles
  • Institutional affiliation history derived from co-author network
  • i10-index (works with ≥10 citations) — Scholar reports this for
    public profiles; OpenAlex computes it from raw citation data

Polite pool: OpenAlex asks unauthenticated callers to set a contact
email so they can reach out if the script misbehaves. We pass that in
as the OPENALEX_MAILTO env var; falling back to the repo owner's email.

Resilience: same pattern as orcid_fetcher.py — each request is
independent; a single failure never breaks the whole run.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Default target — overridden by env vars when fetching for other members.
ORCID_ID_DEFAULT      = "0000-0001-6081-1284"  # Molham Sakkal
OPENALEX_AUTHOR_ID    = "A5072660555"          # Molham Sakkal OpenAlex author ID
DISPLAY_NAME_DEFAULT  = "Molham Sakkal"
MAILTO_DEFAULT        = "Molham.sakkal@gmail.com"

API_BASE = "https://api.openalex.org"

REPO_ROOT   = Path(__file__).resolve().parent
OUTPUT_DIR  = REPO_ROOT / "data" / "openalex"
OUTPUT_FILE = OUTPUT_DIR / "openalex.json"


def _get_json(url: str, mailto: str) -> dict | None:
    """OpenAlex prefers the contact email in the User-Agent string OR as a
    `mailto=` query parameter. We use both for maximum politeness."""
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}mailto={urllib.parse.quote(mailto)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept":     "application/json",
            "User-Agent": f"sbm-openalex/1.0 (mailto:{mailto})",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    fetch failed: {url} ({e})", file=sys.stderr)
        return None


def fetch_author(
    *,
    explicit_id: str | None,
    orcid_id: str | None,
    display_name: str | None,
    mailto: str,
) -> dict | None:
    """Resolve an OpenAlex author with three strategies, in priority order:

    1. Explicit author ID (preferred — bypasses disambiguation issues).
    2. ORCID filter (works if the author has claimed their ORCID on OpenAlex).
    3. Display name search (used as last resort; not all OpenAlex entries
       have an ORCID attached, since they're built from Crossref ingestion).

    The script logs which strategy hit, so future debugging is straightforward
    when a researcher's OpenAlex entity moves or splits."""
    if explicit_id:
        print(f"  resolving by explicit OpenAlex id: {explicit_id}")
        data = _get_json(f"{API_BASE}/authors/{explicit_id}", mailto)
        if data:
            return data

    if orcid_id:
        print(f"  resolving by ORCID filter: {orcid_id}")
        page = _get_json(
            f"{API_BASE}/authors?filter=orcid:{urllib.parse.quote(orcid_id)}",
            mailto,
        )
        if page and page.get("results"):
            return page["results"][0]

    if display_name:
        print(f"  resolving by display-name search: {display_name}")
        page = _get_json(
            f"{API_BASE}/authors?search={urllib.parse.quote(display_name)}",
            mailto,
        )
        if page and page.get("results"):
            # Pick the most-cited entry — disambiguation: if two authors
            # share a name, the one with more cites is almost always the
            # researcher we care about.
            best = max(page["results"], key=lambda a: a.get("cited_by_count", 0))
            return best

    return None


def fetch_works(author_id: str, mailto: str, max_pages: int = 5) -> list[dict]:
    """Pull every work this author authored. Pages are 200 items by default;
    we cap at max_pages to keep the run bounded for prolific researchers."""
    out: list[dict] = []
    cursor = "*"
    page = 0
    while cursor and page < max_pages:
        url = (
            f"{API_BASE}/works?filter=author.id:{urllib.parse.quote(author_id)}"
            f"&per-page=200&cursor={urllib.parse.quote(cursor)}"
        )
        page_data = _get_json(url, mailto)
        if not page_data:
            break
        results = page_data.get("results") or []
        out.extend(results)
        meta = page_data.get("meta") or {}
        cursor = meta.get("next_cursor") or ""
        page += 1
        time.sleep(0.3)
    return out


# ─────────────────────────────────────────────────────────────────────────
# Summary — what the front-end actually wants to render
# ─────────────────────────────────────────────────────────────────────────
def build_summary(author: dict | None, works: list[dict]) -> dict:
    if not author:
        return {}

    summary_stats = author.get("summary_stats") or {}
    counts_by_year = author.get("counts_by_year") or []
    recent_year = counts_by_year[0] if counts_by_year else {}

    # Concept distribution — top ~6 by score gives a research-topic chip set.
    concepts = author.get("x_concepts") or []
    top_concepts = sorted(
        concepts, key=lambda c: c.get("score", 0), reverse=True
    )[:8]

    # Open-access stats — count how many works have open_access.is_oa True.
    oa_count = sum(
        1 for w in works
        if (w.get("open_access") or {}).get("is_oa")
    )
    works_with_doi = sum(1 for w in works if w.get("doi"))

    return {
        "openalex_id":      author.get("id"),
        "display_name":     author.get("display_name"),
        "works_count":      author.get("works_count"),
        "cited_by_count":   author.get("cited_by_count"),
        "h_index":          summary_stats.get("h_index"),
        "i10_index":        summary_stats.get("i10_index"),
        "mean_citedness":   summary_stats.get("2yr_mean_citedness"),
        "recent_year_works":  recent_year.get("works_count", 0),
        "recent_year_cites":  recent_year.get("cited_by_count", 0),
        "oa_works":         oa_count,
        "works_in_pull":    len(works),
        "works_with_doi":   works_with_doi,
        "top_concepts": [
            {
                "name":  c.get("display_name"),
                "score": c.get("score"),
                "level": c.get("level"),
                "id":    c.get("id"),
            }
            for c in top_concepts
        ],
    }


# ─────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    orcid_id     = os.environ.get("ORCID_ID", ORCID_ID_DEFAULT).strip()
    explicit_id  = os.environ.get("OPENALEX_AUTHOR_ID", OPENALEX_AUTHOR_ID).strip()
    display_name = os.environ.get("OPENALEX_DISPLAY_NAME", DISPLAY_NAME_DEFAULT).strip()
    mailto       = os.environ.get("OPENALEX_MAILTO", MAILTO_DEFAULT).strip()

    print(f"openalex_fetcher: orcid={orcid_id} explicit_id={explicit_id or '(none)'}")

    author = fetch_author(
        explicit_id=explicit_id or None,
        orcid_id=orcid_id or None,
        display_name=display_name or None,
        mailto=mailto,
    )
    if not author:
        print("  could not resolve author by any strategy — aborting", file=sys.stderr)
        return 1
    author_id = author.get("id")
    print(f"  resolved author: {author.get('display_name')} ({author_id})")

    works = fetch_works(author_id, mailto)
    print(f"  fetched {len(works)} works")

    summary = build_summary(author, works)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "orcid_id":     orcid_id,
        "last_fetched": datetime.now(timezone.utc).isoformat(),
        "summary":      summary,
        "author":       author,
        "works":        works,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        f"  wrote {OUTPUT_FILE.relative_to(REPO_ROOT)} — "
        f"{summary.get('works_count')} works · "
        f"{summary.get('cited_by_count')} citations · "
        f"h-index {summary.get('h_index')} · "
        f"i10 {summary.get('i10_index')} · "
        f"{summary.get('oa_works')} OA / {summary.get('works_in_pull')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
