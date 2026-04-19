// File: serpapi.v1.js
// Renders publications from data/serpapi/serpapi.json and data/serpapi/metrics.json

const DATA_PATH    = "data/serpapi/serpapi.json";
const METRICS_PATH = "data/serpapi/metrics.json";

/* ── utils ───────────────────────────────────────────────────── */

const fmtDate = (yearStr = "") => {
  if (!yearStr) return "";
  const year = parseInt(yearStr);
  if (isNaN(year)) return "";
  return new Date(year, 0, 1).toLocaleDateString(undefined, { month: "short", year: "numeric" });
};

const bestLink = it => it.link || "#";

const classify = it => {
  const venue = (it.venue || "").toLowerCase();
  if (venue.includes("conference") || venue.includes("proc.") || venue.includes("proceedings"))
    return "conference";
  if (
    venue.includes("journal") || venue.includes("review") ||
    venue.includes("pharmaceutical") || venue.includes("chemical") ||
    venue.includes("economics") || venue.includes("letters") ||
    venue.includes("bulletin") || venue.includes("annals")
  )
    return "article";
  return "article"; // default: treat as article rather than hiding it
};

const hIndex = (arr = []) => {
  const s = [...arr].map(n => Number(n) || 0).sort((a, b) => b - a);
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    if (s[i] >= i + 1) h = i + 1; else break;
  }
  return h;
};

const setText = (id, val) => {
  const el = document.getElementById(id);
  if (el) el.textContent = String(val);
};

/* ── metrics ─────────────────────────────────────────────────── */

function renderOfficialMetrics(m) {
  // KEY FIX: don't trust the file if citations AND h-index are both zero —
  // that means the fetcher's API call failed and wrote zeros to disk.
  // Fall through to computed metrics instead.
  if (!m || typeof m !== "object") return false;
  const total = Number(m.total_documents);
  const cites = Number(m.total_citations);
  const h     = Number(m.h_index);
  if (!cites && !h) return false;   // zeros → don't trust, compute instead
  setText("m-total", total);
  setText("m-cites", cites);
  setText("m-h",     h);
  return true;
}

function renderComputedMetrics(list) {
  const total = list.length;
  const cites = list.reduce((s, x) => s + (Number(x.cited_by) || 0), 0);
  const h     = hIndex(list.map(x => x.cited_by));
  setText("m-total", total);
  setText("m-cites", cites);
  setText("m-h",     h);
}

/* ── card ────────────────────────────────────────────────────── */

function card(it, kind) {
  const title  = it.title || "Untitled";
  const venue  = it.venue || "Journal";
  const date   = fmtDate(it.year);
  const MINE   = /abou.*hajal|hajal.*abou|abdallah/i;
  const authorsHtml = it.authors
    ? it.authors.split(", ").map(a => MINE.test(a) ? `<strong>${a}</strong>` : a).join(", ")
    : "";
  const href   = bestLink(it);
  const label  = kind === "conference" ? "Conference" : "Journal";

  const el = document.createElement("div");
  el.className = "publication-item";
  el.innerHTML = `
    <div class="publication-info">
      <div class="publication-meta">
        <span class="publication-label">${label}</span>
        <span class="publication-date">${date}</span>
        ${venue ? `<a class="publication-category" href="${href}" target="_blank" rel="noopener">${venue}</a>` : ""}
      </div>
      <h3 class="publication-title">
        <a href="${href}" target="_blank" rel="noopener">${title}</a>
      </h3>
      ${authorsHtml ? `<p class="publication-description">${authorsHtml}</p>` : ""}
      <div class="pub-actions">
        <a class="pub-btn" href="${href}" target="_blank" rel="noopener">Read</a>
        ${typeof it.cited_by === "number" && it.cited_by > 0
          ? `<span class="pub-btn">Citations: ${it.cited_by}</span>`
          : ""}
      </div>
    </div>`;
  return el;
}

/* ── boot ────────────────────────────────────────────────────── */

(async function boot() {
  const app  = document.getElementById("pub-app");
  if (!app) return;
  const $list = document.getElementById("list-articles");
  if (!$list) return;

  // Show a loading placeholder immediately
  $list.innerHTML = `<p style="color:#888;font-style:italic;padding:20px;text-align:center">Loading publications…</p>`;

  let pubs     = [];
  let official = null;

  // Daily cache-bust — avoids stale data without hammering the CDN every millisecond
  const bust = Math.floor(Date.now() / 86_400_000);

  try {
    const r = await fetch(`${DATA_PATH}?v=${bust}`, { cache: "no-store" });
    if (r.ok) {
      pubs = await r.json();
      console.log(`serpapi.v1: loaded ${pubs.length} publications`);
    } else {
      console.error(`serpapi.json: HTTP ${r.status}`);
    }
  } catch (e) {
    console.error("serpapi.json fetch error:", e);
  }

  // Sort: newest first, then alphabetical within the same year
  pubs.sort((a, b) => {
    const ay = +a.year || 0, by = +b.year || 0;
    if (ay !== by) return by - ay;
    return (a.title || "").localeCompare(b.title || "");
  });

  // Fetch official metrics and apply — fall back to computed if zeros/missing
  try {
    const m = await fetch(`${METRICS_PATH}?v=${bust}`, { cache: "no-store" });
    if (m.ok) official = await m.json();
  } catch (e) {
    console.warn("metrics.json fetch error:", e);
  }

  if (!renderOfficialMetrics(official)) {
    renderComputedMetrics(pubs);
  }

  // Render all publications
  $list.innerHTML = "";
  if (!pubs.length) {
    $list.innerHTML = `<p style="color:#666">No publications found.</p>`;
    return;
  }

  for (const it of pubs) {
    $list.appendChild(card(it, classify(it)));
  }
})();
