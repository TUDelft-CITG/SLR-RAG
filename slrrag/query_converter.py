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



def test_1():

    example_query = (
        '("risk assessment" OR "risk analysis") AND\n'
        '("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND\n'
        '("maritime" OR "navigational" OR "nautical")'
    )
    expected_url = (
        "https://app.dimensions.ai/discover/publication?search_mode=content&"
        "search_text=(%22risk%20assessment%22%20OR%20%22risk%20analysis%22)%20AND%0A"
        "(%22Offshore%20windfarm%22%20OR%20%22Offshore%20windmill%22%20OR%20%22Offshore%20wind%20turbine%22%20OR%20%22Offshore%20wind%20park%22%20OR%20%22OWF%22)%20AND%0A"
        "(%22maritime%22%20OR%20%22navigational%22%20OR%20%22nautical%22)&"
        "search_type=kws&search_field=text_search"
    )
    assert query_to_dimensions_url(example_query) == expected_url
def test_2():
    example_query = """
("collision" OR "allision" OR "accident" OR "safety" OR "risk assessment" OR "risk analysis") AND
("Offshore infrastructure" OR "Offshore construction"
    OR "Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF"
    OR "Offshore platform" OR "Oil platform" OR "Hydrogen platforms"
    OR "Offshore quay" OR "Offshore wharf"
    OR "Artificial Island" OR "Synthetic Island"
    OR "Bridge"
    OR "Flotel"
    OR "Aquaculture Farms"
    OR "Offshore Lidar"
    OR "Storm surge barrier" OR  "Flood Barrier"
) AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
    """
    expected_url = "https://app.dimensions.ai/discover/publication?search_mode=content&search_text=%0A(%22collision%22%20OR%20%22allision%22%20OR%20%22accident%22%20OR%20%22safety%22%20OR%20%22risk%20assessment%22%20OR%20%22risk%20analysis%22)%20AND%0A(%22Offshore%20infrastructure%22%20OR%20%22Offshore%20construction%22%0A%20%20%20%20OR%20%22Offshore%20windfarm%22%20OR%20%22Offshore%20windmill%22%20OR%20%22Offshore%20wind%20turbine%22%20OR%20%22Offshore%20wind%20park%22%20OR%20%22OWF%22%0A%20%20%20%20OR%20%22Offshore%20platform%22%20OR%20%22Oil%20platform%22%20OR%20%22Hydrogen%20platforms%22%0A%20%20%20%20OR%20%22Offshore%20quay%22%20OR%20%22Offshore%20wharf%22%0A%20%20%20%20OR%20%22Artificial%20Island%22%20OR%20%22Synthetic%20Island%22%0A%20%20%20%20OR%20%22Bridge%22%0A%20%20%20%20OR%20%22Flotel%22%0A%20%20%20%20OR%20%22Aquaculture%20Farms%22%0A%20%20%20%20OR%20%22Offshore%20Lidar%22%0A%20%20%20%20OR%20%22Storm%20surge%20barrier%22%20OR%20%20%22Flood%20Barrier%22%0A)%20AND%0A(%22Strategic%22%20OR%20%22Static%22%20OR%20%22Long-term%22%20OR%20%22Marine%20spatial%20planning%22%20OR%20%22Large%20scale%22)%20AND%0A(%22maritime%22%20OR%20%20%22navigational%22%20OR%20%22nautical%22)%0A%20%20%20%20&search_type=kws&search_field=text_search"
    get_url =  query_to_dimensions_url(example_query)
    print(get_url)
    assert get_url == expected_url
    