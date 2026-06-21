# Dr Thuc Duy Le — Website & Auto-Updating Publications

This repository hosts **Dr Thuc Duy Le's** personal academic website and a small
pipeline that keeps his publication list up to date automatically from **ORCID**.

- **ORCID iD:** [0000-0002-9732-4313](https://orcid.org/0000-0002-9732-4313)
- **Live website:** `index.html` (can be served with GitHub Pages)

---

## What's in here

| File | Purpose |
|------|---------|
| `index.html` | The full website (Adelaide University branding, responsive). |
| `Thuc_photo.jpeg` | Profile photo used in the site header. |
| `fetch_publications.py` | Fetches publications from **ORCID** (enriched with Crossref) and writes `publications.html` + `publications.json`. |
| `requirements.txt` | Python dependency (`requests`). |
| `.github/workflows/update-publications.yml` | GitHub Action that re-runs the fetcher on a schedule. |
| `publications.html` | Auto-generated list embedded by the website (created by the script). |
| `publications.json` | Raw publication data backup (created by the script). |

---

## How the publication list updates (now via ORCID)

Previously this list was built from Semantic Scholar. It now uses **ORCID as the
single source of truth**:

1. `fetch_publications.py` calls the ORCID public API for
   [0000-0002-9732-4313](https://orcid.org/0000-0002-9732-4313) to get the
   canonical list of works.
2. For each work with a DOI, it pulls full author lists and journal names from
   **Crossref** (ORCID summaries often omit co-authors).
3. It writes `publications.html` (grouped by year) and `publications.json`.
4. `index.html` loads `publications.html` automatically, so the website always
   shows the latest list.

### Run it manually

```bash
pip install -r requirements.txt
python fetch_publications.py
```

### Automatic updates

The GitHub Action in `.github/workflows/update-publications.yml` runs every
Sunday at midnight UTC and commits any changes. You can also trigger it any time:

> **Actions** tab → **Update Publications** → **Run workflow**

To change the schedule, edit the `cron` expression:

```yaml
- cron: '0 0 * * 0'   # every Sunday at midnight UTC
- cron: '0 6 * * *'   # every day at 6am UTC
```

---

## Publishing the website with GitHub Pages

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** = *Deploy from a branch*.
3. Choose branch **main** and folder **/(root)**, then **Save**.
4. The site will be available at
   `https://sindypin.github.io/thuc-publications/`.

The site is self-contained — it only needs `index.html`, `Thuc_photo.jpeg`, and
the generated `publications.html`.

---

## Notes

- If a work in ORCID has no DOI, the script falls back to the title/journal/year
  stored directly in ORCID.
- To keep the list complete and accurate, make sure works are present and public
  on the ORCID record.
