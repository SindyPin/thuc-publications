#!/usr/bin/env python3
"""
Fetch Dr Thuc Duy Le's publications from ORCID and generate HTML.

Source of truth:
    ORCID  : https://orcid.org/0000-0002-9732-4313

The ORCID public API returns the canonical list of works. Because ORCID work
summaries don't always include full author lists or journal names, each work is
enriched via Crossref (by DOI) when possible. Works without a DOI fall back to
the metadata stored in ORCID itself.

Usage:
    python fetch_publications.py

Output:
    - publications.html : HTML snippet embedded by the website (index.html)
    - publications.json : Raw data backup
"""

import requests
import json
import time
import os
from datetime import datetime
from collections import defaultdict

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
AUTHOR_NAME = "Thuc Duy Le"
ORCID_ID = "0000-0002-9732-4313"          # Dr Thuc Duy Le
CONTACT_EMAIL = "thuc.le@adelaide.edu.au"  # used as a polite Crossref User-Agent

ORCID_API = "https://pub.orcid.org/v3.0"
CROSSREF_API = "https://api.crossref.org/works"

HEADERS_ORCID = {"Accept": "application/json"}
HEADERS_CROSSREF = {
    "User-Agent": f"thuc-publications/2.0 (mailto:{CONTACT_EMAIL})"
}

MAX_AUTHORS = 6  # show at most this many authors, then ", ..."


# ----------------------------------------------------------------------------
# ORCID
# ----------------------------------------------------------------------------
def fetch_orcid_works(orcid_id: str) -> list:
    """Return the list of work-summary groups from ORCID."""
    url = f"{ORCID_API}/{orcid_id}/works"
    print(f"Fetching ORCID works for {orcid_id} ...")
    r = requests.get(url, headers=HEADERS_ORCID, timeout=60)
    r.raise_for_status()
    groups = r.json().get("group", [])
    print(f"  ORCID returned {len(groups)} work groups")
    return groups


def best_external_ids(summary: dict) -> dict:
    """Extract DOI / arXiv / PubMed ids from an ORCID work summary."""
    ids = {}
    ext = (summary.get("external-ids") or {}).get("external-id", []) or []
    for e in ext:
        typ = (e.get("external-id-type") or "").lower()
        val = e.get("external-id-value") or ""
        if not val:
            continue
        if typ == "doi" and "doi" not in ids:
            ids["doi"] = val.replace("https://doi.org/", "").strip()
        elif typ == "arxiv" and "arxiv" not in ids:
            ids["arxiv"] = val.replace("arXiv:", "").strip()
        elif typ in ("pmid", "pubmed") and "pmid" not in ids:
            ids["pmid"] = val.strip()
    return ids


def parse_orcid_summary(summary: dict) -> dict:
    """Build a publication record from an ORCID work summary (no Crossref)."""
    title = (((summary.get("title") or {}).get("title") or {}).get("value")) or "Untitled"
    journal = (summary.get("journal-title") or {}).get("value") or ""
    year = None
    pub_date = summary.get("publication-date") or {}
    if pub_date and pub_date.get("year"):
        try:
            year = int(pub_date["year"]["value"])
        except (KeyError, TypeError, ValueError):
            year = None
    ids = best_external_ids(summary)
    return {
        "title": title.strip(),
        "authors": [],            # ORCID summaries rarely carry co-authors
        "venue": journal.strip(),
        "year": year,
        "doi": ids.get("doi", ""),
        "arxiv": ids.get("arxiv", ""),
        "pmid": ids.get("pmid", ""),
        "source": "orcid",
    }


