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
        example_query = (
            '("risk assessment" OR "risk analysis") AND\n'
            '("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND\n'
            '("maritime" OR "navigational" OR "nautical")'
        )
        expected_url = "https://app.dimensions.ai/discover/publication?search_mode=content&search_text=(%22collision%22%20OR%20%22allision%22%20OR%20%22accident%22%20OR%20%22safety%22%20OR%20%22risk%20assessment%22%20OR%20%22risk%20analysis%22)%20AND%0A(%22Offshore%20infrastructure%22%20OR%20%22Offshore%20construction%22%0A%09OR%20%22Offshore%20windfarm%22%20OR%20%22Offshore%20windmill%22%20OR%20%22Offshore%20wind%20turbine%22%20OR%20%22Offshore%20wind%20park%22%20OR%20%22OWF%22%0A%09OR%20%22Offshore%20platform%22%20OR%20%22Oil%20platform%22%20OR%20%22Hydrogen%20platforms%22%0A%09OR%20%22Offshore%20quay%22%20OR%20%22Offshore%20wharf%22%0A%09OR%20%22Artificial%20Island%22%20OR%20%22Synthetic%20Island%22%0A%09OR%20%22Bridge%22%0A%09OR%20%22Flotel%22%0A%09OR%20%22Aquaculture%20Farms%22%0A%09OR%20%22Offshore%20Lidar%22%0A%09OR%20%22Storm%20surge%20barrier%22%20OR%20%20%22Flood%20Barrier%22%0A)%20AND%0A(%22Strategic%22%20OR%20%22Static%22%20OR%20%22Long-term%22%20OR%20%22Marine%20spatial%20planning%22%20OR%20%22Large%20scale%22)%20AND%0A(%22maritime%22%20OR%20%20%22navigational%22%20OR%20%22nautical%22)&search_type=kws&search_field=text_search"
        assert query_to_dimensions_url(example_query) == expected_url
        
    test_1()
    test_2()