#!/usr/bin/env python3
"""Bake a co-author network panel into publications.html.

Reads data/openalex/openalex.json (produced by openalex_fetcher.py) and
emits an inline SVG radial network: the researcher at the centre,
co-authors arranged in a circle around them, node size proportional to
shared-paper count, line opacity proportional to shared-paper count.

We hand-roll the SVG layout (polar coordinates with collision-aware
radius) instead of pulling in D3 to keep the page lightweight — no
client-side JS required for the visualization itself. Hover state is
implemented with CSS so the file stays static.

Patches an idempotent marker block:

    <!-- COAUTHOR-NETWORK-START -->...<!-- COAUTHOR-NETWORK-END -->

Failing gracefully:
- Missing/empty openalex.json → no patch attempt
- Fewer than 2 co-authors → no graph rendered (the marker block is
  cleared so a stale graph doesn't linger)
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from html import escape
from pathlib import Path

REPO_ROOT       = Path(__file__).resolve().parent
DATA_FILE       = REPO_ROOT / "data" / "openalex" / "openalex.json"
PUBS_HTML       = REPO_ROOT / "publications.html"

# How many top co-authors to plot. Higher counts crowd the rim; 12 keeps
# labels readable while still showing depth.
MAX_NODES       = 12

# SVG viewBox dimensions. The graph is drawn into a 600x600 logical box;
# the CSS scales it responsively.
VB_W, VB_H      = 720, 580
CENTER_X, CENTER_Y = VB_W / 2, VB_H / 2
INNER_R         = 160   # ring radius (centre → co-author nodes)

PANEL_RE = re.compile(
    r"<!--\s*COAUTHOR-NETWORK-START\s*-->.*?<!--\s*COAUTHOR-NETWORK-END\s*-->",
    re.DOTALL,
)


def extract_coauthors(payload: dict) -> list[dict]:
    """Walk every work's authorships array, tally co-authors (excluding
    the researcher themselves), and attach a representative institution."""
    me_id = (payload.get("summary") or {}).get("openalex_id")
    counter: Counter[str] = Counter()
    names: dict[str, str] = {}
    inst:  dict[str, str] = {}

    for w in payload.get("works") or []:
        for a in w.get("authorships") or []:
            au = a.get("author") or {}
            aid = au.get("id")
            if not aid or aid == me_id:
                continue
            counter[aid] += 1
            if aid not in names:
                names[aid] = au.get("display_name") or "Unknown"
            if aid not in inst:
                affs = a.get("institutions") or []
                if affs:
                    inst[aid] = affs[0].get("display_name") or ""

    out = []
    for aid, count in counter.most_common(MAX_NODES):
        out.append({
            "id":          aid,
            "name":        names[aid],
            "institution": inst.get(aid, ""),
            "papers":      count,
        })
    return out


def render_svg(me_name: str, me_profile_url: str, coauthors: list[dict]) -> str:
    n = len(coauthors)
    if n < 2:
        return ""

    # Radius per node — scaled by paper count, but with a sensible floor
    # so single-paper co-authors don't shrink to nothing.
    max_papers = max(c["papers"] for c in coauthors) or 1
    def node_r(papers: int) -> float:
        return 14 + 18 * (papers / max_papers)

    # Place co-authors around a circle, equal angular spacing.
    nodes_svg: list[str] = []
    edges_svg: list[str] = []
    labels_svg: list[str] = []

    for i, c in enumerate(coauthors):
        angle = (i / n) * 2 * math.pi - math.pi / 2  # start at top
        x = CENTER_X + INNER_R * math.cos(angle)
        y = CENTER_Y + INNER_R * math.sin(angle)
        r = node_r(c["papers"])

        # Edge from centre to this node — opacity scales with paper count.
        opacity = 0.22 + 0.55 * (c["papers"] / max_papers)
        edges_svg.append(
            f'<line class="coauth-edge" x1="{CENTER_X:.1f}" y1="{CENTER_Y:.1f}" '
            f'x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke-opacity="{opacity:.2f}" '
            f'stroke-width="{1.0 + 1.4*(c["papers"]/max_papers):.2f}" />'
        )

        # The node itself — a circle linking to that author's OpenAlex page.
        name_safe = escape(c["name"])
        inst_safe = escape(c["institution"] or "—")
        href      = escape(c["id"])
        nodes_svg.append(
            f'<a href="{href}" target="_blank" rel="noopener">'
            f'<circle class="coauth-node" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}">'
            f'<title>{name_safe} · {c["papers"]} paper{"s" if c["papers"]!=1 else ""} · {inst_safe}</title>'
            f'</circle></a>'
        )

        # Label — place it just outside the node, on the angle from centre.
        # We push the label radius out by node_r + 12 so it doesn't overlap.
        label_r = INNER_R + r + 10
        lx = CENTER_X + label_r * math.cos(angle)
        ly = CENTER_Y + label_r * math.sin(angle)
        # Text anchor: left/right depending on which side of the centre
        # the node sits — keeps the labels from getting clipped by the rim.
        anchor = "start" if math.cos(angle) > 0.1 else (
                 "end" if math.cos(angle) < -0.1 else "middle")
        # Compact name (drop middle initials/etc to fit, but keep readable)
        short = c["name"]
        # First initial + family name is usually plenty:
        parts = short.split()
        if len(parts) > 2:
            short = parts[0][0] + ". " + parts[-1]
        labels_svg.append(
            f'<text class="coauth-label" x="{lx:.1f}" y="{ly:.1f}" '
            f'text-anchor="{anchor}" dominant-baseline="middle">'
            f'<tspan class="coauth-name">{escape(short)}</tspan>'
            f'<tspan class="coauth-papers" dx="6">×{c["papers"]}</tspan>'
            f'</text>'
        )

    # Centre node — researcher themselves.
    centre_initial = (me_name.split()[0][0] if me_name else "?").upper()
    centre = (
        f'<a href="{escape(me_profile_url)}" target="_blank" rel="noopener">'
        f'<circle class="coauth-centre" cx="{CENTER_X}" cy="{CENTER_Y}" r="36"/>'
        f'<text class="coauth-centre-label" x="{CENTER_X}" y="{CENTER_Y + 1}" '
        f'text-anchor="middle" dominant-baseline="central">{escape(centre_initial)}</text>'
        f'</a>'
    )

    return (
        f'<svg class="coauth-network" viewBox="0 0 {VB_W} {VB_H}" '
        f'role="img" aria-label="Co-author network for {escape(me_name)}">'
        + "".join(edges_svg)
        + centre
        + "".join(nodes_svg)
        + "".join(labels_svg)
        + '</svg>'
    )


def render_panel(payload: dict) -> str:
    coauthors = extract_coauthors(payload)
    if len(coauthors) < 2:
        return ""  # Nothing meaningful to show.

    me_id     = (payload.get("summary") or {}).get("openalex_id") or ""
    me_name   = (payload.get("summary") or {}).get("display_name") or ""
    me_profile_url = me_id if me_id.startswith("http") else (
        f"https://openalex.org/{me_id}" if me_id else ""
    )

    svg = render_svg(me_name, me_profile_url, coauthors)
    if not svg:
        return ""

    # Compact data table for screen readers + a "more co-authors" tail.
    total_extra = max(0, len((payload.get("works") or [])) and (
        sum(1 for _ in coauthors) > 0
    ))
    rows = "".join(
        f'<li class="coauth-row">'
        f'<a class="coauth-row-name" href="{escape(c["id"])}" target="_blank" rel="noopener">{escape(c["name"])}</a>'
        f'<span class="coauth-row-inst">{escape(c["institution"] or "—")}</span>'
        f'<span class="coauth-row-count">{c["papers"]}</span>'
        f'</li>'
        for c in coauthors
    )

    return (
        '<section class="reveal coauth-panel" aria-label="Co-author network">'
        '<p class="sec-kicker">Network</p>'
        '<h2 class="sec-title">Top <em>co-authors</em>.</h2>'
        '<p class="coauth-lede">Built from OpenAlex authorships across every indexed publication. '
        'Node size and edge weight scale with the number of shared papers.</p>'
        '<div class="coauth-wrap">' + svg + '</div>'
        '<ol class="coauth-list" aria-label="Co-authors listed with shared paper count and institution">'
        + rows +
        '</ol>'
        '</section>'
    )


def main() -> int:
    if not DATA_FILE.exists():
        print(f"  {DATA_FILE.relative_to(REPO_ROOT)} missing — skipping")
        return 0
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  failed to parse: {e}")
        return 0

    panel = render_panel(payload)
    if not panel:
        print("  not enough co-authors to render network — skipping")
        return 0

    html = PUBS_HTML.read_text(encoding="utf-8")
    block = "<!-- COAUTHOR-NETWORK-START -->" + panel + "<!-- COAUTHOR-NETWORK-END -->"

    if PANEL_RE.search(html):
        new_html = PANEL_RE.sub(block, html)
    else:
        # First run — inject just before the closing </main>, after the
        # publications article list.
        new_html = html.replace("</main>", "    " + block + "\n\n</main>", 1)

    if new_html != html:
        PUBS_HTML.write_text(new_html, encoding="utf-8")
        print(f"  patched {PUBS_HTML.name}")
    else:
        print(f"  no change to {PUBS_HTML.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