# ----------------------------------------------------------------------------
# Crossref enrichment
# ----------------------------------------------------------------------------
def enrich_with_crossref(doi: str) -> dict:
    """Return {title, authors[], venue, year} for a DOI, or {} on failure."""
    try:
        r = requests.get(f"{CROSSREF_API}/{doi}", headers=HEADERS_CROSSREF, timeout=30)
        if r.status_code != 200:
            return {}
        m = r.json().get("message", {})
    except requests.exceptions.RequestException:
        return {}

    # Authors
    authors = []
    for a in m.get("author", []) or []:
        given = a.get("given", "")
        family = a.get("family", "")
        name = (f"{given} {family}").strip() or a.get("name", "")
        if name:
            authors.append(name)

    # Venue
    venue = ""
    for key in ("container-title", "short-container-title"):
        v = m.get(key)
        if v:
            venue = v[0]
            break
    if not venue and m.get("institution"):
        inst = m["institution"]
        venue = inst[0].get("name", "") if isinstance(inst, list) else ""

    # Year
    year = None
    for key in ("published-print", "published-online", "published", "issued", "created"):
        dp = (m.get(key) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break

    title = ""
    if m.get("title"):
        title = m["title"][0]

    return {"title": title, "authors": authors, "venue": venue, "year": year}


def build_publications(groups: list) -> list:
    """Merge ORCID + Crossref into a clean, de-duplicated publication list."""
    pubs = []
    seen = set()  # de-dup by DOI or normalised title

    for g in groups:
        summaries = g.get("work-summary", []) or []
        if not summaries:
            continue
        rec = parse_orcid_summary(summaries[0])

        # Enrich via Crossref when a DOI is available
        if rec["doi"]:
            cr = enrich_with_crossref(rec["doi"])
            if cr:
                if cr.get("authors"):
                    rec["authors"] = cr["authors"]
                if cr.get("venue"):
                    rec["venue"] = cr["venue"]
                if cr.get("title"):
                    rec["title"] = cr["title"]
                if cr.get("year"):
                    rec["year"] = cr["year"]
            time.sleep(0.4)  # be polite to Crossref

        key = rec["doi"].lower() if rec["doi"] else rec["title"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        pubs.append(rec)
        print(f"  + {rec.get('year','????')}  {rec['title'][:70]}")

    return pubs


# ----------------------------------------------------------------------------
# HTML generation
# ----------------------------------------------------------------------------
def group_by_year(pubs: list) -> dict:
    by_year = defaultdict(list)
    for p in pubs:
        by_year[p.get("year") or "Other"].append(p)
    return dict(sorted(by_year.items(),
                       key=lambda x: (x[0] != "Other", x[0]), reverse=True))


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_html(by_year: dict) -> str:
    out = []
    out.append(f"""
<!-- Auto-generated publications list -->
<!-- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Source: ORCID ({ORCID_ID}) enriched with Crossref -->

<style>
.pub-list {{ list-style-type: decimal; }}
.pub-item {{ margin-bottom: 1em; }}
.pub-title {{ font-weight: normal; }}
.pub-authors {{ color: #666; }}
.pub-venue {{ font-style: italic; }}
.pub-links {{ margin-top: 0.3em; }}
.pub-links a {{ margin-right: 1em; text-decoration: none; color: #0066cc; }}
.pub-links a:hover {{ text-decoration: underline; }}
</style>
""")

    total = sum(len(v) for v in by_year.values())
    out.append(f"<p><strong>Total publications: {total}</strong></p>\n")

    for year, pubs in by_year.items():
        out.append(f"\n<h3>{year}</h3>\n<ol class='pub-list'>\n")
        for p in pubs:
            authors = ", ".join(p["authors"][:MAX_AUTHORS])
            if len(p["authors"]) > MAX_AUTHORS:
                authors += ", ..."
            out.append("<li class='pub-item'>\n")
            out.append(f"    <span class='pub-title'>{esc(p['title'])}</span><br>\n")
            if authors:
                out.append(f"    <span class='pub-authors'>{esc(authors)}</span><br>\n")
            if p["venue"]:
                out.append(f"    <span class='pub-venue'>{esc(p['venue'])}</span>\n")
            out.append("    <div class='pub-links'>\n")
            if p["doi"]:
                out.append(f'        <a href="https://doi.org/{p["doi"]}" target="_blank">[DOI]</a>\n')
            if p["arxiv"]:
                out.append(f'        <a href="https://arxiv.org/abs/{p["arxiv"]}" target="_blank">[arXiv]</a>\n')
            if p["pmid"]:
                out.append(f'        <a href="https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}" target="_blank">[PubMed]</a>\n')
            out.append(f'        <a href="https://orcid.org/{ORCID_ID}" target="_blank">[ORCID]</a>\n')
            out.append("    </div>\n</li>\n")
        out.append("</ol>\n")

    return "".join(out)


def save(pubs: list, html: str, out_dir: str = "."):
    with open(os.path.join(out_dir, "publications.json"), "w", encoding="utf-8") as f:
        json.dump(pubs, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "publications.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved publications.json and publications.html ({len(pubs)} works)")


def main():
    print("=" * 60)
    print(f"ORCID Publication Fetcher — {AUTHOR_NAME} ({ORCID_ID})")
    print("=" * 60)

    groups = fetch_orcid_works(ORCID_ID)
    if not groups:
        print("ERROR: No works returned from ORCID. Aborting.")
        return

    pubs = build_publications(groups)
    by_year = group_by_year(pubs)
    html = generate_html(by_year)
    save(pubs, html)
    print("\nDone!")


if __name__ == "__main__":
    main()
