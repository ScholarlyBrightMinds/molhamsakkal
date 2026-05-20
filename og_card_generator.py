#!/usr/bin/env python3
"""
og_card_generator.py — Per-paper OG/Twitter share cards (1200x630).

Generates two kinds of PNG into ``images/og/``:

1. **Per-paper cards** (``{doi-slug}.png``): one card per resolved DOI in
   ``data/serpapi/dois.json``, showing title / authors / year / venue / cites.
   These are intended for future per-paper detail pages or for sharing the
   DOI link with a richer preview (the Twitter/X validator and LinkedIn
   scraper both honour ``og:image`` overrides via per-page meta).

2. **Publications summary card** (``publications.png``): a single 1200x630
   showing headline metrics (publications / citations / h-index) and the
   top three most-cited papers. Wired into the ``og:image`` on
   ``publications.html`` so that share previews of the listing page have
   real content instead of the static profile photo.

The script is idempotent: each PNG is written only when its content hash
differs from the on-disk file, so re-running in CI doesn't produce noisy
diffs.

Run locally:  python og_card_generator.py
In CI:        added as a workflow step after build_html.py.

Font resolution: try Linux paths first (CI runner) → Windows paths (local
dev) → Pillow default bitmap. The site brand uses Segoe/Inter system stack
so Liberation Sans Bold on Linux + Arial Bold on Windows look close enough.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[FAIL] Pillow not installed — pip install Pillow", file=sys.stderr)
    sys.exit(1)

REPO_ROOT     = Path(__file__).resolve().parent
DATA_PUBS     = REPO_ROOT / "data" / "serpapi" / "serpapi.json"
DATA_METR     = REPO_ROOT / "data" / "serpapi" / "metrics.json"
DATA_DOIS     = REPO_ROOT / "data" / "serpapi" / "dois.json"
DATA_OPENALX  = REPO_ROOT / "data" / "openalex" / "openalex.json"
OUT_DIR       = REPO_ROOT / "images" / "og"

# 1200x630 is the Facebook / LinkedIn / Twitter recommended OG card size
CARD_W, CARD_H = 1200, 630

# Brand palette — matches styles.css :root
BG          = (13, 20, 17)        # var(--bg)
BG_PANEL    = (22, 32, 28)        # subtle inset
ACCENT      = (255, 184, 77)      # var(--accent) — warm orange
ACCENT_SOFT = (255, 184, 77, 40)  # for hairlines and tints
TEXT        = (228, 235, 230)     # var(--text)
TEXT_SOFT   = (160, 175, 168)     # var(--text-soft)
INK_TEAL    = (120, 200, 180)     # secondary accent (sparkline color)


# ─────────────────────────────────────────────────────────────────────────
# Font resolution
# ─────────────────────────────────────────────────────────────────────────
def _font_paths() -> dict[str, list[str]]:
    """Candidate font paths per role (bold / regular / mono). First hit wins."""
    return {
        "bold": [
            # Linux (GitHub Actions ubuntu-latest)
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
            # Windows
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ],
        "regular": [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ],
        "mono": [
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationMono-Bold.ttf",
            r"C:\Windows\Fonts\consolab.ttf",
            "/System/Library/Fonts/Monaco.ttf",
        ],
    }


def _load_font(role: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _font_paths().get(role, []):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    # Last resort: Pillow's tiny default bitmap. Cards will look bad but won't crash.
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────
# Text layout helpers
# ─────────────────────────────────────────────────────────────────────────
def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Return (width, height) of `text` in `font`, robust across PIL versions."""
    if hasattr(draw, "textbbox"):
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return r - l, b - t
    return draw.textsize(text, font=font)  # legacy


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int, max_lines: int) -> list[str]:
    """Greedy word-wrap with ellipsis when over budget."""
    words = (text or "").split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        if _measure(draw, candidate, font)[0] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    # If we hit the line cap, ellipsise the last visible line
    if len(lines) == max_lines and len(words) > sum(len(l.split()) for l in lines):
        last = lines[-1]
        while _measure(draw, last + "…", font)[0] > max_w and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last + "…"
    return lines


