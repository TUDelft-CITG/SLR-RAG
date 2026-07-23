import os

from dotenv import load_dotenv
import pandas as pd
from pandera.typing import DataFrame
from pyalex import Works
import pyalex
from tqdm import tqdm

from slrrag.settings import (
    DEFAULT_OPEN_ALEX_PAGING,
    NAME_COL_KEYWORDS_OPENALEX,
    NAME_COL_PRIMARY_DOMAIN_OPENALEX,
    NAME_COL_PRIMARY_FIELD_OPENALEX,
    NAME_COL_PRIMARY_SUBFIELD_OPENALEX,
    NAME_COL_PRIMARY_TOPIC_OPENALEX,
    NAME_COL_RELEVANCE_OPENALEX,
    PANDERA_LAZY_VALIDATION,
    PROJECT_ROOT,
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

def load_openalex_api_key():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    pyalex.config.api_key = os.environ.get("OPENALEX_API_KEY")
    if pyalex.config.api_key is None:
        print(f"Warning: OPENALEX_API_KEY in {PROJECT_ROOT / ".env"} has not been loaded.\n Please write OPENALEX_API_KEY=<you api key> in the file.")

def get_openalex_work_from_query(query: str):
    load_openalex_api_key()
    return Works().search_filter(title_and_abstract=query)


def work_openalex_to_list(works: Works):
    nb_papers_openalex = works.count()
    print(f"{nb_papers_openalex} found in Openalex.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in tqdm(pager, total=nb_papers_openalex / DEFAULT_OPEN_ALEX_PAGING):
        list_ret += page
    return list_ret

def parse_openalex_list_to_dataframe(list_openalex_papers: list)  -> DataFrame[SchemaOpenAlexPapers]:
    input_openalex_columns_name = [
        "doi",
        "id",
        "title",
        "publication_date",
        "abstract",
        "type",
        "relevance_score",
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
        if (paper["primary_topic"] is not None) and ("field" in paper["primary_topic"]):
            return paper["primary_topic"]["field"]["display_name"]
        else:
            return None

    def get_primary_subfield(paper):
        if (paper["primary_topic"] is not None) and (
            "subfield" in paper["primary_topic"]
        ):
            return paper["primary_topic"]["subfield"]["display_name"]
        else:
            return None

    def get_primary_domain(paper):
        if (paper["primary_topic"] is not None) and (
            "domain" in paper["primary_topic"]
        ):
            return paper["primary_topic"]["domain"]["display_name"]
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
            + [get_primary_subfield(x)]
            + [get_primary_domain(x)]
            + [get_keywords(x)]
            for x in list_openalex_papers
        ],
        columns=input_openalex_columns_name
        + [
            "pdf",
            NAME_COL_PRIMARY_TOPIC_OPENALEX,
            NAME_COL_PRIMARY_FIELD_OPENALEX,
            NAME_COL_PRIMARY_SUBFIELD_OPENALEX,
            NAME_COL_PRIMARY_DOMAIN_OPENALEX,
            NAME_COL_KEYWORDS_OPENALEX,
        ],
    )
    return_df = return_df.rename(
        columns={
            "publication_date": NAME_COL_DATE,
            "id": "id_openalex",
            "relevance_score": NAME_COL_RELEVANCE_OPENALEX,
        }
    )
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return SchemaOpenAlexPapers.validate(return_df, lazy=PANDERA_LAZY_VALIDATION)


# --- OpenAlex functions ---
def query_openalex(query: str) -> DataFrame[SchemaOpenAlexPapers]:
    """Query OpenAlex and return results as a pandas DataFrame."""
    print("Query :", query)
    works = get_openalex_work_from_query(query)
    
    list_ret = work_openalex_to_list(works)
    return parse_openalex_list_to_dataframe(list_ret)
    