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

# MAIN_QUERY = """
# ("risk assessment" OR "risk analysis") AND
# ("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
# ("maritime" OR "navigational" OR "nautical")
# """

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
# ("collision" OR "allision" OR "accident" OR "ship encounter" OR "safety" OR "hazards" OR "risk") AND
# ("Offshore infrastructure" OR "Offshore construction" OR "Offshore installation" OR "Offshore windfarm" OR "Offshore windfarms" OR "Offshore wind farm" OR "Offshore wind farms" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF" OR "Offshore platform" OR "Oil platform" OR "Hydrogen platforms" OR "Bridge" OR "offshore marine platform") AND
# ("maritime" OR "navigational" OR "nautical" OR "marine" OR "shipping" OR "vessel" OR "ship")
# """

### 8th QUERY

# MAIN_QUERY = """
# ("Navigational Risk assessment" OR "Navigation Risk assessment")
# """

### 9th QUERY

# MAIN_QUERY = """
# ("offshore") AND ("infrastructure" OR "construction" OR "installation" OR "windfarm" OR "windfarms" OR "wind farm" OR "wind farms" OR "windmill" OR "wind turbine" OR "wind park" OR "wind energy") AND
# (("Navigation risk assessment" OR "Navigational risk assessment") OR
# (("collision" OR "allision") AND ("ship" OR "vessel") AND ("Probabily" OR "likelihood" OR "model")) OR
# ("risk" AND ("assess" OR "model" OR "predict") AND ("ship" OR "vessel" OR "maritime traffic")))
# """

### 10th QUERY

# MAIN_QUERY = """
# ("offshore") AND ("infrastructure*" OR "construction*" OR "installation*" OR "windfarm*" OR "wind farm*" OR "windmill*" OR "wind turbine*" OR "wind park*" OR "wind energy") AND
# (("Navigation risk assessment*" OR "Navigational risk assessment*") OR
# (("collision*" OR "allision*") AND ("ship*" OR "vessel*") AND ("probabi*" OR "likelihood*" OR "model*")) OR
# ("risk*" AND ("assess*" OR "model*" OR "predict*" OR "analy*") AND ("ship*" OR "vessel*" OR "maritime traffic*" OR "navigation*")))
# """


### 11th QUERY

# MAIN_QUERY = """
# ("offshore") AND ("infrastructure*" OR "construction*" OR "installation*" OR "windfarm*" OR "wind farm*" OR "windmill*" OR "wind turbine*" OR "wind park*" OR "wind energy") AND
# (("Navigation risk assessment*" OR "Navigational risk assessment*") OR
# (("collision*" OR "allision*") AND ("ship*" OR "vessel*") AND ("probabi*" OR "likelihood*" OR "model*")) OR
# (("risk*" OR "safety") AND ("assess*" OR "model*" OR "predict*" OR "analy*" OR "study" OR "studies") AND ("ship*" OR "vessel*" OR "maritime traffic*" OR "navigation*")))
# """

### 12th QUERY

MAIN_QUERY = """
((("offshore") AND ("infrastructure" OR "construction" OR "installation" OR "windfarm" OR "wind farm" OR "windmill" OR "wind turbine" OR "wind park" OR "wind energy" OR "platform" OR "quay" OR "wharf" OR "lidar")) OR ("bridge" OR "flotel" OR "Aquaculture farm" OR "Artificial Island" OR "Synthetic Island")) AND
(("Navigation risk assessment" OR "Navigational risk assessment" OR "Navigation risk assessments" OR "Navigational risk assessments") OR
(("collision" OR "allision") AND ("ship" OR "vessel") AND ("probability" OR "probabilistic" OR "likelihood" OR "chance")) OR
(("risk" OR "safe" OR "safety") AND ("assess" OR "assessing" OR "assessment" OR "model" OR "modeling" OR "modelisation" OR "predict" OR "predicting" OR "prediction" OR "analyse" OR "analysing" OR "analyze" OR "analyzing" OR "study" OR "studies" OR "studying") AND ("ship" OR "vessel" OR "maritime traffic" OR "navigation" OR "navigational" OR "nautical")))
"""

