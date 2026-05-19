def query_to_dimensions_url(query: str) -> str:
    """
    Convert a Scopus query string to a Dimensions.ai discover URL for title and abstract search.
    
    Args:
        query: The Scopus query string (e.g., '("risk assessment" OR "risk analysis") AND ...')
    
    Returns:
        The corresponding Dimensions.ai URL with the query URL-encoded.
    """
    encoded_query = query.replace('"', '%22').replace(' ', '%20').replace('\n', '%0A')
    base_url = "https://app.dimensions.ai/discover/publication"
    return (
        f"{base_url}?search_mode=content&search_text={encoded_query}"
        f"&search_type=kws&search_field=text_search"
    )

import re

def convert_query_to_lens(query: str):
    """
    Convert a query string into the equivalent Lens.org query format.

    This function parses a Scopus query supposing using the TITLE-ABS field and transforms it
    into a Lens.org-compatible query. The conversion ensures that each term or group of OR terms
    in the original query is expanded to search both the title and abstract fields in Lens.org.
    Parentheses and logical operators (AND, OR) are preserved to maintain the original query logic.
    The query MUST NOT have the field "TITLE-ABS" OR "TITLE-ABS-KEY".
    Args:
        query (str): A Scopus query string, typically using the TITLE-ABS-KEY field.
                            Example: '("risk assessment" OR "risk analysis") AND ...'

    Returns:
        str: The equivalent query formatted for Lens.org, with each term or group of OR terms
             wrapped in title:() OR abstract:() clauses.
             Example: '((title:("risk assessment") OR abstract:("risk assessment")) OR ...)'

    Example:
        >>> query = '("risk assessment" OR "risk analysis") AND ("Offshore windfarm")'
        >>> convert_query_to_lens(query)
        '((title:("risk assessment") OR abstract:("risk assessment")) OR (title:("risk analysis") OR abstract:("risk analysis"))) AND ((title:("Offshore windfarm") OR abstract:("Offshore windfarm")))'
    """
    # Split the inner query into top-level AND groups
    # We need to handle parentheses carefully
    def split_and_groups(s):
        groups = []
        depth = 0
        start = 0
        for i, c in enumerate(s):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif c == 'A' and s[i:i+3].upper() == 'AND' and depth == 0:
                groups.append(s[start:i].strip())
                start = i + 3
        groups.append(s[start:].strip())
        return groups

    and_groups = split_and_groups(query)

    # Process each AND group
    lens_groups = []
    for group in and_groups:
        # Remove outer parentheses if present
        group = group.strip()
        if group.startswith('(') and group.endswith(')'):
            group = group[1:-1].strip()

        # Split into OR terms
        or_terms = [t.strip() for t in re.split(r'\s+OR\s+', group, flags=re.IGNORECASE)]

        # For each OR term, create title: or abstract: version
        lens_or_terms = []
        for term in or_terms:
            # Remove quotes if present
            clean_term = term.strip('"\'')
            lens_or_terms.append(f'title:("{clean_term}") OR abstract:("{clean_term}")')

        # Join OR terms
        lens_group = f'({" OR ".join(lens_or_terms)})'
        lens_groups.append(lens_group)

    # Join AND groups
    return f'({" AND ".join(lens_groups)})'



