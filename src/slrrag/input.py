from slrrag.settings import (
    ARTICLE_N,
    BOOK_CHAPTER_N,
    BOOK_N,
    CONFERENCE_PAPER_N,
    CONFERENCE_PROCEEDING_N,
)

MAIN_QUERY = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
"""

MINIMUM_YEAR_NAME = "minimum_year"
LIST_TYPE_TO_KEEP_NAME = "type_paper_to_keep"

ADDITIONAL_PARAMETERS = {
    MINIMUM_YEAR_NAME: 2010,  # Comment this line if no date filtering
    LIST_TYPE_TO_KEEP_NAME: [  # Comment a line if you do not want to include a specific type of paper, or all of them if no type filtering
        ARTICLE_N,
        CONFERENCE_PAPER_N,
        BOOK_CHAPTER_N,
        BOOK_N,
        CONFERENCE_PROCEEDING_N,
    ],
}

# TITLE, DOI
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
        "A Novel Method for Navigational Risk Assessment in Wind Farm Waters Based on the Fuzzy Inference System",
        "10.1155/2021/4588333",
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
        "The Impact of Offshore Wind Farm Construction on Maritime Traffic Complexity: An Empirical Analysis of the Yangtze River Estuary",
        "10.3390/jmse12122232",
    ),
    (
        "Risk Assessment of Collision Between Out of Control Vessels and Offshore Platforms",
        "10.1109/ICTIS68762.2025.11214868",
    ),
]

MAIN_QUESTION = """
We consider the following subjects part of risks for maritime traffic :
- Collisions/allisions probabilities
- Alert system when detecting risky situation
- Detection of anlomalous trajectories
- Risk or safety index/score calculation
- Frequency of collisions/allisions
- Safety distance estimations
- Explanation and or analysis of collisions using models.
- Maritime traffic analysis for martime safety.
- Marine spatial planning and pressure on maritime traffic ana

But we are not interested in:
- Ecological impact (collision between birds and OWF)
- impact on structural bridges/platforms when collisions. (mainly damage analysis).
- Structural or design analysis of bridges of offshore infrastructures.
- Cybersecurity
- Risk assessment during maintnance operation.
- Predicting inboard problems.
- Diverse other risk of accidents related to offshore platforms or bridges (e.g : oil spill, crash during operations, ice)
- Risk assessment when installing/decommisionning offshore infrastructures. (Impact of weather, ground...)
- Collision/Risk linked to the bridge of ships. (studying human factors)
- Other safety assessment of bridges (e.g heavy load)
- Other risky threats (tsunami, anchor damages to infrastructures)
- Safe manoeuver in ports or other areas.
- Terrorist attack on infrastructures.
- Ship/platforms/bridges evacuation in case of risks.

Is the subject of the paper is about risks for maritime traffic, as explained above, around offshore infrastructures (e.g windfarms, platforms...) and/or bridges?
"""
FIRST_ROUND_QUESTIONS = [
    # {"name": "risk_nautical", "question": "Does this paper discuss about risk assessment or risk analysis in the context of nautical safety for ships or vessels?"},
    # {"name": "nautical_offshore", "question": "Is this paper about nautical safety around offshore infrastructures, like offshore windfarms?"},
    # {"name": "probability_collision", "question": "Does this paper include a method to estimate the probability or risk of collision or allision of ships?"},
    # {"name": "quantitative_model", "question": "Does this paper include a quantitative model?"},
    # {"name": "technique_risk_collision", "question": "Does this paper present a technique to assess the risk of collision or allisions between ships and other human-made objects around offshore infrastructures or bridges?"},
    # {"name": "recommendation_safety", "question": "Does this paper gives recommendation for safe navigation around offshore infrastructures or bridges?"},
    {"name": "main_question", "question": MAIN_QUESTION},
]


SECOND_ROUND_QUESTIONS = {
    "strategic": [
        {
            "name": "frequency",
            "question": "This paper estimates the frequency / return periods of collisions of ships with another object in a certain area.",
        },
        {
            "name": "long-term",
            "question": "This paper assesses the risk in a long-term context with static data.",
        },
    ],
    "tactical": [
        {
            "name": "traffic-accidents",
            "question": "This paper study the traffic in general, in order to minimize the risks of a accidents, such as by reducing the complexity or congestion of the traffic.",
        },
        {
            "name": "traffic-dynamic",
            "question": "This paper studies the entire traffic by using dynamic data.",
        },
    ],
    "operational": [
        {
            "name": "short-term",
            "question": "This paper present a methodology to assess the risk of a accidents that can come in short-term (usually in terms of hours).",
        },
        {
            "name": "limited-number-agents",
            "question": "The paper uses only a limited amount of agents (ships) to estimate the risks of accidents.",
        },
    ],
    "quantitative": [
        {
            "name": "quantitative-model",
            "question": "This paper includes a quantitative model to calculate the likehood of the risks in a mathematical way. (such as probability, risk index, frequency, or return period.",
        },
        {
            "name": "empirical-data",
            "question": "This paper relies on empirical data to estimate the risks",
        },
    ],
    "qualitative": [
        {
            "name": "expert-judgment",
            "question": "This paper makes use of experts judgements to estimate the risks.",
        },
        {
            "name": "visualisation",
            "question": "This paper only makes conclusion of the risks by visualizing the traffic, without calculating the risk in a mathematical way (like probability or frequency).",
        },
    ],
}

OLLAMA_MODELS = [
    "granite4.1:3b",
    "ministral-3:3b",
    "llama3.2:3b",
]