MINIMUM_YEAR_NAME = "minimum_year"
ADDITIONAL_PARAMETERS = {
    MINIMUM_YEAR_NAME: 2010  # Comment this line if no date filtering
}
# TITLE, DOI, IN_SCOPUS, IN_OPENALEX, IN_LENS, IN_DIMENSIONS
REFERENCE_PAPERS = [
    (
        "A dynamic risk assessment method to address safety of navigation concerns around offshore renewable energy installations",
        "10.1177/1475090219837409",
    ),
    (
        "A Marine GIS-based Alert System to Prevent Vessels Collision with Offshore Platforms",
        "10.51400/2709-6998.2462",
    ),
    (
        "A method for risk analysis of ship collisions with stationary infrastructure using AIS data and a ship manoeuvring simulator",
        "10.1016/j.oceaneng.2021.109396",
    ),
    (
        "A Novel Method for Navigational Risk Assessment in Wind Farm Waters Based on the Fuzzy Inference System",
        "10.1155/2021/4588333",
    ),
    (
        "A study on influence of Putian Port offshore wind farm construction on navigation safety",
        None,
    ),
    (
        "A System-Theory and Complex Network-Fused Approach to Analyze Vessel–Wind Turbine Allisions in Offshore Wind Farm Waters",
        "10.3390/jmse11071306",
    ),
    (
        "Allision risk analysis of offshore petroleum installations on the Norwegian Continental Shelf—an empirical study of vessel traffic patterns",
        "10.1007/s13437-016-0123-7",
    ),
    (
        "Assessing the impacts to vessel traffic from offshore wind farms in the Thames Estuary",
        None,
    ),
    (
        "Assessing the validity of navigation risk assessments; A study of offshore wind farms in the UK",
        "10.1016/j.ocecoaman.2022.106078",
    ),
    (
        "Evaluation of Ship Importance in Offshore Wind Farm Area Based on Fusion Gravity Model in Complex Network",
        "10.3390/su17188252",
    ),
    (
        "Improving the coexistence of offshore wind farms and shipping; an international comparison of navigational risk assessment processes",
        "10.1007/s13437-018-0149-0",
    ),
    (
        "Likelihood of a marine vessel accident from wind energy development in the Atlantic",
        "10.1002/we.1935",
    ),
    (
        "Multi-Perspective Nautical Safety Risk Assessment of Allisions with Offshore Wind Parks",
        "10.1016/j.apor.2025.104564",
    ),
    (
        "Navigational Risk Assessment in Offshore Wind Farms Using Spatial Ship Domain Models",
        "10.3390/app15126943",
    ),
    (
        "Navigational Safety Hazards Posed by Offshore Wind Farms: A Comprehensive Literature Review and Bibliometric Analysis.",
        "10.3390/jmse13071330",
    ),
    (
        "Probabilistic approach for collision risk analysis of powered vessel with offshore platforms",
        "10.1016/j.oceaneng.2018.01.008",
    ),
    (
        "Realising advanced risk assessment of vessel traffic flows near offshore wind farms",
        "10.1016/j.ress.2020.107086",
    ),
    (
        "Research on the Impact of Deep Sea Offshore Wind Farms on Maritime Safety",
        "10.3390/jmse13040699",
    ),
    (
        "Review of Probabilistic Risk Assessment Models for Ship Collisions with Structures",
        "10.3390/app12073441",
    ),
    (
        "The Impact of Offshore Wind Farm Construction on Maritime Traffic Complexity; An Empirical Analysis of the Yangtze River Estuary",
        "10.3390/jmse12122232",
    ),
    (
        "Risk Assessment of Collision Between Out of Control Vessels and Offshore Platforms",
        "10.1109/ICTIS68762.2025.11214868",
    ),
]


FIRST_ROUND_QUESTIONS = [
    "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or vessels.",
    "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms.",
    "This paper talks about a method to estimate the probability or risk of collision or allision of ships.",
    "This paper includes a quantitative model.",
]


# TODO : make global name (ASK an LLM)
SECOND_ROUND_QUESTIONS = {
    "strategic": {
        "frequency": "This paper estimates the frequency / return periods of collisions of ships with another object in a certain area.",
        "long-term": "This paper assesses the risk in a long-term context with static data.",
    },
    "tactical": {
        "traffic-accidents": "This paper study the traffic in general, in order to minimize the risks of a accidents, such as by reducing the complexity or congestion of the traffic.",
        "traffic-dynamic": "This paper studies the entire traffic by using dynamic data.",
    },
    "operational": {
        "short-term": "This paper present a methodology to assess the risk of a accidents that can come in short-term (usually in terms of hours).",
        "limited-number-agents": "The paper uses only a limited amount of agents (ships) to estimate the risks of accidents.",
    },
    "quantitative": {
        "quantitative-model": "This paper includes a quantitative model to calculate the likehood of the risks in a mathematical way. (such as probability, risk index, frequency, or return period.",
        "empirical-data": "This paper relies on empirical data to estimate the risks",
    },
    "qualitative": {
        "expert-judgment": "This paper makes use of experts judgements to estimate the risks.",
        "visualisation": "This paper only makes conclusion of the risks by visualizing the traffic, without calculating the risk in a mathematical way (like probability or frequency).",
    },
    "": {},
}

OLLAMA_MODELS = ["qwen3.5:0.8b"]
