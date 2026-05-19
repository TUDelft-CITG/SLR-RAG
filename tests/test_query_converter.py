from slrrag.query_converter import convert_query_to_lens, query_to_dimensions_url


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

def test_lens_1():
    input_query = """
    ("offshore") AND ("infrastructure" OR "construction" OR "installation" OR "windfarm" OR "windfarms" OR "wind farm" OR "wind farms" OR "windmill" OR "wind turbine" OR "wind park" OR "wind energy") AND
    (("Navigation risk assessment" OR "Navigational risk assessment") OR 
    (("collision" OR "allision") AND ("ship" OR "vessel") AND ("Probabily" OR "likelihood" OR "model")) OR
    ("risk" AND ("assess" OR "model" OR "predict") AND ("ship" OR "vessel" OR "maritime traffic")))
    """
    get_lens_query = convert_query_to_lens(input_query)
    print(get_lens_query)
