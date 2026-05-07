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



def scopus_to_dimensions_query(scopus_query: str) -> str:
    """
    Convert a Scopus query to a Dimensions.ai search URL for title and abstract.

    Args:
        scopus_query (str): The query in Scopus format.

    Returns:
        str: The Dimensions.ai search URL.
    """
    # Replace Scopus-specific syntax if any (e.g., TITLE-ABS-KEY)
    # Here, we assume the input is already in a logical format like the example.

    # Encode the query for URL
    encoded_query = urllib.parse.quote(scopus_query, safe='() ')

    # Construct the Dimensions.ai URL
    base_url = "https://app.dimensions.ai/discover/publication"
    params = {
        "search_mode": "content",
        "search_text": encoded_query,
        "search_type": "kws",
        "search_field": "text_search"
    }

    # Build the URL with parameters
    query_string = urllib.parse.urlencode(params)
    dimensions_url = f"{base_url}?{query_string}"

    return dimensions_url



def highlight_differences_colored(str1: str, str2: str) -> str:
    """
    Highlight differences between two strings:
    - Green: Similar parts
    - Red: Differing parts
    - Blue: Added parts

    Args:
        str1 (str): First string.
        str2 (str): Second string.

    Returns:
        str: Colored string with differences highlighted.
    """
    # ANSI color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    # Use SequenceMatcher to find matching blocks
    matcher = difflib.SequenceMatcher(None, str1, str2)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Similar parts (green)
            result.append(f"{GREEN}{str1[i1:i2]}{RESET}")
        elif tag == 'replace':
            # Differing parts (red for str1, blue for str2)
            result.append(f"{RED}{str1[i1:i2]}{RESET}")
            result.append(f"{BLUE}{str2[j1:j2]}{RESET}")
        elif tag == 'delete':
            # Only in str1 (red)
            result.append(f"{RED}{str1[i1:i2]}{RESET}")
        elif tag == 'insert':
            # Only in str2 (blue)
            result.append(f"{BLUE}{str2[j1:j2]}{RESET}")

    return ''.join(result)
# Example usage

if __name__ == "__main__":

    scopus_query = """
    ("risk assessment" OR "risk analysis") AND
    ("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
    ("maritime" OR "navigational" OR "nautical")
    """
    str1 = "Hello world! This is a test."
    str2 = "Hello there! This is a test case."
    print(highlight_differences_colored(str1, str2))
    expected_link = "https://app.dimensions.ai/discover/publication?search_mode=content&search_text=(%22risk%20assessment%22%20OR%20%22risk%20analysis%22)%20AND%0A(%22Offshore%20windfarm%22%20OR%20%22Offshore%20windmill%22%20OR%20%22Offshore%20wind%20turbine%22%20OR%20%22Offshore%20wind%20park%22%20OR%20%22OWF%22)%20AND%0A(%22maritime%22%20OR%20%22navigational%22%20OR%20%22nautical%22)&search_type=kws&search_field=text_search"
    dimensions_url = scopus_to_dimensions_query(scopus_query.strip())
    print(dimensions_url)
    if expected_link != dimensions_url:
        print(highlight_differences_colored(expected_link, dimensions_url))
        assert expected_link == dimensions_url
    # query = "Ship Collision Risk assessment"
    # df = query_arxiv(query, max_results=20)
    # print(df.head())
