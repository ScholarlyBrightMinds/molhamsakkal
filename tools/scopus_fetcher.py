# tools/scopus_fetcher.py
from __future__ import annotations
import argparse, csv, json, os, time, logging, requests

API_KEYS=[k.strip() for k in os.getenv("SCOPUS_API_KEYS","").split(",") if k.strip()]
if not API_KEYS:
    raise SystemExit("Set SCOPUS_API_KEYS=key1,key2,... (comma-separated) before running.")

SEARCH="https://api.elsevier.com/content/search/scopus"
ABSTRACT="https://api.elsevier.com/content/abstract/eid/{}"
FIELDS="dc:title,eid,prism:doi,citedby-count,prism:coverDate,subtype,subtypeDescription,prism:publicationName,prism:volume,prism:issueIdentifier,prism:pageRange,dc:creator"
PAGE=25; TIMEOUT=20
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("scopus")

def ensure(p): os.makedirs(p, exist_ok=True)
def scopus_link(eid): return f"https://www.scopus.com/record/display.uri?eid={eid}&origin=recordpage"

def parts(date):
    y=m=d=None
    if date:
        sp=date.split("-")
        y=sp[0] if len(sp)>0 else None
        m=(sp[1].zfill(2) if len(sp)>1 and sp[1] else None)
        d=(sp[2].zfill(2) if len(sp)>2 and sp[2] else None)
    return y,m,d

def req(url, headers, params):
    r=requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def iter_search(keys, query):
    i=start=0; total=None
    while True:
        headers={"Accept":"application/json","X-ELS-APIKey":keys[i%len(keys)]}
        params={"query":query,"field":FIELDS,"count":PAGE,"start":start}
        try:
            data=req(SEARCH, headers, params)
        except Exception:
            i+=1; time.sleep(0.4); continue
        root=data.get("search-results",{}); entries=root.get("entry",[]) or []
        if total is None:
            tr=root.get("opensearch:totalResults")
            total=int(tr) if tr and str(tr).isdigit() else None
        for e in entries: yield e
        start+=PAGE
        if total is None and len(entries)<PAGE: break
        if total is not None and (start>=total or not entries): break
        time.sleep(0.25)

def fetch_authors(keys, eid):
    headers={"Accept":"application/json","X-ELS-APIKey":keys[0]}
    for _ in range(4):
        try:
            j=req(ABSTRACT.format(eid), headers, {"view":"FULL"})
            authors=j.get("abstracts-retrieval-response",{}).get("authors",{}).get("author",[])
            if isinstance(authors, dict): authors=[authors]
            names=[]
            for a in authors:
                nm=a.get("ce:indexed-name") or a.get("preferred-name",{}).get("ce:indexed-name") or a.get("authname")
                if nm: names.append(nm)
            return names
        except Exception:
            time.sleep(0.5)
    return []

def normalize(it, authors):
    y,m,d=parts(it.get("prism:coverDate") or "")
    doi=it.get("prism:doi")
    return {
        "title": it.get("dc:title") or "",
        "eid": it.get("eid") or "",
        "scopus_url": scopus_link(it.get("eid","")),
        "doi": doi,
        "doi_url": f"https://doi.org/{doi}" if doi else None,
        "cited_by": int(it.get("citedby-count",0) or 0),
        "cover_date": it.get("prism:coverDate") or "",
        "year": y, "month": m, "day": d,
        "venue": it.get("prism:publicationName"),
        "type": it.get("subtypeDescription"),
        "subtype": it.get("subtype"),  # 'ar' = article, 'cp' = conference paper, etc.
        "volume": it.get("prism:volume"),
        "issue": it.get("prism:issueIdentifier"),
        "pages": it.get("prism:pageRange"),
        "first_author": it.get("dc:creator"),
        "authors": authors
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--authors-file", default="data/authors.csv")
    ap.add_argument("--out", default="data/scopus")
    ap.add_argument("--combined", default="data/scopus/scopus.json")
    ap.add_argument("--details", action="store_true")
    ap.add_argument("--types", default="Article,Review,Editorial,Conference Paper")
    args=ap.parse_args()

    ensure(args.out)

    authors=[]
    with open(args.authors_file, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            aid=str(r.get("author_id","")).strip(); nm=str(r.get("name","")).strip()
            if aid and nm: authors.append((aid,nm))
    if not authors: raise SystemExit("authors.csv has no rows.")

    include=[t.strip().lower() for t in args.types.split(",") if t.strip()]
    combined=[]
    for i,(aid,nm) in enumerate(authors,1):
        log.info("Author %d/%d %s (%s)", i, len(authors), nm, aid)
        q=f"AU-ID({aid})"
        rows=[]
        for it in iter_search(API_KEYS, q):
            desc=(it.get("subtypeDescription") or it.get("subtype") or "").lower()
            keep = any(t in desc for t in include) or it.get("subtype","").lower()=="cp"
            if not keep: continue
            a = fetch_authors(API_KEYS, it.get("eid","")) if (args.details and it.get("eid")) else []
            row=normalize(it, a)
            row["author_id"]=aid; row["author_name"]=nm
            rows.append(row)

        rows.sort(key=lambda r: (
            int(r["year"]) if (r["year"] and str(r["year"]).isdigit()) else -1,
            r.get("month") or "",
            r.get("title") or ""
        ), reverse=True)

        # per-author CSV
        csvp=os.path.join(args.out, f"{nm.replace(' ','_')}_articles.csv")
        with open(csvp,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["title","scopus_url","doi_url","cited_by","cover_date","venue","volume","issue","pages"])
            w.writeheader()
            for r in rows: w.writerow({k:r.get(k) for k in w.fieldnames})
        log.info("Saved %d item(s) → %s", len(rows), csvp)

        combined.extend(rows); time.sleep(0.1)

    with open(args.combined,"w",encoding="utf-8") as f:
        json.dump(combined,f,ensure_ascii=False,indent=2)
    log.info("Combined JSON: %s (total %d)", args.combined, len(combined))

if __name__=="__main__": main()
