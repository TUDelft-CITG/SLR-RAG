import pandas as pd
from pandera.typing import DataFrame
from pyalex import Works
from tqdm import tqdm

from slrrag.settings import (
    DEFAULT_OPEN_ALEX_PAGING,
    NAME_COL_TOPIC_OPENALEX,
    THRESHOLD_BIG_COUNT_PAPER,
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


# --- OpenAlex functions ---
def query_openalex(query: str) -> DataFrame[SchemaPapers]:
    """Query OpenAlex and return results as a pandas DataFrame."""
    print("Query :", query)
    works = Works().search_filter(title_and_abstract=query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != "y":
            return None
    print(f"{nb_paper} found in OpenAlex. Downloading.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in tqdm(pager, total=nb_paper/DEFAULT_OPEN_ALEX_PAGING):
        list_ret += page
    input_openalex_columns_name = [
        "doi",
        "id",
        "title",
        "publication_date",
        "abstract",
        "type",
    ]
    # Due to legal reasons, we have to extract the abstract manually : https://pypi.org/project/pyalex/#get-abstract:~:text=Get%20abstract
    # TODO : we get the pdf url, but we must setup a API key to download them.
    def get_topic(paper):
        if (paper["primary_topic"] is not None) and ("display_name" in paper["primary_topic"]):
            return paper["primary_topic"]["display_name"]
        else:
            return None
    return_df = pd.DataFrame(
        [
            [x[col_name] for col_name in input_openalex_columns_name] + [x.pdf.url] +[ get_topic(x)]
            for x in list_ret
        ],
        columns=input_openalex_columns_name + ["pdf"] + [NAME_COL_TOPIC_OPENALEX],
    )
    return_df = return_df.rename(
        columns={"publication_date": NAME_COL_DATE, "id": "id_openalex"}
    )
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return SchemaPapers.validate(return_df)