# ─────────────────────────────────────────────────────────────────────────
# Background painter — shared between summary + per-paper cards
# ─────────────────────────────────────────────────────────────────────────
def _paint_background(img: Image.Image) -> None:
    """Soft top-left accent glow + bottom accent hairline."""
    draw = ImageDraw.Draw(img, "RGBA")
    # Radial-ish glow approximated by stacked translucent ellipses
    for i, alpha in enumerate([14, 10, 7, 4]):
        r = 380 + i * 80
        draw.ellipse(
            (-r // 2, -r // 2, r, r),
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha),
        )
    # Bottom hairline
    draw.rectangle((0, CARD_H - 6, CARD_W, CARD_H - 5), fill=ACCENT)
    # Subtle dotted grid in the lower-right (hex-pattern echo from blog covers)
    for x in range(800, CARD_W, 22):
        for y in range(CARD_H - 220, CARD_H - 20, 22):
            draw.ellipse((x, y, x + 2, y + 2), fill=(*INK_TEAL, 38))


# ─────────────────────────────────────────────────────────────────────────
# Per-paper card
# ─────────────────────────────────────────────────────────────────────────
def render_paper_card(
    title: str,
    authors: str,
    year: str | int,
    venue: str,
    cites: int,
    doi: str | None,
    full_name: str = "Researcher",
) -> Image.Image:
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    _paint_background(img)
    draw = ImageDraw.Draw(img, "RGBA")

    f_kicker  = _load_font("regular", 24)
    f_title   = _load_font("bold",    56)
    f_title_s = _load_font("bold",    48)
    f_meta    = _load_font("regular", 26)
    f_stat    = _load_font("mono",    32)
    f_brand   = _load_font("bold",    22)

    pad = 72
    inner_w = CARD_W - 2 * pad

    # Kicker — small uppercase line above the title
    draw.text((pad, 78), "PUBLICATION", font=f_kicker, fill=ACCENT)
    # Accent bar under the kicker
    draw.rectangle((pad, 116, pad + 64, 119), fill=ACCENT)

    # Title — up to 4 lines at 56px, else step down to 48px and allow 5 lines
    title_lines = _wrap(draw, title, f_title, inner_w, max_lines=4)
    title_font  = f_title
    if len(title_lines) >= 4:
        # Try smaller size for more room
        alt = _wrap(draw, title, f_title_s, inner_w, max_lines=5)
        if len(alt) >= len(title_lines):
            title_lines, title_font = alt, f_title_s
    y = 150
    for ln in title_lines:
        draw.text((pad, y), ln, font=title_font, fill=TEXT)
        _, lh = _measure(draw, ln, title_font)
        y += int(lh * 1.18)

    # Meta row: Authors · Year · Venue (separate lines, soft text)
    meta_y = CARD_H - 200
    if authors:
        # Truncate author list to keep it on one line
        au_lines = _wrap(draw, authors, f_meta, inner_w, max_lines=1)
        draw.text((pad, meta_y), au_lines[0], font=f_meta, fill=TEXT_SOFT)
        meta_y += 38
    venue_year = " · ".join(x for x in [str(year), venue] if x)
    if venue_year:
        v_lines = _wrap(draw, venue_year, f_meta, inner_w, max_lines=1)
        draw.text((pad, meta_y), v_lines[0], font=f_meta, fill=TEXT_SOFT)

    # Citations stat block — bottom right
    if cites:
        stat_text = str(cites)
        stat_label = "citations" if cites != 1 else "citation"
        sw, sh = _measure(draw, stat_text, f_stat)
        x_stat = CARD_W - pad - sw
        y_stat = CARD_H - 130
        draw.text((x_stat, y_stat), stat_text, font=f_stat, fill=ACCENT)
        lw, _ = _measure(draw, stat_label, f_kicker)
        draw.text(
            (CARD_W - pad - lw, y_stat + 42),
            stat_label,
            font=f_kicker,
            fill=TEXT_SOFT,
        )

    # Brand strip — bottom-left
    draw.text(
        (pad, CARD_H - 56),
        f"{full_name} · Scholarly Bright Minds",
        font=f_brand,
        fill=ACCENT,
    )
    if doi:
        doi_short = doi if len(doi) <= 60 else doi[:57] + "..."
        draw.text(
            (pad, CARD_H - 88),
            f"doi.org/{doi_short}",
            font=f_kicker,
            fill=TEXT_SOFT,
        )

    return img


