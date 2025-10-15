// scopus.v2.js — renders Template-2 cards from /data/scopus/scopus.json + metrics
const DATA_PATH = "data/scopus/scopus.json"; // JSON created by tools/scopus_fetcher.py

/* ---------- helpers ---------- */
const fmtDate = (iso="")=>{
  if(!iso) return "";
  const [y,m="01"] = iso.split("-");
  const dt = new Date(Number(y), Number(m)-1, 1);
  return Number.isNaN(dt) ? (y||"") : dt.toLocaleDateString(undefined,{month:"short", year:"numeric"});
};

const bestLink  = it => it.doi_url || it.scopus_url || "#";
const classify  = it => {
  const st=(it.subtype||"").toLowerCase();
  const desc=(it.type||it.subtypeDescription||"").toLowerCase();
  const isConf = st==="cp" || desc.includes("conference");
  const isArt  = st==="ar" || desc.includes("article") || desc.includes("review") || desc.includes("editorial");
  return isConf ? "conference" : (isArt ? "article" : "other");
};
const placeholder = kind => kind==="conference" ? "images/conference-placeholder.png" : "images/publication-placeholder.png";

/* h-index from a list of citation counts */
const hIndex = (citations=[])=>{
  const s=[...citations].sort((a,b)=>b-a);
  let h=0;
  for(let i=0;i<s.length;i++){
    if(s[i] >= i+1) h=i+1; else break;
  }
  return h;
};

/* ---------- card ---------- */
function card(it, kind){
  const label = kind==="conference" ? "Conference" : "Journal";
  const date  = fmtDate(it.cover_date || `${it.year||""}-${it.month||""}-01`);
  const venue = it.venue || (kind==="conference" ? "Conference" : "Journal");
  const title = it.title || "Untitled";

  // authors: show full list, bold your name if present
  let authorsText = "";
  if (Array.isArray(it.authors) && it.authors.length){
    const mine = /abou.*hajal/i;
    const parts = it.authors.map(a => mine.test(a) ? `<strong>${a}</strong>` : a);
    authorsText = parts.join(", ");
  } else if (it.first_author){
    authorsText = `${it.first_author} et al.`;
  }

  const href  = bestLink(it), img=placeholder(kind);

  const el = document.createElement("div");
  el.className = "publication-item";
  el.innerHTML = `
    <div class="publication-info">
      <div class="publication-meta">
        <span class="publication-label">${label}</span>
        <span class="publication-date">${date}</span>
        ${venue ? `<a class="publication-category" href="${href}" target="_blank" rel="noopener">${venue}</a>` : ``}
      </div>
      <h3 class="publication-title"><a href="${href}" target="_blank" rel="noopener">${title}</a></h3>
      ${authorsText ? `<p class="publication-description">${authorsText}</p>` : ``}
      <div class="pub-actions">
        <a class="pub-btn" href="${href}" target="_blank" rel="noopener">Read</a>
        ${typeof it.cited_by==="number" ? `<span class="pub-btn">Citations: ${it.cited_by}</span>` : ``}
      </div>
    </div>`
  return el;
}

/* ---------- metrics ---------- */
function renderMetrics(list){
  const total = list.length;
  const cites = list.reduce((s,x)=> s + (Number(x.cited_by)||0), 0);
  const h     = hIndex(list.map(x=> Number(x.cited_by)||0));

  const $t = document.getElementById("m-total");
  const $c = document.getElementById("m-cites");
  const $h = document.getElementById("m-h");
  if($t) $t.textContent = String(total);
  if($c) $c.textContent = String(cites);
  if($h) $h.textContent = String(h);
}

/* ---------- boot ---------- */
async function boot(){
  const app=document.getElementById("pub-app"); if(!app) return;
  const AUTHOR=app.dataset.authorId||"";
  const $a=document.getElementById("list-articles");

  try{
    const r=await fetch(DATA_PATH,{headers:{Accept:"application/json"}});
    if(!r.ok) throw new Error(`HTTP ${r.status}`);
    let data=await r.json();

    // filter to your author
    if(AUTHOR) data=data.filter(x=> (x.author_id||"")===AUTHOR);

    // sort newest first (year, month, title)
    data.sort((a,b)=>{
      const ay=+a.year||0, by=+b.year||0; if(ay!==by) return by-ay;
      const am=+a.month||0, bm=+b.month||0; if(am!==bm) return bm-am;
      return (a.title||"").localeCompare(b.title||"");
    });

    // metrics for ALL your items (articles + reviews + editorials + conf)
    renderMetrics(data);

    // render just journal-like material in this template page
    let countArticles=0;
    for(const it of data){
      const kind=classify(it);
      if(kind==="article"){ $a.appendChild(card(it,"article")); countArticles++; }
    }
    if(!countArticles) $a.innerHTML=`<p style="color:#666">No journal articles found.</p>`;
  }catch(e){
    console.error(e);
    if ($a) $a.innerHTML=`<p style="color:#666">Could not load publications.</p>`;
  }
}

boot();
