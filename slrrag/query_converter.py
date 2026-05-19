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

    This function finds all quoted phrases in the query and wraps each with
    (abstract:(...) OR title:(...)).

    Args:
        query (str): A Scopus query string with quoted phrases.

    Returns:
        str: The equivalent query formatted for Lens.org.

    Example:
        >>> query = '("risk assessment" OR "risk analysis") AND ("Offshore windfarm")'
        >>> convert_query_to_lens(query)
        '(abstract:("risk assessment") OR title:("risk assessment")) OR (abstract:("risk analysis") OR title:("risk analysis"))) AND (abstract:("Offshore windfarm") OR title:("Offshore windfarm"))'
    """
    def replace_quoted(match):
        quoted_text = match.group(0)
        return f'(title:({quoted_text}) OR abstract:({quoted_text}))'

    return re.sub(r'"[^"]*"', replace_quoted, query)
