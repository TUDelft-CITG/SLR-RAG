
from pathlib import Path

import pandas as pd
# --- User-defined variables ---


### FIRST QUERY

# MAIN_QUERY = """
# ("collision" OR "allision" OR "accident" OR "safety" OR "risk assessment" OR "risk analysis") AND
# ("Offshore infrastructure" OR "Offshore construction"
# 	OR "Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF"
# 	OR "Offshore platform" OR "Oil platform" OR "Hydrogen platforms"
# 	OR "Offshore quay" OR "Offshore wharf"
# 	OR "Artificial Island" OR "Synthetic Island"
# 	OR "Bridge"
# 	OR "Flotel"
# 	OR "Aquaculture Farms"
# 	OR "Offshore Lidar"
# 	OR "Storm surge barrier" OR  "Flood Barrier"
# ) AND
# ("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
# ("maritime" OR  "navigational" OR "nautical")
# """

### SECOND QUERY

# MAIN_QUERY = """
# ("risk assessment" OR "risk analysis") AND
# ("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
# ("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
# ("maritime" OR  "navigational" OR "nautical")
# """
### THIRD QUERY

MAIN_QUERY = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("maritime" OR "navigational" OR "nautical")
"""

### FOURTH QUERY

# MAIN_QUERY = """
# ("ship collision" OR "ship-object collision" OR "allision" OR "maritime accident" OR "ship encounter" OR "safety" OR "risk assessments" OR "risk analysis" OR "risk model" OR "hazards") AND
# ("Offshore windfarms" OR "Offshore wind farms" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
# ("maritime" OR  "navigational" OR "nautical" OR "marine" OR "shipping")
# """


### FIFTH QUERY


# MAIN_QUERY = """
# ("ship collision" OR "ship-object collision" OR "allision" OR "maritime accident" OR "ship encounter" OR "safety" OR "risk assessments" OR "risk analysis" OR "risk model" OR "hazards") AND
# ("Offshore windfarms" OR "Offshore wind farms" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF" OR "Offshore wind energy" OR "Offshore infrastructure" OR "Offshore construction" OR "Offshore installation" OR "offshore marine platforms") AND
# ("maritime" OR  "navigational" OR "nautical" OR "marine" OR "shipping")
# """


### SIXTH QUERY


# MAIN_QUERY = """
# ("collision" OR "allision") AND
# ("Offshore infrastructure" OR "Offshore construction" OR "Offshore installation" OR "Offshore windfarm" OR "Offshore windfarms" OR "Offshore wind farm" OR "Offshore wind farms" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF" OR "Offshore platform" OR "Oil platform" OR "Hydrogen platforms" OR "Bridge" OR "offshore marine platform") AND
# ("maritime" OR "navigational" OR "nautical" OR "marine" OR "shipping" OR "vessel" OR "ship")
# """

### 7th QUERY

# MAIN_QUERY = """
# Navigational Risk Assessment
# """

SCOPUS_QUERY = f"""
TITLE-ABS-KEY( {MAIN_QUERY})
"""

