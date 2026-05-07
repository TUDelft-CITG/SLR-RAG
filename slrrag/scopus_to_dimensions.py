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


if __name__ == "__main__":
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
    print(query_to_dimensions_url(example_query))