# ─────────────────────────────────────────────────────────────────────────
# Summary card (publications.html OG)
# ─────────────────────────────────────────────────────────────────────────
def render_summary_card(
    full_name: str,
    total: int,
    cites: int,
    hidx: int | str,
    top_papers: list[dict],
) -> Image.Image:
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    _paint_background(img)
    draw = ImageDraw.Draw(img, "RGBA")

    f_kicker = _load_font("regular", 24)
    f_h1     = _load_font("bold",    72)
    f_h2     = _load_font("bold",    36)
    f_stat_n = _load_font("mono",    64)
    f_stat_l = _load_font("regular", 22)
    f_paper  = _load_font("regular", 22)
    f_brand  = _load_font("bold",    22)

    pad = 72

    # Header
    draw.text((pad, 64), "PUBLICATIONS", font=f_kicker, fill=ACCENT)
    draw.rectangle((pad, 102, pad + 64, 105), fill=ACCENT)
    draw.text((pad, 124), full_name, font=f_h1, fill=TEXT)

    # Stats row — three tiles
    stats = [
        (str(total), "publications"),
        (str(cites), "citations"),
        (str(hidx),  "h-index"),
    ]
    tile_w = (CARD_W - 2 * pad - 2 * 28) // 3
    tile_y = 240
    tile_h = 130
    for i, (num, lab) in enumerate(stats):
        x = pad + i * (tile_w + 28)
        # subtle panel
        draw.rounded_rectangle(
            (x, tile_y, x + tile_w, tile_y + tile_h),
            radius=12,
            fill=BG_PANEL,
            outline=ACCENT_SOFT,
            width=1,
        )
        nw, nh = _measure(draw, num, f_stat_n)
        draw.text((x + (tile_w - nw) // 2, tile_y + 18), num, font=f_stat_n, fill=ACCENT)
        lw, _ = _measure(draw, lab, f_stat_l)
        draw.text(
            (x + (tile_w - lw) // 2, tile_y + 88),
            lab,
            font=f_stat_l,
            fill=TEXT_SOFT,
        )

    # Recent / top papers list
    draw.text((pad, 400), "Highlights", font=f_h2, fill=TEXT)
    draw.rectangle((pad, 442, pad + 48, 445), fill=ACCENT)
    py = 458
    for paper in top_papers[:3]:
        bullet_y = py + 12
        draw.ellipse((pad, bullet_y, pad + 8, bullet_y + 8), fill=ACCENT)
        title_lines = _wrap(
            draw,
            paper["title"],
            f_paper,
            CARD_W - 2 * pad - 22,
            max_lines=1,
        )
        if title_lines:
            draw.text((pad + 22, py), title_lines[0], font=f_paper, fill=TEXT)
        py += 34

    # Brand strip — set below the bullets with breathing room
    draw.text(
        (pad, CARD_H - 44),
        f"scholarlybrightminds.github.io/{REPO_ROOT.name}",
        font=f_brand,
        fill=ACCENT,
    )

    return img


# ─────────────────────────────────────────────────────────────────────────
# DOI helpers
# ─────────────────────────────────────────────────────────────────────────
def _slugify_doi(doi: str) -> str:
    """Make a filesystem-safe slug from a DOI. e.g. ``10.1080/abc.123`` ->
    ``10-1080_abc-123``. Hash long DOIs to keep filenames sane."""
    safe = re.sub(r"[^a-z0-9]+", "-", doi.lower()).strip("-")
    if len(safe) > 80:
        safe = safe[:60] + "-" + hashlib.sha1(
            doi.encode("utf-8"), usedforsecurity=False
        ).hexdigest()[:8]
    return safe


def _pub_doi_key(pub: dict) -> str:
    """Mirror of enrich_dois.pub_key() / build_html._pub_doi_key()."""
    link = (pub.get("link") or "").strip()
    if link:
        return hashlib.sha1(link.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
    fallback = (pub.get("title") or "") + "|" + str(pub.get("year") or "")
    return hashlib.sha1(fallback.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────
# Idempotent write
# ─────────────────────────────────────────────────────────────────────────
def _save_if_changed(img: Image.Image, dest: Path) -> bool:
    """Write `img` to `dest` only if the file would actually change. Returns
    True if a write happened."""
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    new_bytes = buf.getvalue()
    if dest.exists() and dest.read_bytes() == new_bytes:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(new_bytes)
    return True


# ─────────────────────────────────────────────────────────────────────────
# Identity (mirrors build_html.load_identity for the full_name field)
# ─────────────────────────────────────────────────────────────────────────
def _load_full_name() -> str:
    cfg = REPO_ROOT / "theme.config.js"
    if cfg.exists():
        m = re.search(r'fullName\s*:\s*"([^"]*)"', cfg.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return REPO_ROOT.name


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    full_name = _load_full_name()

    pubs_raw: list[dict] = []
    if DATA_PUBS.exists():
        with DATA_PUBS.open(encoding="utf-8") as f:
            pubs_raw = json.load(f)
    if not pubs_raw:
        print("[og-cards] no publications found, nothing to do")
        return 0

    dois: dict = {}
    if DATA_DOIS.exists():
        with DATA_DOIS.open(encoding="utf-8") as f:
            dois = json.load(f)

    metrics: dict = {}
    if DATA_METR.exists():
        with DATA_METR.open(encoding="utf-8") as f:
            metrics = json.load(f)

    # Per-paper cards
    written = 0
    skipped = 0
    for pub in pubs_raw:
        doi_info = dois.get(_pub_doi_key(pub)) or {}
        doi = (doi_info.get("doi") or "").strip()
        if not doi:
            skipped += 1
            continue
        img = render_paper_card(
            title=pub.get("title", "Untitled"),
            authors=pub.get("authors", ""),
            year=pub.get("year", ""),
            venue=pub.get("venue", "") or pub.get("publication", ""),
            cites=int(pub.get("cited_by") or 0),
            doi=doi,
            full_name=full_name,
        )
        dest = OUT_DIR / f"{_slugify_doi(doi)}.png"
        if _save_if_changed(img, dest):
            written += 1
    print(f"[og-cards] per-paper: {written} written, {skipped} skipped (no DOI)")

    # Summary card
    top_papers = sorted(
        pubs_raw,
        key=lambda p: int(p.get("cited_by") or 0),
        reverse=True,
    )[:3]
    total = metrics.get("total_documents") or len(pubs_raw)
    cites = (metrics.get("total_citations")
             or sum(int(p.get("cited_by") or 0) for p in pubs_raw))
    hidx  = metrics.get("h_index") or "—"
    summary = render_summary_card(full_name, total, cites, hidx, top_papers)
    summary_dest = OUT_DIR / "publications.png"
    if _save_if_changed(summary, summary_dest):
        print(f"[og-cards] summary: wrote {summary_dest.relative_to(REPO_ROOT)}")
    else:
        print("[og-cards] summary: no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
