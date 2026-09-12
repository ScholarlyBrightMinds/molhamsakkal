#!/usr/bin/env python3
"""
citations_fetcher.py · publications and citation counts from open indexes.

Replaces serpapi_fetcher.py. No SerpApi, no Google Scholar, no paid key.

Sources, in order of trust:
  1. OpenAlex   works by author id, plus per-DOI cited_by_count   (no key)
  2. Crossref   works by ORCID, plus per-DOI is-referenced-by-count (no key)
  3. ORCID      the local record already fetched by orcid_fetcher.py
  4. Semantic Scholar  per-DOI citationCount, only if S2_API_KEY is set

A paper's citation count is the HIGHEST count any source reports for it.
Indexes disagree because they crawl different corpora; taking the maximum
is the count we can actually point at a source for, per paper.

Why the numbers are lower than Google Scholar: Scholar also counts theses,
preprints, lecture slides and books that no open index indexes. The gap is
real and it is not a bug. Every number here traces to a DOI you can open.

Writes the same three files serpapi_fetcher.py did, with the same schema,
so build_html.py, serpapi.v1.js, og_card_generator.py and the hub's
aggregate_metrics.py keep working untouched:

  data/serpapi/serpapi.json   list of {title, authors, venue, year,
                              cited_by, link, author_id}
  data/serpapi/metrics.json   {total_documents, total_citations, h_index,
                              author_id, source, last_updated, sources}
  data/serpapi/dois.json      pub_key -> {doi, confidence, matched_title,
                              matched_year, matched_at}

Two safeguards, both deliberate:

  * A paper is never dropped because an API failed. The previous DOI list
    is unioned in, and if every source fails for one paper this run, its
    last known count is carried forward rather than written as zero.
  * If the run resolves fewer than 80% of the papers it knew about last
    week, it writes nothing and exits non-zero. A network outage must not
    be able to publish a collapsed citation count.

Genuine downward corrections still land: if a source answers with a lower
number (a retraction, a merged duplicate), that number is used.

Config, all via env:
  OPENALEX_AUTHOR_IDS  required, comma separated. More than one when a
                       person's works are split across OpenAlex records.
  ORCID_ID             optional, enables the Crossref-by-ORCID sweep
  CROSSREF_MAILTO      optional, polite pool
  S2_API_KEY           optional, enables Semantic Scholar
  SCHOLAR_AUTHOR_ID    optional, preserved in the author_id field only
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

OUTPUT_DIR = "data/serpapi"
ORCID_LOCAL = "data/orcid/orcid.json"

OPENALEX_IDS = [s.strip() for s in os.getenv("OPENALEX_AUTHOR_IDS", "").split(",") if s.strip()]
ORCID_ID = os.getenv("ORCID_ID", "").strip()
MAILTO = os.getenv("CROSSREF_MAILTO", "editorial@scifiniti.com").strip()
S2_KEY = os.getenv("S2_API_KEY", "").strip()
AUTHOR_ID_FIELD = os.getenv("SCHOLAR_AUTHOR_ID", "").strip() or (OPENALEX_IDS[0] if OPENALEX_IDS else "")

UA = f"ScholarlyBrightMinds-citations/1.0 (mailto:{MAILTO})"
MIN_RETAINED_FRACTION = 0.8


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_doi(raw) -> str | None:
    if not raw:
        return None
    d = str(raw).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = d.rstrip(" .,;")
    return d if d.startswith("10.") else None


def pub_key(pub: dict) -> str:
    """Mirror of enrich_dois.pub_key() and build_html._pub_doi_key()."""
    link = (pub.get("link") or "").strip()
    if link:
        return hashlib.sha1(link.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
    fallback = (pub.get("title") or "") + "|" + str(pub.get("year") or "")
    return hashlib.sha1(fallback.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


def http_json(url: str, data: bytes | None = None, headers: dict | None = None,
              retries: int = 3, backoff: float = 2.0):
    h = {"User-Agent": UA}
    if data is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            # 404 means "not in this index", which is an answer, not a failure
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            return None
    return None


# ── 1 · collect the paper list ───────────────────────────────────────────

def dois_from_openalex_author() -> tuple[set[str], dict]:
    """Every DOI OpenAlex attributes to these author records, with metadata."""
    found, meta = set(), {}
    if not OPENALEX_IDS:
        return found, meta
    filt = "|".join(OPENALEX_IDS)
    cursor = "*"
    while cursor:
        url = ("https://api.openalex.org/works"
               f"?filter=author.id:{urllib.parse.quote(filt, safe='|')}"
               "&per-page=200"
               f"&cursor={urllib.parse.quote(cursor)}"
               f"&mailto={urllib.parse.quote(MAILTO)}")
        page = http_json(url)
        if not page:
            break
        for w in page.get("results", []):
            d = norm_doi(w.get("doi"))
            if d:
                found.add(d)
                meta[d] = w
        cursor = (page.get("meta") or {}).get("next_cursor")
        time.sleep(0.2)
    print(f"  OpenAlex author sweep : {len(found)} DOIs")
    return found, meta


def dois_from_crossref_orcid() -> set[str]:
    """Crossref indexes ORCID on authorships, which catches papers OpenAlex
    has filed under a different author record."""
    found = set()
    if not ORCID_ID:
        return found
    offset, rows = 0, 200
    while True:
        url = ("https://api.crossref.org/works"
               f"?filter=orcid:{urllib.parse.quote(ORCID_ID)}"
               f"&rows={rows}&offset={offset}&select=DOI"
               f"&mailto={urllib.parse.quote(MAILTO)}")
        page = http_json(url)
        items = ((page or {}).get("message") or {}).get("items") or []
        for it in items:
            d = norm_doi(it.get("DOI"))
            if d:
                found.add(d)
        if len(items) < rows:
            break
        offset += rows
        time.sleep(0.3)
    print(f"  Crossref ORCID sweep  : {len(found)} DOIs")
    return found


def dois_from_local_orcid() -> set[str]:
    if not os.path.exists(ORCID_LOCAL):
        return set()
    try:
        blob = json.dumps(json.load(open(ORCID_LOCAL, encoding="utf-8")))
    except Exception:
        return set()
    found = {norm_doi(m) for m in re.findall(r'10\.\d{4,9}/[^\s"\\<>]+', blob)}
    found.discard(None)
    print(f"  ORCID record (local)  : {len(found)} DOIs")
    return found


def simplify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def resolve_missing_titles(prev_pubs: list, known: set[str], mapped_titles: set[str]) -> set[str]:
    """One-time rescue for papers carried over from the Scholar era that have
    no DOI yet: ask Crossref for the title and accept only an exact match
    after punctuation and case are stripped."""
    rescued = set()
    for p in prev_pubs:
        d = norm_doi(p.get("link")) or norm_doi(p.get("doi"))
        if d and d in known:
            continue
        title = (p.get("title") or "").strip()
        if len(title) < 20 or simplify(title) in mapped_titles:
            continue
        url = ("https://api.crossref.org/works"
               f"?query.bibliographic={urllib.parse.quote(title)}"
               "&rows=3&select=DOI,title"
               f"&mailto={urllib.parse.quote(MAILTO)}")
        page = http_json(url)
        for it in ((page or {}).get("message") or {}).get("items") or []:
            cand = simplify((it.get("title") or [""])[0])
            if cand and cand == simplify(title):
                dd = norm_doi(it.get("DOI"))
                if dd and dd not in known:
                    rescued.add(dd)
                    print(f"    rescued by title: {dd}  {title[:56]}")
                break
        time.sleep(0.4)
    return rescued


# ── 2 · counts per paper ─────────────────────────────────────────────────

def openalex_counts(dois: list[str], meta: dict) -> dict[str, int]:
    counts = {}
    for i in range(0, len(dois), 50):
        chunk = "|".join(dois[i:i + 50])
        url = ("https://api.openalex.org/works"
               f"?filter=doi:{urllib.parse.quote(chunk, safe='|/')}"
               "&per-page=50"
               "&select=doi,type,title,display_name,publication_year,cited_by_count,authorships,primary_location"
               f"&mailto={urllib.parse.quote(MAILTO)}")
        page = http_json(url)
        for w in (page or {}).get("results", []):
            d = norm_doi(w.get("doi"))
            if d:
                counts[d] = int(w.get("cited_by_count") or 0)
                meta.setdefault(d, w)
        time.sleep(0.2)
    return counts


def crossref_counts(dois: list[str], meta: dict) -> dict[str, int]:
    counts = {}
    for n, d in enumerate(dois, 1):
        url = (f"https://api.crossref.org/works/{urllib.parse.quote(d)}"
               f"?mailto={urllib.parse.quote(MAILTO)}")
        page = http_json(url, retries=2)
        msg = (page or {}).get("message")
        if not msg:
            continue
        counts[d] = int(msg.get("is-referenced-by-count") or 0)
        meta.setdefault("_cr:" + d, msg)
        if n % 25 == 0:
            print(f"    crossref {n}/{len(dois)}")
        time.sleep(0.12)
    return counts


def s2_counts(dois: list[str]) -> dict[str, int]:
    if not S2_KEY:
        print("  Semantic Scholar      : skipped, no S2_API_KEY")
        return {}
    counts = {}
    for i in range(0, len(dois), 400):
        chunk = dois[i:i + 400]
        page = http_json("https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount",
                         data=json.dumps({"ids": ["DOI:" + d for d in chunk]}).encode(),
                         headers={"x-api-key": S2_KEY}, retries=2)
        if not isinstance(page, list):
            continue
        for d, r in zip(chunk, page):
            if isinstance(r, dict) and r.get("citationCount") is not None:
                counts[d] = int(r["citationCount"])
        time.sleep(1.0)
    print(f"  Semantic Scholar      : {len(counts)} papers")
    return counts


# ── 3 · shape the output ─────────────────────────────────────────────────

def authors_string(work: dict | None) -> str:
    if not work:
        return ""
    names = []
    for a in (work.get("authorships") or [])[:3]:
        nm = ((a.get("author") or {}).get("display_name") or "").strip()
        if nm:
            parts = nm.split()
            names.append((parts[0][0] + " " + " ".join(parts[1:])) if len(parts) > 1 else nm)
    total = len(work.get("authorships") or [])
    out = ", ".join(names)
    if total > 3:
        out += ", et al"
    return out


def venue_string(oa: dict | None, cr: dict | None) -> str:
    if oa:
        loc = oa.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name")
        if src:
            bits = [src]
            if oa.get("publication_year"):
                bits.append(str(oa["publication_year"]))
            return ", ".join(bits)
    if cr:
        ct = cr.get("container-title") or []
        if ct:
            return ct[0]
    return ""


# Things that carry a DOI but are not publications. A peer review someone
# wrote is scholarly service (the ORCID panel counts those separately), and a
# correction notice is not a second paper.
NON_PAPER_TYPES = {"peer-review", "erratum", "retraction", "component", "grant", "paratext", "supplementary-materials"}
NON_PAPER_TITLE = re.compile(
    r"^(peer review report|reviewer report|review for|author response|decision letter|"
    r"response to reviewers|correction to|erratum|corrigendum|retraction|expression of concern)\b", re.I)

PREPRINT_HOSTS = ("research square", "biorxiv", "medrxiv", "arxiv", "ssrn", "preprints", "authorea", "chemrxiv")


def is_preprint(p: dict) -> bool:
    return any(h in (p.get("venue") or "").lower() for h in PREPRINT_HOSTS)


def same_paper(a: dict, b: dict) -> bool:
    """Titles match exactly after punctuation is stripped, or one is a
    preprint whose title shares its opening words with the other and whose
    words are almost all contained in it. Preprints often spell out an
    acronym the journal version abbreviates, which defeats a prefix match."""
    ta, tb = simplify(a["title"]), simplify(b["title"])
    if ta == tb:
        return True
    if is_preprint(a) == is_preprint(b):
        return False
    wa, wb = ta.split(), tb.split()
    if wa[:6] != wb[:6]:
        return False
    short, long_ = (set(wa), set(wb)) if len(wa) <= len(wb) else (set(wb), set(wa))
    return len(short & long_) / max(1, len(short)) >= 0.8


def collapse_versions(pubs: list, dois_out: dict) -> tuple[list, dict]:
    """A preprint and its published article carry different DOIs but are one
    paper. Keep the published version, and keep the higher of the two counts
    rather than their sum, which could count the same citing paper twice."""
    kept, dropped = [], set()
    ordered = sorted(pubs, key=lambda p: (is_preprint(p), -int(p["cited_by"])))
    for p in ordered:
        home = next((k for k in kept if same_paper(k, p)), None)
        if home is None:
            kept.append(dict(p))
            continue
        home["cited_by"] = max(int(home["cited_by"]), int(p["cited_by"]))
        dropped.add(pub_key(p))
        print(f"    merged version: {p['venue'][:28]} into {home['venue'][:28]}  {home['title'][:48]}")
    return kept, {k: v for k, v in dois_out.items() if k not in dropped}


def h_index(counts: list[int]) -> int:
    return sum(1 for i, c in enumerate(sorted(counts, reverse=True), 1) if c >= i)


def main() -> None:
    if not OPENALEX_IDS:
        print("ERROR: OPENALEX_AUTHOR_IDS is not set.", file=sys.stderr)
        sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pubs_path = os.path.join(OUTPUT_DIR, "serpapi.json")
    metrics_path = os.path.join(OUTPUT_DIR, "metrics.json")
    dois_path = os.path.join(OUTPUT_DIR, "dois.json")

    prev_pubs = json.load(open(pubs_path, encoding="utf-8")) if os.path.exists(pubs_path) else []
    prev_dois_file = json.load(open(dois_path, encoding="utf-8")) if os.path.exists(dois_path) else {}
    prev_counts = {}
    for p in prev_pubs:
        d = norm_doi(p.get("link"))
        if d:
            prev_counts[d] = int(p.get("cited_by") or 0)
    prev_known = {norm_doi(v.get("doi")) for v in prev_dois_file.values()}
    prev_known.discard(None)

    print("=== Citations from open indexes ===")
    print(f"  OpenAlex authors      : {', '.join(OPENALEX_IDS)}")

    meta: dict = {}
    dois = set()
    oa_author, oa_meta = dois_from_openalex_author()
    meta.update(oa_meta)
    dois |= oa_author
    dois |= dois_from_crossref_orcid()
    dois |= dois_from_local_orcid()
    if prev_known:
        dois |= prev_known
        print(f"  carried from last run : {len(prev_known)} DOIs")
    mapped_titles = {simplify(v.get("matched_title")) for v in prev_dois_file.values() if v.get("matched_title")}
    rescued = resolve_missing_titles(prev_pubs, dois, mapped_titles)
    dois |= rescued
    dois = sorted(d for d in dois if d)
    print(f"  total distinct papers : {len(dois)}")

    print("  fetching counts...")
    oa_c = openalex_counts(dois, meta)
    print(f"  OpenAlex counts       : {len(oa_c)} papers, {sum(oa_c.values())} citations")
    cr_c = crossref_counts(dois, meta)
    print(f"  Crossref counts       : {len(cr_c)} papers, {sum(cr_c.values())} citations")
    s2_c = s2_counts(dois)

    resolved = [d for d in dois if d in oa_c or d in cr_c or d in s2_c]
    if prev_known and len(resolved) < MIN_RETAINED_FRACTION * len(prev_known):
        print(f"FATAL: only resolved {len(resolved)} of {len(prev_known)} known papers "
              f"(< {int(MIN_RETAINED_FRACTION * 100)}%). Refusing to write a collapsed "
              f"citation count. Nothing changed.", file=sys.stderr)
        sys.exit(1)

    pubs, dois_out, carried, not_papers = [], {}, 0, 0
    for d in dois:
        candidates = [c for c in (oa_c.get(d), cr_c.get(d), s2_c.get(d)) if c is not None]
        if candidates:
            cited = max(candidates)
        elif d in prev_counts:
            cited = prev_counts[d]
            carried += 1
        else:
            continue
        oa = meta.get(d)
        cr = meta.get("_cr:" + d)
        title = ((oa or {}).get("display_name") or (oa or {}).get("title")
                 or ((cr or {}).get("title") or [""])[0] or "").strip()
        if not title:
            for p in prev_pubs:
                if norm_doi(p.get("link")) == d and p.get("title"):
                    title = p["title"]
                    break
        if not title:
            continue
        kind = ((oa or {}).get("type") or (cr or {}).get("type") or "").lower()
        if kind in NON_PAPER_TYPES or NON_PAPER_TITLE.search(title):
            not_papers += 1
            continue
        year = (oa or {}).get("publication_year")
        if not year and cr:
            parts = ((cr.get("issued") or {}).get("date-parts") or [[None]])[0]
            year = parts[0] if parts else None
        link = f"https://doi.org/{d}"
        pub = {
            "title": title,
            "authors": authors_string(oa),
            "venue": venue_string(oa, cr),
            "year": str(year or ""),
            "cited_by": int(cited),
            "link": link,
            "author_id": AUTHOR_ID_FIELD,
        }
        pubs.append(pub)
        dois_out[pub_key(pub)] = {
            "doi": d,
            "confidence": 1.0,
            "matched_title": title,
            "matched_year": int(year) if year else None,
            "matched_at": utc_now(),
        }

    pubs, dois_out = collapse_versions(pubs, dois_out)
    pubs.sort(key=lambda p: (-int(p["cited_by"]), p["title"]))
    counts = [int(p["cited_by"]) for p in pubs]
    metrics = {
        "total_documents": len(pubs),
        "total_citations": sum(counts),
        "h_index": h_index(counts),
        "author_id": AUTHOR_ID_FIELD,
        "source": "open_indexes",
        "last_updated": utc_now(),
        "sources": {
            "openalex": {"papers": len(oa_c), "citations": sum(oa_c.values())},
            "crossref": {"papers": len(cr_c), "citations": sum(cr_c.values())},
            "semantic_scholar": {"papers": len(s2_c), "citations": sum(s2_c.values())},
            "carried_forward": carried,
            "excluded_non_papers": not_papers,
        },
    }

    json.dump(pubs, open(pubs_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(metrics, open(metrics_path, "w", encoding="utf-8"), indent=2)
    json.dump(dois_out, open(dois_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("=== Done ===")
    print(f"  Publications : {metrics['total_documents']}")
    print(f"  Citations    : {metrics['total_citations']}")
    print(f"  h-index      : {metrics['h_index']}")
    print(f"  DOIs mapped  : {len(dois_out)}")
    if not_papers:
        print(f"  Left out {not_papers} DOI(s) that are peer reviews or notices, not papers")
    if carried:
        print(f"  Carried counts for {carried} paper(s) no source answered for this run")


if __name__ == "__main__":
    main()
