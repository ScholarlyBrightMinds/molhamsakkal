#!/usr/bin/env python3
"""Bake the ORCID-derived "Verified activity" panel into about.html.

Reads data/orcid/orcid.json (produced by orcid_fetcher.py) and patches a
small idempotent block inside about.html marked by HTML comment fences:

    <!-- ORCID-PANEL-START -->...<!-- ORCID-PANEL-END -->

The panel shows the ORCID iD with a deep link, headline counts (works,
peer reviews, employments, educations, fundings, distinctions, services),
and a "last synced" timestamp so visitors can see the data is live.

Failing gracefully:
- If data/orcid/orcid.json is missing or empty, we DO NOT touch the page —
  the markers stay in place so a future successful fetch can fill them.
- If a count is zero, we omit that pill (don't dilute the panel with empties).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent
ORCID_JSON = REPO_ROOT / "data" / "orcid" / "orcid.json"
ABOUT_HTML = REPO_ROOT / "about.html"

PANEL_RE = re.compile(
    r"<!--\s*ORCID-PANEL-START\s*-->.*?<!--\s*ORCID-PANEL-END\s*-->",
    re.DOTALL,
)


def _format_synced(iso: str) -> str:
    """Render the last_fetched ISO timestamp as a human date."""
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return iso[:10]


def render_panel(payload: dict) -> str:
    orcid_id    = payload.get("orcid_id", "")
    summary     = payload.get("summary") or {}
    last_synced = _format_synced(payload.get("last_fetched", ""))

    # Each pill is (label, count). Skip any with zero so the panel doesn't
    # advertise empty achievements.
    pill_specs: list[tuple[str, int]] = [
        ("works",        summary.get("works_count", 0)),
        ("peer reviews", summary.get("peer_reviews_count", 0)),
        ("employments",  summary.get("employments_count", 0)),
        ("educations",   summary.get("educations_count", 0)),
        ("fundings",     summary.get("fundings_count", 0)),
        ("distinctions", summary.get("distinctions_count", 0)),
        ("services",     summary.get("services_count", 0)),
    ]
    pills = "".join(
        f'<span class="orcid-pill"><strong>{count}</strong> {label}</span>'
        for label, count in pill_specs
        if count
    )

    orcid_link = (
        f'<a class="orcid-id" href="https://orcid.org/{orcid_id}" target="_blank" '
        f'rel="noopener" title="View on orcid.org">'
        f'<span class="orcid-logo" aria-hidden="true">iD</span>'
        f'<span class="orcid-id-text">{orcid_id}</span>'
        f'</a>'
        if orcid_id else ""
    )

    synced_p = (
        f'<p class="orcid-synced">Last synced {last_synced}</p>' if last_synced else ''
    )
    return (
        '<section class="reveal orcid-panel" aria-label="ORCID verified activity">'
        '<p class="sec-kicker">Verified profile</p>'
        '<h2 class="sec-title">ORCID <em>activity</em>.</h2>'
        '<p class="orcid-lede">Synced from the public ORCID record. Counts come straight from orcid.org and reflect what peer-review and editorial work is on file with the registry.</p>'
        '<div class="orcid-grid">'
        + orcid_link
        + '<div class="orcid-pills">' + pills + '</div>'
        '</div>'
        + synced_p
        + '</section>'
    )


def main() -> int:
    if not ORCID_JSON.exists():
        print(f"  {ORCID_JSON.relative_to(REPO_ROOT)} missing — skipping")
        return 0

    try:
        payload = json.loads(ORCID_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  failed to parse {ORCID_JSON.name}: {e}")
        return 0

    if not payload.get("summary"):
        print("  no summary in ORCID payload — skipping")
        return 0

    html = ABOUT_HTML.read_text(encoding="utf-8")
    panel = render_panel(payload)
    block = "<!-- ORCID-PANEL-START -->" + panel + "<!-- ORCID-PANEL-END -->"

    if PANEL_RE.search(html):
        new_html = PANEL_RE.sub(block, html)
    else:
        # First run — inject right before the closing </main> so the panel
        # appears below the awards section.
        new_html = html.replace("</main>", "    " + block + "\n\n</main>", 1)

    if new_html != html:
        ABOUT_HTML.write_text(new_html, encoding="utf-8")
        print(f"  patched {ABOUT_HTML.name}")
    else:
        print(f"  no change to {ABOUT_HTML.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
