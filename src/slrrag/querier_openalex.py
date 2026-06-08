import pandas as pd
from pandera.typing import DataFrame
from pyalex import Works
from tqdm import tqdm

from slrrag.settings import (
    DEFAULT_OPEN_ALEX_PAGING,
    NAME_COL_KEYWORDS_OPENALEX,
    NAME_COL_PRIMARY_FIELD_OPENALEX,
    NAME_COL_PRIMARY_TOPIC_OPENALEX,
    NAME_COL_RELEVANCE_OPENALEX,
    PANDERA_LAZY_VALIDATION,
    THRESHOLD_BIG_COUNT_PAPER,
    SchemaOpenAlexPapers,
    SchemaPapers,
)
from slrrag.settings import (
    NAME_COL_DATE,
)


def check_doi_in_openalex(doi: str) -> bool:
    """Check if a DOI exists in OpenAlex."""
    try:
        works = Works().filter_or(doi=doi)
        return works.count() > 0
    except Exception:
        return False

def query_openalex(query: str, ask_input=True, n_paper_max=None):
    works = Works().search_filter(title_and_abstract=query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER and ask_input:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != "y":
            return None
    print(f"{nb_paper} found in OpenAlex. Downloading.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in tqdm(pager, total=nb_paper / DEFAULT_OPEN_ALEX_PAGING):
        list_ret += page
        if n_paper_max and len(list_ret) > n_paper_max:
            break
    return list_ret
# --- OpenAlex functions ---
def query_openalex_and_standardize(
    query: str, ask_input=True, n_paper_max=None
) -> DataFrame[SchemaPapers]:
    """Query OpenAlex and return results as a pandas DataFrame."""
    print("Query :", query)
    list_ret = query_openalex(query,ask_input,n_paper_max)
    input_openalex_columns_name = [
        "doi",
        "id",
        "title",
        "publication_date",
        "abstract",
        "type",
        "relevance_score"
    ]

    # Due to legal reasons, we have to extract the abstract manually : https://pypi.org/project/pyalex/#get-abstract:~:text=Get%20abstract
    # TODO : we get the pdf url, but we must setup a API key to download them.
    # TODO : OpenAlex has much more then just the "primary_topic" -> we can use more of this.
    # Notably the subfields
    # See more : https://developers.openalex.org/api-reference/introduction
    def get_primary_topic(paper):
        if (paper["primary_topic"] is not None) and (
            "display_name" in paper["primary_topic"]
        ):
            return paper["primary_topic"]["display_name"]
        else:
            return None

    def get_primary_field(paper):
        if (paper["primary_topic"] is not None) and (
            "display_name" in paper["primary_topic"]
        ):
            return paper["primary_topic"]["field"]["display_name"]
        else:
            return None

    def get_keywords(paper):
        if paper["keywords"] is not None:
            return "|".join(
                [x.get("display_name") for x in paper["keywords"]]
            )  # Get all keywords in one string , separated by "|"
        else:
            return None

    return_df = pd.DataFrame(
        [
            [x[col_name] for col_name in input_openalex_columns_name]
            + [x.pdf.url]
            + [get_primary_topic(x)]
            + [get_primary_field(x)]
            + [get_keywords(x)]
            for x in list_ret
        ],
        columns=input_openalex_columns_name
        + [
            "pdf",
            NAME_COL_PRIMARY_TOPIC_OPENALEX,
            NAME_COL_PRIMARY_FIELD_OPENALEX,
            NAME_COL_KEYWORDS_OPENALEX,
        ],
    )
    return_df = return_df.rename(
        columns={"publication_date": NAME_COL_DATE, "id": "id_openalex", "relevance_score" : NAME_COL_RELEVANCE_OPENALEX}
    )
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return SchemaOpenAlexPapers.validate(return_df, lazy=PANDERA_LAZY_VALIDATION)
