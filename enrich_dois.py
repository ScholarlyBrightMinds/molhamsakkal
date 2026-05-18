#!/usr/bin/env python3
"""
enrich_dois.py - Resolve a DOI for each SerpAPI-fetched publication via Crossref.

Reads data/serpapi/serpapi.json (the weekly Google Scholar dump) and, for each
publication, queries Crossref's REST API (free, unauthenticated, polite-pool)
to find the matching DOI. Writes data/serpapi/dois.json as a cache so the
weekly cron only pays the Crossref cost for newly-added publications.

The DOI cache feeds build_html.py, which uses each DOI to render the Altmetric
attention-score donut next to that publication.

Match strategy (all three must hold for a DOI to be accepted):
  - Title similarity >= 0.85 (difflib.SequenceMatcher on lower-cased titles)
  - Year match within +/- 1 (Crossref's `published.date-parts[0][0]`)
  - First-author surname appears in any Crossref author family-name (case-fold)

Run locally:
    python enrich_dois.py
    python enrich_dois.py --refresh   # ignore cache, re-query all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

# Windows consoles default to cp1252, which can't encode characters like the
# non-breaking hyphen (U+2010) that show up in some scientific paper titles.
# Force UTF-8 with `errors="replace"` so a single odd glyph in a title preview
# never crashes a 140-paper run mid-way.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent
DATA_PUBS = REPO_ROOT / "data" / "serpapi" / "serpapi.json"
DATA_DOIS = REPO_ROOT / "data" / "serpapi" / "dois.json"

CROSSREF_BASE = "https://api.crossref.org/works"
USER_AGENT = (
    "scholarlybrightminds-doi-enricher/0.1 "
    "(+https://scholarlybrightminds.github.io; mailto:abdallah.abouhajal@scifiniti.com)"
)
REQUEST_TIMEOUT = 15.0
THROTTLE_SECONDS = 0.3
TITLE_SIM_THRESHOLD = 0.85
YEAR_TOLERANCE = 1


def pub_key(pub: dict) -> str:
    """Stable key per publication, surviving title/year updates on the same paper."""
    link = (pub.get("link") or "").strip()
    if link:
        return hashlib.sha1(link.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
    fallback = (pub.get("title") or "") + "|" + str(pub.get("year") or "")
    return hashlib.sha1(fallback.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


def first_author_surname(pub: dict) -> str:
    """SerpAPI's `authors` is 'A Abou Hajal, AZ Al Meslamani'.
    First author is everything up to the first comma; surname is everything
    after the first whitespace-separated token (the initials).
    """
    authors = (pub.get("authors") or "").strip()
    first = authors.split(",", 1)[0].strip()
    if not first:
        return ""
    tokens = first.split()
    if len(tokens) >= 2:
        return " ".join(tokens[1:]).strip()
    return first


def normalize_title(t: str) -> str:
    t = re.sub(r"\s+", " ", (t or "").lower()).strip()
    t = re.sub(r"[‘’“”]", "'", t)
    return t


def crossref_search(title: str, surname: str) -> list[dict]:
    """Query Crossref polite-pool for up to 3 candidates."""
    params = {"query.bibliographic": title, "rows": "3"}
    if surname:
        params["query.author"] = surname
    url = f"{CROSSREF_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        payload = json.load(resp)
    return ((payload.get("message") or {}).get("items") or [])


def best_match(candidates: list[dict], target_title: str, target_year: int | None,
               target_surname: str) -> tuple[dict | None, float]:
    """Pick the Crossref candidate that satisfies title-sim, year, and surname checks."""
    best = None
    best_score = 0.0
    norm_target = normalize_title(target_title)
    surname_cf = (target_surname or "").casefold().strip()

    for cand in candidates:
        cand_titles = cand.get("title") or []
        if not cand_titles:
            continue
        norm_cand = normalize_title(cand_titles[0])
        sim = SequenceMatcher(None, norm_target, norm_cand).ratio()
        if sim < TITLE_SIM_THRESHOLD:
            continue

        # Year sanity
        try:
            cand_year = int((cand.get("published") or cand.get("issued") or
                              cand.get("created") or {}).get("date-parts", [[None]])[0][0])
        except (TypeError, ValueError, IndexError):
            cand_year = None
        if target_year is not None and cand_year is not None:
            if abs(cand_year - target_year) > YEAR_TOLERANCE:
                continue

        # First-author surname sanity
        if surname_cf:
            authors = cand.get("author") or []
            family_names = " ".join((a.get("family") or "") for a in authors).casefold()
            if surname_cf not in family_names:
                continue

        if sim > best_score:
            best = cand
            best_score = sim

    return best, best_score


def resolve_one(pub: dict) -> dict | None:
    """Return {doi, confidence, title, year, source_url} or None if no good match."""
    title = (pub.get("title") or "").strip()
    if not title:
        return None
    try:
        year = int(pub.get("year") or 0) or None
    except (TypeError, ValueError):
        year = None
    surname = first_author_surname(pub)

    try:
        candidates = crossref_search(title, surname)
    except Exception as e:
        print(f"  [crossref-err] {title[:60]!r}: {e}", file=sys.stderr)
        return None

    match, score = best_match(candidates, title, year, surname)
    if not match:
        return None

    doi = (match.get("DOI") or "").strip()
    if not doi:
        return None
    return {
        "doi": doi,
        "confidence": round(score, 3),
        "matched_title": (match.get("title") or [""])[0],
        "matched_year": (match.get("published") or match.get("issued") or
                          {}).get("date-parts", [[None]])[0][0],
        "matched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve Crossref DOIs for SerpAPI publications.")
    ap.add_argument("--refresh", action="store_true",
                     help="Ignore cache and re-query every publication.")
    args = ap.parse_args()

    if not DATA_PUBS.exists():
        print(f"[FAIL] {DATA_PUBS} missing - run serpapi_fetcher.py first.", file=sys.stderr)
        return 1
    with DATA_PUBS.open(encoding="utf-8") as f:
        pubs: list[dict] = json.load(f)

    cache: dict[str, dict] = {}
    if DATA_DOIS.exists() and not args.refresh:
        try:
            with DATA_DOIS.open(encoding="utf-8") as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            print(f"[WARN] {DATA_DOIS} unreadable; starting fresh.", file=sys.stderr)
            cache = {}

    resolved = 0
    unresolved = 0
    skipped_cached = 0
    for pub in pubs:
        key = pub_key(pub)
        title_preview = (pub.get("title") or "")[:70]

        if key in cache and cache[key].get("doi") and not args.refresh:
            skipped_cached += 1
            continue

        info = resolve_one(pub)
        time.sleep(THROTTLE_SECONDS)
        if info:
            cache[key] = info
            resolved += 1
            print(f"  [OK] {info['doi']} (conf={info['confidence']:.2f})  {title_preview}")
        else:
            cache.setdefault(key, {})
            cache[key]["no_match_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            unresolved += 1
            print(f"  [--] no Crossref match  {title_preview}")

    DATA_DOIS.parent.mkdir(parents=True, exist_ok=True)
    DATA_DOIS.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    total = resolved + unresolved + skipped_cached
    print(
        f"\n[enrich_dois] {resolved} new, {unresolved} unresolved, "
        f"{skipped_cached} cached. Total publications: {total}. "
        f"Cache written to {DATA_DOIS.name}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
