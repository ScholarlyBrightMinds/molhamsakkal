#!/usr/bin/env python3
"""
SerpApi Google Scholar Fetcher for Molham Sakkal
Fetches all publications and metrics, saving JSON for the website.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

# ========== CONFIG ==========
SERPAPI_KEY       = os.getenv("SERPAPI_KEY", "").strip()
SCHOLAR_AUTHOR_ID = os.getenv("SCHOLAR_AUTHOR_ID", "JO1OQj8AAAAJ").strip()
# ============================

API_URL    = "https://serpapi.com/search.json"
OUTPUT_DIR = "data/serpapi"


def utc_now() -> str:
    """Clean ISO-8601 timestamp — no double-suffix bug."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(params: dict, retries: int = 3, backoff: float = 5.0) -> dict:
    """GET with retry/backoff. Raises on final failure."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(API_URL, params=params, timeout=45)
            r.raise_for_status()
            data = r.json()
            if data.get("error"):
                raise RuntimeError(f"SerpApi error: {data['error']}")
            return data
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  Attempt {attempt}/{retries} failed: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
    raise RuntimeError("All retries exhausted")


def fetch_author_profile() -> dict | None:
    """Fetch the author profile page — contains the citations table and h-index."""
    print(f"Fetching author profile for {SCHOLAR_AUTHOR_ID}...")
    try:
        data = _get({
            "engine":    "google_scholar_author",
            "author_id": SCHOLAR_AUTHOR_ID,
            "api_key":   SERPAPI_KEY,
            "hl":        "en",
            "no_cache":  "true",
        })
        print("  Author profile fetched.")
        return data
    except Exception as e:
        print(f"  Warning: Could not fetch author profile: {e}")
        return None


def fetch_all_articles() -> list:
    """Paginate through all articles on the author's Google Scholar page."""
    all_articles = []
    start = 0
    num   = 20

    print("Fetching articles...")

    while True:
        try:
            data = _get({
                "engine":    "google_scholar_author",
                "author_id": SCHOLAR_AUTHOR_ID,
                "api_key":   SERPAPI_KEY,
                "hl":        "en",
                "start":     start,
                "num":       num,
            })
        except Exception as e:
            print(f"  Fatal: article fetch failed at start={start}: {e}", file=sys.stderr)
            break

        page = data.get("articles", [])
        if not page:
            break

        all_articles.extend(page)
        print(f"  Page {start // num + 1}: +{len(page)} articles (total: {len(all_articles)})")

        if len(page) < num:
            break

        start += num
        time.sleep(0.5)

    return all_articles


def extract_metrics(profile: dict | None) -> dict:
    """
    Pull total_citations and h_index from the author profile's cited_by table.
    Returns zeros on any failure — caller should fall back to computed metrics.
    """
    if not profile:
        return {"total_citations": 0, "h_index": 0}

    table = profile.get("cited_by", {}).get("table", [])
    total_citations = 0
    h_index         = 0

    for item in table:
        if "citations" in item:
            total_citations = int(item["citations"].get("all", 0) or 0)
        if "indice_h" in item:          # SerpApi's actual key name
            h_index = int(item["indice_h"].get("all", 0) or 0)
        if "h_index" in item:           # fallback spelling
            h_index = int(item["h_index"].get("all", 0) or 0)

    print(f"  Extracted from profile — citations: {total_citations}, h-index: {h_index}")
    return {"total_citations": total_citations, "h_index": h_index}


def compute_metrics(publications: list) -> dict:
    """Derive citations and h-index directly from the publications list."""
    counts = sorted([int(p.get("cited_by") or 0) for p in publications], reverse=True)
    h      = sum(1 for i, c in enumerate(counts, 1) if c >= i)
    return {
        "total_citations": sum(counts),
        "h_index":         h,
    }


def normalize(articles: list) -> list:
    """Convert SerpApi article dicts to the shape expected by serpapi.v1.js."""
    pubs = []
    for a in articles:
        cited_raw = a.get("cited_by", {})
        cited_val = cited_raw.get("value") if isinstance(cited_raw, dict) else cited_raw
        pubs.append({
            "title":     (a.get("title") or "").strip(),
            "authors":   a.get("authors", ""),
            "venue":     (a.get("publication") or "").strip(),
            "year":      str(a.get("year", "")),
            "cited_by":  int(cited_val) if cited_val else 0,
            "link":      a.get("link", "#"),
            "author_id": SCHOLAR_AUTHOR_ID,
        })
    return pubs


def main() -> None:
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    if not SCHOLAR_AUTHOR_ID:
        print("ERROR: SCHOLAR_AUTHOR_ID is not set.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Starting SerpApi Scholar Fetch ===")

    # --- Articles (required) ---
    articles = fetch_all_articles()
    if not articles:
        print("FATAL: No articles fetched.", file=sys.stderr)
        sys.exit(1)

    publications = normalize(articles)

    pubs_path = os.path.join(OUTPUT_DIR, "serpapi.json")
    with open(pubs_path, "w", encoding="utf-8") as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(publications)} publications → {pubs_path}")

    # --- Metrics (with fallback) ---
    profile = fetch_author_profile()
    metrics = extract_metrics(profile)

    # If the API gave us zeros (failed silently), compute from the articles instead
    if not metrics["total_citations"] and not metrics["h_index"]:
        print("  Official metrics are zero — computing from publications as fallback...")
        metrics = compute_metrics(publications)
        source  = "computed_from_publications"
    else:
        source  = "serpapi_profile"

    final_metrics = {
        "total_documents": len(publications),
        "total_citations": metrics["total_citations"],
        "h_index":         metrics["h_index"],
        "author_id":       SCHOLAR_AUTHOR_ID,
        "source":          source,
        "last_updated":    utc_now(),
    }

    metrics_path = os.path.join(OUTPUT_DIR, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)
    print(f"  Saved metrics → {metrics_path}")

    print("=== Fetch Complete ===")
    print(f"  Publications : {final_metrics['total_documents']}")
    print(f"  Citations    : {final_metrics['total_citations']}")
    print(f"  h-index      : {final_metrics['h_index']}")
    print(f"  Source       : {source}")


if __name__ == "__main__":
    main()