OPENALEX_QUERY = MAIN_QUERY
MINIMUM_YEAR_NAME = "minimum_year"
ADDITIONAL_PARAMETERS = {
    MINIMUM_YEAR_NAME : 2010 # Comment this line if no date filtering
}
# TITLE, DOI, IN_SCOPUS, IN_OPENALEX, IN_LENS,
REFERENCE_PAPERS = [
    (
        "A dynamic risk assessment method to address safety of navigation concerns around offshore renewable energy installations",
        "10.1177/1475090219837409",
        True, True, True, True
    ),
    (
        "A Marine GIS-based Alert System to Prevent Vessels Collision with Offshore Platforms",
        "10.51400/2709-6998.2462",
        True, True, True, True
    ),
    (
        "A method for risk analysis of ship collisions with stationary infrastructure using AIS data and a ship manoeuvring simulator",
        "10.1016/j.oceaneng.2021.109396",
        True, True, True, True
    ),
    (
        "A Novel Method for Navigational Risk Assessment in Wind Farm Waters Based on the Fuzzy Inference System",
        "10.1155/2021/4588333",
        True, True, False, True
    ),
    (
        "A study on influence of Putian Port offshore wind farm construction on navigation safety",
        "",
        False, True, False, False
    ),
    (
        "A System-Theory and Complex Network-Fused Approach to Analyze Vessel–Wind Turbine Allisions in Offshore Wind Farm Waters",
        "10.3390/jmse11071306",
        True, True, True, True
    ),
    (
        "Allision risk analysis of offshore petroleum installations on the Norwegian Continental Shelf—an empirical study of vessel traffic patterns",
        "10.1007/s13437-016-0123-7",
        True, True, True, True
    ),
    (
        "Assessing the impacts to vessel traffic from offshore wind farms in the Thames Estuary",
        "",
        False, True, True, False
    ),
    (
        "Assessing the validity of navigation risk assessments; A study of offshore wind farms in the UK",
        "10.1016/j.ocecoaman.2022.106078",
        True, True, False, True
    ),
    (
        "Evaluation of Ship Importance in Offshore Wind Farm Area Based on Fusion Gravity Model in Complex Network",
        "10.3390/su17188252",
        True, True, True, True
    ),
    (
        "Improving the coexistence of offshore wind farms and shipping; an international comparison of navigational risk assessment processes",
        "10.1007/s13437-018-0149-0",
        True, True, True, True
    ),
    (
        "Likelihood of a marine vessel accident from wind energy development in the Atlantic",
        "10.1002/we.1935",
        True, True, True, True
    ),
    (
        "Multi-Perspective Nautical Safety Risk Assessment of Allisions with Offshore Wind Parks",
        "10.2139/ssrn.5002935",
        True, True, False, False
    ),
    (
        "Navigational Risk Assessment in Offshore Wind Farms Using Spatial Ship Domain Models",
        "10.3390/app15126943",
        True, True, False, False
    ),
    (
        "Navigational Safety Hazards Posed by Offshore Wind Farms: A Comprehensive Literature Review and Bibliometric Analysis.",
        "10.3390/jmse13071330",
        True, True, True, True
    ),
    (
        "Probabilistic approach for collision risk analysis of powered vessel with offshore platforms",
        "10.1016/j.oceaneng.2018.01.008",
        True, True, True, True
    ),
    (
        "Realising advanced risk assessment of vessel traffic flows near offshore wind farms",
        "10.1016/j.ress.2020.107086",
        True, True, True, True
    ),
    (
        "Research on the Impact of Deep Sea Offshore Wind Farms on Maritime Safety",
        "10.3390/jmse13040699",
        True, True, True, True
    ),
    (
        "Review of Probabilistic Risk Assessment Models for Ship Collisions with Structures",
        "10.3390/app12073441",
        True, True, True, True
    ),
    (
        "The Impact of Offshore Wind Farm Construction on Maritime Traffic Complexity; An Empirical Analysis of the Yangtze River Estuary",
        "10.3390/jmse12122232",
        True, True, True, True
    ),
        (
        "Risk Assessment of Collision Between Out of Control Vessels and Offshore Platforms",
        "10.1109/ICTIS68762.2025.11214868",
        True, True, True, True
    )
]


REFERENCE_DOIS = [paper[1] for paper in REFERENCE_PAPERS]


QUESTIONS = [
    "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or Vessels. OR"
    "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms.",
    "This paper includes a quantitative model.",
]

AUTOMATICALLY_OVERWRITE = False

PATH_INPUT = Path("data/export_databases/")
PATH_LENS_EXPORT = PATH_INPUT / "lens-export.csv"
PATH_DIMENSIONS_EXPORT = PATH_INPUT / "dimensions-export.csv"

OUTPUT_PATH = Path("outputs/")
OUTPUT_CSV_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_DOI_RESULTS = OUTPUT_PATH / "papers_selected.csv"
OUTPUT_UPSET = OUTPUT_PATH / "upset.html"


SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50
LIST_NAME_DATABASE = ["scopus", "openalex"]
DEFAULT_DF_COLUMNS = ["doi", "title", "date", "abstract"]
DEFAULT_DF_COLUMNS_LENS = DEFAULT_DF_COLUMNS + ["id_lens"]
DEFAULT_DF_COLUMNS_DIMENSIONS = DEFAULT_DF_COLUMNS + ["id_dimensions"]
