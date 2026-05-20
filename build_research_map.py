#!/usr/bin/env python3
"""
build_research_map.py — Research-map graph generator.

Reads ``data/openalex/openalex.json`` and bakes:

1. A SEO-friendly fallback SVG inside ``<section id="research-map">`` on
   ``research.html`` — pre-positioned nodes (central researcher + concepts +
   topics) drawn with semantic ``<text>`` labels so Google can read every
   concept term and crawlers without JS still see real content.

2. An embedded ``<script type="application/json" id="research-map-data">``
   block carrying the graph (nodes + weighted edges). The client-side
   ``research-map.js`` reads this and runs a small force-directed solver
   on top of the static layout, adding hover highlight + drag.

Data shape exported to the JS layer::

    {
      "center": {"id": "me", "label": "Abdallah's research", "kind": "center"},
      "concepts": [{"id": "c-medicine", "label": "Medicine",
                    "kind": "concept", "score": 0.81}, ...],
      "topics":   [{"id": "t-comp-drug-discovery",
                    "label": "Computational Drug Discovery Methods",
                    "kind": "topic", "count": 6,
                    "concept_id": "c-drug-discovery"}, ...],
      "edges":    [{"a": "me", "b": "c-medicine", "weight": 0.81},
                   {"a": "t-comp-drug-discovery",
                    "b": "c-drug-discovery", "weight": 4}, ...]
    }

The script is idempotent (markers + content-equal short-circuit) so it can
re-run on every weekly cron without producing noisy diffs.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from html import escape
from pathlib import Path

REPO_ROOT     = Path(__file__).resolve().parent
DATA_OPENALX  = REPO_ROOT / "data" / "openalex" / "openalex.json"
RESEARCH_HTML = REPO_ROOT / "research.html"

# Marker comments make the bake idempotent.
MARK_BEGIN = "<!-- RESEARCH-MAP:BEGIN -->"
MARK_END   = "<!-- RESEARCH-MAP:END -->"

# How many of each kind to surface in the map. The author has 5 concepts and
# 5 topics in OpenAlex right now; widening these caps lets the map grow as
# the publication list grows.
N_CONCEPTS = 5
N_TOPICS   = 6

# SVG canvas — matches the section CSS. The JS layer uses these to seed
# initial node positions before the simulation runs.
W, H = 1000, 560
CENTER_R   = 64
CONCEPT_R  = 38
TOPIC_R    = 26


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def _build_graph(data: dict) -> dict:
    """Compute the {center, concepts, topics, edges} payload from OpenAlex."""
    author = data.get("author") or {}
    works  = data.get("works")  or []
    full_name = author.get("display_name") or author.get("full_name") or "Researcher"

    # ── Concepts (top-level disciplines) ──────────────────────────────
    raw_concepts = author.get("x_concepts") or []
    raw_concepts = sorted(
        raw_concepts, key=lambda c: float(c.get("score") or 0), reverse=True
    )[:N_CONCEPTS]
    concepts = []
    concept_id_by_label: dict[str, str] = {}
    for c in raw_concepts:
        label = (c.get("display_name") or "").strip()
        if not label:
            continue
        cid = "c-" + _slugify(label)
        concepts.append({
            "id":    cid,
            "label": label,
            "kind":  "concept",
            "score": float(c.get("score") or 0),
        })
        concept_id_by_label[label] = cid

    # ── Topics ────────────────────────────────────────────────────────
    raw_topics = author.get("topics") or []
    raw_topics = sorted(
        raw_topics, key=lambda t: int(t.get("count") or 0), reverse=True
    )[:N_TOPICS]

    # For each topic, count how often each top-level concept co-occurs in
    # the same work. The most-correlated concept becomes the topic's
    # "primary" — used both for the static layout (cluster the topic near
    # its parent concept) and as the edge endpoint.
    topic_concept_counts: dict[str, Counter] = {}
    for w in works:
        w_topics = {(t.get("display_name") or "").strip()
                    for t in (w.get("topics") or [])
                    if t.get("display_name")}
        # Walk up the topic hierarchy too — OpenAlex concepts on a work
        # are messy ("Drug", "Computer science", "Tumor progression") and
        # don't always include the author's top-level concepts. So fall
        # back to a fuzzy match against the author's top-level set.
        w_concept_labels = set()
        for c in (w.get("concepts") or []):
            cl = (c.get("display_name") or "").strip()
            if not cl:
                continue
            # Prefer exact match against the author's top concepts.
            if cl in concept_id_by_label:
                w_concept_labels.add(cl)
            else:
                # Token-overlap fallback (e.g. "Artificial intelligence" on
                # a work → "Machine learning" in author concepts).
                cl_low = cl.lower()
                for top in concept_id_by_label:
                    if (cl_low in top.lower() or top.lower() in cl_low):
                        w_concept_labels.add(top)
        for tl in w_topics:
            counts = topic_concept_counts.setdefault(tl, Counter())
            for cl in w_concept_labels:
                counts[cl] += 1

    topics = []
    for t in raw_topics:
        label = (t.get("display_name") or "").strip()
        if not label:
            continue
        # Pick the most-correlated top-level concept; fall back to the
        # OpenAlex topic.subfield → field mapping if no overlap was found.
        primary = ""
        cc = topic_concept_counts.get(label)
        if cc:
            primary = cc.most_common(1)[0][0]
        if not primary:
            # Try the field/domain string off the topic record
            field = (t.get("field") or {}).get("display_name", "")
            if field in concept_id_by_label:
                primary = field
        if not primary and concepts:
            # Last resort: anchor under the highest-score author concept
            primary = concepts[0]["label"]
        primary_id = concept_id_by_label.get(primary, concepts[0]["id"] if concepts else "")
        topics.append({
            "id":         "t-" + _slugify(label),
            "label":      label,
            "kind":       "topic",
            "count":      int(t.get("count") or 0),
            "concept_id": primary_id,
        })

    # ── Edges ─────────────────────────────────────────────────────────
    edges = []
    for c in concepts:
        edges.append({"a": "me", "b": c["id"],
                      "weight": round(c["score"], 3)})
    for t in topics:
        if t["concept_id"]:
            edges.append({"a": t["id"], "b": t["concept_id"],
                          "weight": t["count"]})

    # Center label — keep short enough to fit inside the disc. The full
    # name lives on every other page; here we just need a clear anchor.
    first = (full_name.split() or [""])[0]
    center_label = f"{first}'s research"
    return {
        "center":   {"id": "me", "label": center_label, "kind": "center"},
        "concepts": concepts,
        "topics":   topics,
        "edges":    edges,
    }


def _seed_positions(graph: dict) -> dict[str, tuple[float, float]]:
    """Initial positions in two concentric rings around the center. The JS
    layer uses these as the starting point for the simulation; if JS is
    disabled the static SVG draws nodes here directly."""
    import math
    positions: dict[str, tuple[float, float]] = {}
    cx, cy = W / 2, H / 2
    positions["me"] = (cx, cy)

    concepts = graph["concepts"]
    n_c = len(concepts) or 1
    r_c = 175
    for i, c in enumerate(concepts):
        # Distribute around the circle, starting at -90° (top)
        ang = -math.pi / 2 + 2 * math.pi * (i / n_c)
        positions[c["id"]] = (cx + r_c * math.cos(ang), cy + r_c * math.sin(ang))

    # Topics: clustered near their primary concept (angular offset)
    topics_per_concept: dict[str, list[dict]] = {}
    for t in graph["topics"]:
        topics_per_concept.setdefault(t["concept_id"], []).append(t)
    r_t_min, r_t_max = 270, 240  # alternate radius so close pairs don't collide
    for cid, ts in topics_per_concept.items():
        if cid not in positions:
            continue
        ccx, ccy = positions[cid]
        # Anchor angle from center → concept
        ang0 = math.atan2(ccy - cy, ccx - cx)
        # Spread topics evenly within a 70° arc around the concept's bearing
        if len(ts) == 1:
            angs = [ang0]
        else:
            spread = math.radians(70)
            angs = [ang0 - spread / 2 + spread * (i / (len(ts) - 1))
                    for i in range(len(ts))]
        for i, (t, ang) in enumerate(zip(ts, angs)):
            r_t = r_t_min if i % 2 == 0 else r_t_max
            positions[t["id"]] = (cx + r_t * math.cos(ang), cy + r_t * math.sin(ang))

    return positions


def _render_svg(graph: dict, positions: dict) -> str:
    """Pre-rendered SVG (works without JS for SEO + accessibility)."""
    lines: list[str] = []
    lines.append(
        f'<svg class="research-map-svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="research-map-title research-map-desc">'
    )
    lines.append('<title id="research-map-title">Research concept map</title>')
    lines.append(
        '<desc id="research-map-desc">A radial map of the research concepts '
        f'and topics linked to {escape(graph["center"]["label"])}. Top-level '
        'concepts surround the center; topics extend outward.</desc>'
    )

    # Edges first so nodes paint on top
    lines.append('<g class="rm-edges">')
    for e in graph["edges"]:
        if e["a"] not in positions or e["b"] not in positions:
            continue
        x1, y1 = positions[e["a"]]
        x2, y2 = positions[e["b"]]
        sw = 0.8 + min(2.4, float(e["weight"]) * 0.4)
        lines.append(
            f'<line class="rm-edge" data-a="{escape(e["a"])}" data-b="{escape(e["b"])}" '
            f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke-width="{sw:.2f}"/>'
        )
    lines.append('</g>')

    # Center node
    cx, cy = positions["me"]
    lines.append('<g class="rm-nodes">')
    lines.append(
        f'<g class="rm-node rm-node--center" data-id="me" '
        f'transform="translate({cx:.1f} {cy:.1f})">'
    )
    lines.append(f'<circle r="{CENTER_R}" class="rm-node-disc"/>')
    label = escape(graph["center"]["label"])
    lines.append(f'<text class="rm-node-label" text-anchor="middle" dy="4">{label}</text>')
    lines.append('</g>')

    # Concept nodes — scaled by score
    for c in graph["concepts"]:
        if c["id"] not in positions:
            continue
        x, y = positions[c["id"]]
        r = CONCEPT_R + min(8, float(c["score"]) * 8)
        lines.append(
            f'<g class="rm-node rm-node--concept" data-id="{escape(c["id"])}" '
            f'transform="translate({x:.1f} {y:.1f})">'
        )
        lines.append(f'<circle r="{r:.1f}" class="rm-node-disc"/>')
        lines.append(
            f'<text class="rm-node-label" text-anchor="middle" dy="4">{escape(c["label"])}</text>'
        )
        lines.append('</g>')

    # Topic nodes — scaled by count
    for t in graph["topics"]:
        if t["id"] not in positions:
            continue
        x, y = positions[t["id"]]
        r = TOPIC_R + min(10, int(t["count"]) * 1.4)
        # Shorten very long topic labels for readability in the static SVG
        label_t = t["label"]
        if len(label_t) > 26:
            label_t = label_t[:24] + "…"
        lines.append(
            f'<g class="rm-node rm-node--topic" data-id="{escape(t["id"])}" '
            f'transform="translate({x:.1f} {y:.1f})">'
        )
        lines.append(f'<circle r="{r:.1f}" class="rm-node-disc"/>')
        lines.append(
            f'<text class="rm-node-label" text-anchor="middle" dy="3">{escape(label_t)}</text>'
        )
        lines.append('</g>')
    lines.append('</g>')

    lines.append('</svg>')
    return "\n".join(lines)


def _render_section(graph: dict, positions: dict) -> str:
    """Full <section id="research-map"> block, including the JSON data
    payload the client-side JS reads."""
    svg = _render_svg(graph, positions)
    # JSON payload sans positions — the JS layer recomputes positions from
    # the simulation, so we keep the data file small.
    payload = {
        "center":   graph["center"],
        "concepts": graph["concepts"],
        "topics":   graph["topics"],
        "edges":    graph["edges"],
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    # Escape closing script tag in the data payload to be safe inside <script>
    payload_json = payload_json.replace("</", "<\\/")

    return (
        '\n    <section class="research-map reveal" aria-labelledby="research-map-h2">\n'
        '        <p class="sec-kicker">Research map</p>\n'
        '        <h2 id="research-map-h2" class="sec-title">'
        'Where my research <em>sits</em>.</h2>\n'
        '        <p class="research-map-lede">Top-level disciplines surround the centre. '
        'Topics radiate outward, clustered near the discipline they most overlap with. '
        'Sourced from OpenAlex. Concept scores and topic counts are computed across the full '
        'publication list and rebuilt every Monday.</p>\n'
        '        <div class="research-map-canvas">\n'
        f'        {svg}\n'
        '        </div>\n'
        f'        <script type="application/json" id="research-map-data">{payload_json}</script>\n'
        '    </section>\n'
    )


def patch_research_html(section_html: str) -> None:
    if not RESEARCH_HTML.exists():
        print(f"[FAIL] {RESEARCH_HTML} missing")
        sys.exit(1)
    text = RESEARCH_HTML.read_text(encoding="utf-8")
    orig = text

    block = f"\n    {MARK_BEGIN}{section_html}    {MARK_END}\n"

    if MARK_BEGIN in text and MARK_END in text:
        text = re.sub(
            re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
            (MARK_BEGIN + section_html + "    " + MARK_END),
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # First-time install: inject between sub-hero and research-intro
        anchor = '<section class="reveal research-intro">'
        if anchor not in text:
            print(f"[FAIL] anchor '{anchor}' not found in research.html")
            sys.exit(1)
        text = text.replace(anchor, block + "    " + anchor, 1)

    if text != orig:
        RESEARCH_HTML.write_text(text, encoding="utf-8")
        print(f"[OK] research.html: research-map section updated")
    else:
        print(f"[OK] research.html: research-map unchanged")


def main() -> int:
    if not DATA_OPENALX.exists():
        print(f"[WARN] {DATA_OPENALX} missing — skipping research-map build")
        return 0
    with DATA_OPENALX.open(encoding="utf-8") as f:
        data = json.load(f)
    graph = _build_graph(data)
    if not graph["concepts"]:
        print("[WARN] no concepts in OpenAlex data — skipping research-map")
        return 0
    positions = _seed_positions(graph)
    section = _render_section(graph, positions)
    patch_research_html(section)
    print(
        f"[research-map] {len(graph['concepts'])} concepts, "
        f"{len(graph['topics'])} topics, {len(graph['edges'])} edges baked."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
