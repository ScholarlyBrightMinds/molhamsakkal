#!/usr/bin/env python3
"""Bake the OpenAlex research-topics panel into about.html.

Reads data/openalex/openalex.json (produced by openalex_fetcher.py) and
patches an idempotent marker block:

    <!-- OPENALEX-PANEL-START -->...<!-- OPENALEX-PANEL-END -->

The panel shows the top OpenAlex "concepts" (research topics) as chips
sized by score, an open-access percentage badge, and a small caption
linking to the canonical OpenAlex author page.

Fails gracefully — missing JSON or zero concepts skips the patch.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT     = Path(__file__).resolve().parent
DATA_FILE     = REPO_ROOT / "data" / "openalex" / "openalex.json"
ABOUT_HTML    = REPO_ROOT / "about.html"

PANEL_RE = re.compile(
    r"<!--\s*OPENALEX-PANEL-START\s*-->.*?<!--\s*OPENALEX-PANEL-END\s*-->",
    re.DOTALL,
)


def _pct(numer: int | None, denom: int | None) -> int:
    if not numer or not denom:
        return 0
    return round((numer / denom) * 100)


def render_panel(payload: dict) -> str:
    summary = payload.get("summary") or {}
    concepts = summary.get("top_concepts") or []
    openalex_id = summary.get("openalex_id") or ""
    profile_url = openalex_id if openalex_id.startswith("http") else (
        f"https://openalex.org/{openalex_id}" if openalex_id else ""
    )

    oa_works     = summary.get("oa_works")    or 0
    total_pulled = summary.get("works_in_pull") or 0
    oa_pct       = _pct(oa_works, total_pulled)

    # Chip the top 6 concepts; size each chip by score so high-weight
    # topics visually dominate. The score is 0..1, we map to 0.85..1.18 rem.
    if concepts:
        chips = "".join(
            f'<span class="oa-chip" style="font-size:{0.82 + (c.get("score") or 0) * 0.36:.2f}rem">'
            f'{c.get("name") or "?"}'
            f'</span>'
            for c in concepts[:6]
            if c.get("name")
        )
    else:
        chips = ''

    if not chips:
        # Nothing meaningful to render
        return (
            '<section class="reveal openalex-panel" aria-label="OpenAlex topics" style="display:none"></section>'
        )

    badges = []
    if total_pulled:
        badges.append(
            f'<span class="oa-badge"><strong>{oa_pct}%</strong> open access</span>'
        )
    if summary.get("i10_index"):
        badges.append(
            f'<span class="oa-badge"><strong>i10-index</strong> {summary["i10_index"]}</span>'
        )
    if summary.get("cited_by_count"):
        badges.append(
            f'<span class="oa-badge"><strong>{summary["cited_by_count"]}</strong> verified citations</span>'
        )
    badges_html = "".join(badges)

    profile_link = (
        f'<a class="oa-profile-link" href="{profile_url}" target="_blank" rel="noopener">'
        f'View full OpenAlex profile →</a>' if profile_url else ''
    )

    return (
        '<section class="reveal openalex-panel" aria-label="OpenAlex research topics">'
        '<p class="sec-kicker">Research focus</p>'
        '<h2 class="sec-title">Topics by <em>OpenAlex</em>.</h2>'
        '<p class="oa-lede">Auto-derived from publication metadata indexed in OpenAlex — '
        'the larger the chip, the stronger the topic association.</p>'
        '<div class="oa-chips">' + chips + '</div>'
        + (f'<div class="oa-badges">{badges_html}</div>' if badges_html else '')
        + profile_link
        + '</section>'
    )


def main() -> int:
    if not DATA_FILE.exists():
        print(f"  {DATA_FILE.relative_to(REPO_ROOT)} missing — skipping")
        return 0
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  failed to parse {DATA_FILE.name}: {e}")
        return 0

    html = ABOUT_HTML.read_text(encoding="utf-8")
    panel = render_panel(payload)
    block = "<!-- OPENALEX-PANEL-START -->" + panel + "<!-- OPENALEX-PANEL-END -->"

    if PANEL_RE.search(html):
        new_html = PANEL_RE.sub(block, html)
    else:
        # First run — inject right before the ORCID panel so the "Verified
        # profile" comes after "Research focus" in reading order.
        anchor = "<!-- ORCID-PANEL-START -->"
        if anchor in html:
            new_html = html.replace(anchor, block + "\n    " + anchor, 1)
        else:
            new_html = html.replace("</main>", "    " + block + "\n\n</main>", 1)

    if new_html != html:
        ABOUT_HTML.write_text(new_html, encoding="utf-8")
        print(f"  patched {ABOUT_HTML.name}")
    else:
        print(f"  no change to {ABOUT_HTML.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
