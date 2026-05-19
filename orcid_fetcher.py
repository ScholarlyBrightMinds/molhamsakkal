#!/usr/bin/env python3
"""ORCID Public API fetcher.

Pulls every public section of an ORCID record (person bio, works, employments,
educations, peer-reviews, fundings, distinctions, services, memberships,
invited-positions, qualifications) using the 2-legged OAuth client_credentials
grant and writes the result to data/orcid/orcid.json.

Authentication
--------------
We register a Public API client once on the ORCID developer portal and obtain
a Client ID + Client Secret. At runtime we exchange them for an access token
scoped to /read-public — that token can fetch ANY ORCID record's public-facing
data. The credentials are passed in via env vars (GitHub Actions secrets);
they never appear in source or commits.

  ORCID_CLIENT_ID       — Client ID from orcid.org/developer-tools
  ORCID_CLIENT_SECRET   — matching secret
  ORCID_ID              — target record (defaults to ORCID_ID_DEFAULT)

Resilience
----------
Each section is fetched independently. A single 404 / 500 / network error
on one section never breaks the whole run — the offending section is simply
omitted from the output. The exit code is 1 only if we can't authenticate.

This is intentionally dependency-free (stdlib only) so the GitHub Actions
workflow doesn't need any pip install beyond the existing 'requests' for
the serpapi fetcher.
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

# Default target — overridden by ORCID_ID env var when fetching for another
# member from the same script.
ORCID_ID_DEFAULT = "0000-0001-6081-1284"  # Molham Sakkal

TOKEN_URL = "https://orcid.org/oauth/token"
API_BASE  = "https://pub.orcid.org/v3.0"

# Sections that make up an ORCID record. Order matters only for log
# readability; the order in the saved JSON follows the dict insertion order.
SECTIONS = [
    "person",             # name, biography, country, keywords, researcher-urls
    "works",              # publications & products
    "employments",        # current/past jobs
    "educations",         # degrees
    "qualifications",     # certificates, board exams
    "distinctions",       # awards, honors
    "fundings",           # grants
    "memberships",        # society memberships
    "peer-reviews",       # papers / proposals reviewed
    "services",           # editorial, committee, volunteer work
    "invited-positions",  # visiting / honorary positions
]

REPO_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "data" / "orcid"
OUTPUT_FILE = OUTPUT_DIR / "orcid.json"


# ─────────────────────────────────────────────────────────────────────────
# HTTP — small stdlib wrappers
# ─────────────────────────────────────────────────────────────────────────
def _post_form(url: str, fields: dict[str, str]) -> dict:
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _get_json(url: str, token: str) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    fetch failed: {url} ({e})", file=sys.stderr)
        return None


# ─────────────────────────────────────────────────────────────────────────
# Token + fetch
# ─────────────────────────────────────────────────────────────────────────
def get_access_token(client_id: str, client_secret: str) -> str:
    """Exchange the client credentials for a /read-public access token.

    ORCID issues these tokens with a 20-year lifetime, so we don't bother
    caching across runs — each weekly invocation gets a fresh one."""
    payload = _post_form(
        TOKEN_URL,
        {
            "client_id":     client_id,
            "client_secret": client_secret,
            "grant_type":    "client_credentials",
            "scope":         "/read-public",
        },
    )
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"token request returned no access_token: {payload}")
    return token


def fetch_all(orcid_id: str, token: str) -> dict[str, dict]:
    """Pull every section in SECTIONS, stash whatever succeeds."""
    out: dict[str, dict] = {}
    for section in SECTIONS:
        print(f"  fetching {section}…")
        data = _get_json(f"{API_BASE}/{orcid_id}/{section}", token)
        if data is not None:
            out[section] = data
        # Brief pause between requests — ORCID's published rate limit is
        # 24 requests/sec but their docs explicitly ask for politeness.
        time.sleep(0.25)
    return out


# ─────────────────────────────────────────────────────────────────────────
# Summary — derives a small "highlights" object the front-end can render
# without having to walk every section.
# ─────────────────────────────────────────────────────────────────────────
def _safe_count(section_data: dict | None, key: str) -> int:
    if not section_data:
        return 0
    items = section_data.get(key) or []
    return len(items) if isinstance(items, list) else 0


def _count_peer_reviews(pr_section: dict | None) -> int:
    """ORCID peer-reviews nest as journal-group → peer-review-group → summary.
    The headline number researchers expect to see is the count of individual
    reviews — i.e. the inner-most summary list, summed across all journals."""
    if not pr_section:
        return 0
    total = 0
    for journal in pr_section.get("group") or []:
        for review in journal.get("peer-review-group") or []:
            total += len(review.get("peer-review-summary") or [])
    return total


def build_summary(sections: dict[str, dict]) -> dict:
    """Distill commonly-displayed totals so the front-end doesn't walk JSON."""
    works        = sections.get("works", {})
    peer_reviews = sections.get("peer-reviews", {})
    employments  = sections.get("employments", {})
    educations   = sections.get("educations", {})
    fundings     = sections.get("fundings", {})
    distinctions = sections.get("distinctions", {})
    services     = sections.get("services", {})

    return {
        "works_count":        len(works.get("group") or []),
        "peer_reviews_count": _count_peer_reviews(peer_reviews),
        "employments_count":  _safe_count(employments,  "affiliation-group"),
        "educations_count":   _safe_count(educations,   "affiliation-group"),
        "fundings_count":     _safe_count(fundings,     "group"),
        "distinctions_count": _safe_count(distinctions, "affiliation-group"),
        "services_count":     _safe_count(services,     "affiliation-group"),
    }


# ─────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    client_id     = os.environ.get("ORCID_CLIENT_ID", "").strip()
    client_secret = os.environ.get("ORCID_CLIENT_SECRET", "").strip()
    orcid_id      = os.environ.get("ORCID_ID", ORCID_ID_DEFAULT).strip()

    if not client_id or not client_secret:
        print("ORCID_CLIENT_ID and ORCID_CLIENT_SECRET must be set in env", file=sys.stderr)
        return 1

    print(f"orcid_fetcher: target={orcid_id} at {datetime.now(timezone.utc).isoformat()}")

    try:
        token = get_access_token(client_id, client_secret)
    except Exception as e:
        print(f"  token exchange failed: {e}", file=sys.stderr)
        return 1
    print(f"  token acquired (len={len(token)})")

    sections = fetch_all(orcid_id, token)
    summary  = build_summary(sections)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "orcid_id":     orcid_id,
        "last_fetched": datetime.now(timezone.utc).isoformat(),
        "summary":      summary,
        "sections":     sections,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        f"  wrote {OUTPUT_FILE.relative_to(REPO_ROOT)} — "
        f"{summary['works_count']} works · "
        f"{summary['peer_reviews_count']} peer reviews · "
        f"{summary['employments_count']} employments · "
        f"{summary['educations_count']} educations"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
