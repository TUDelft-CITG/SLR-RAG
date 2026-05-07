import arxiv
import pandas as pd
from typing import List, Dict
import urllib.parse
# Example usage

import difflib

def query_arxiv(query: str, max_results: int = 100) -> pd.DataFrame:
    """
    Query arXiv and return results as a DataFrame with columns:
    title, year, doi, abstract, arxiv_id.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = []
    for entry in client.results(search):
        # For weird reasons, it does not take account of the query.
        results.append({
            "title": entry.title,
            "year": int(entry.published.year) if entry.published else None,
            "doi": getattr(entry, 'doi', None),
            "abstract": entry.summary.replace('\n', ' ').strip(),
            "arxiv_id": entry.entry_id.split('/abs/')[-1]
        })
    
    return pd.DataFrame(results)



if __name__ == "__main__":
    query = "Ship Collision Risk assessment"
    df = query_arxiv(query, max_results=20)
    print(df.head())
