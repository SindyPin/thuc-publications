#!/usr/bin/env python3
"""
Fetch publications from Semantic Scholar API and generate HTML.
This script fetches all publications for Dr. Thuc Le and generates
an HTML file that can be included in the website.

Usage:
    python fetch_publications.py

Output:
    - publications.html: HTML snippet with all publications
    - publications.json: Raw data backup
"""

import requests
import json
from datetime import datetime
from collections import defaultdict
import time
import os

# Configuration
AUTHOR_NAME = "Thuc Duy Le"
# Semantic Scholar author ID for Dr. Thuc Le (UniSA)
# You can find this by searching: https://www.semanticscholar.org/
AUTHOR_ID = "2482441"  # This is Thuc Duy Le's Semantic Scholar ID

# Alternative: Use Google Scholar ID with scholarly library
GOOGLE_SCHOLAR_ID = "wMSCRxUAAAAJ"

# API endpoints
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"


def fetch_from_semantic_scholar(author_id: str) -> list:
    """Fetch all publications from Semantic Scholar API."""
    publications = []
    offset = 0
    limit = 100
    
    print(f"Fetching publications for author ID: {author_id}")
    
    while True:
        url = f"{SEMANTIC_SCHOLAR_API}/author/{author_id}/papers"
        params = {
            "fields": "title,year,authors,venue,publicationDate,externalIds,url,citationCount,abstract",
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            papers = data.get("data", [])
            if not papers:
                break
                
            publications.extend(papers)
            print(f"  Fetched {len(publications)} papers so far...")
            
            offset += limit
            time.sleep(1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Semantic Scholar: {e}")
            break
    
    return publications


def search_author_by_name(name: str) -> str:
    """Search for author ID by name if not known."""
    url = f"{SEMANTIC_SCHOLAR_API}/author/search"
    params = {"query": name, "limit": 5}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        authors = data.get("data", [])
        for author in authors:
            # Look for the correct author (UniSA affiliation)
            print(f"Found: {author.get('name')} (ID: {author.get('authorId')})")
        
        if authors:
            return authors[0].get("authorId")
            
    except requests.exceptions.RequestException as e:
        print(f"Error searching author: {e}")
    
    return None


def group_by_year(publications: list) -> dict:
    """Group publications by year."""
    by_year = defaultdict(list)
    
    for pub in publications:
        year = pub.get("year")
        if year:
            by_year[year].append(pub)
        else:
            by_year["Unknown"].append(pub)
    
    return dict(sorted(by_year.items(), key=lambda x: (x[0] != "Unknown", x[0]), reverse=True))


def generate_html(publications_by_year: dict) -> str:
    """Generate HTML for publications list."""
    html_parts = []
    
    html_parts.append("""
<!-- Auto-generated publications list -->
<!-- Last updated: {update_time} -->
<!-- Source: Semantic Scholar API -->

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
""".format(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    total_count = 0
    
    for year, pubs in publications_by_year.items():
        html_parts.append(f"\n<h3>{year}</h3>\n")
        html_parts.append("<ol class='pub-list'>\n")
        
        for i, pub in enumerate(pubs, 1):
            total_count += 1
            title = pub.get("title", "Untitled")
            authors = ", ".join([a.get("name", "") for a in pub.get("authors", [])[:6]])
            if len(pub.get("authors", [])) > 6:
                authors += ", ..."
            venue = pub.get("venue", "")
            url = pub.get("url", "")
            
            # Get external links
            external_ids = pub.get("externalIds", {})
            doi = external_ids.get("DOI", "")
            arxiv = external_ids.get("ArXiv", "")
            pubmed = external_ids.get("PubMed", "")
            
            html_parts.append(f"""<li class='pub-item'>
    <span class='pub-title'>{title}</span><br>
    <span class='pub-authors'>{authors}</span><br>
    <span class='pub-venue'>{venue}</span>
    <div class='pub-links'>
""")
            
            if url:
                html_parts.append(f'        <a href="{url}" target="_blank">[Semantic Scholar]</a>\n')
            if doi:
                html_parts.append(f'        <a href="https://doi.org/{doi}" target="_blank">[DOI]</a>\n')
            if arxiv:
                html_parts.append(f'        <a href="https://arxiv.org/abs/{arxiv}" target="_blank">[arXiv]</a>\n')
            if pubmed:
                html_parts.append(f'        <a href="https://pubmed.ncbi.nlm.nih.gov/{pubmed}" target="_blank">[PubMed]</a>\n')
            
            html_parts.append("    </div>\n</li>\n")
        
        html_parts.append("</ol>\n")
    
    # Add summary at top
    summary = f"<p><strong>Total publications: {total_count}</strong></p>\n"
    html_parts.insert(1, summary)
    
    return "".join(html_parts)


def save_results(publications: list, html_content: str, output_dir: str = "."):
    """Save publications to JSON and HTML files."""
    # Save raw JSON
    json_path = os.path.join(output_dir, "publications.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(publications)} publications to {json_path}")
    
    # Save HTML
    html_path = os.path.join(output_dir, "publications.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML to {html_path}")


def main():
    print("=" * 60)
    print("Publication Fetcher for Dr. Thuc Le")
    print("=" * 60)
    
    # Try to fetch using known author ID
    publications = fetch_from_semantic_scholar(AUTHOR_ID)
    
    # If no results, try searching by name
    if not publications:
        print("\nNo publications found with author ID, searching by name...")
        author_id = search_author_by_name(AUTHOR_NAME)
        if author_id:
            print(f"Found author ID: {author_id}")
            publications = fetch_from_semantic_scholar(author_id)
    
    if not publications:
        print("\nERROR: Could not fetch publications!")
        print("Please verify the AUTHOR_ID in the script.")
        return
    
    print(f"\nTotal publications fetched: {len(publications)}")
    
    # Group by year
    by_year = group_by_year(publications)
    
    # Generate HTML
    html_content = generate_html(by_year)
    
    # Save results
    save_results(publications, html_content)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
