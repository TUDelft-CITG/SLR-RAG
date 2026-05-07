
import pandas as pd
from pyalex import Works

from settings import DEFAULT_OPEN_ALEX_PAGING, THRESHOLD_BIG_COUNT_PAPER


def check_doi_in_openalex(doi: str) -> bool:
    """Check if a DOI exists in OpenAlex."""
    try:
        works = Works().filter_or(doi=doi)
        return works.count() > 0
    except Exception:
        return False

# --- OpenAlex functions ---
def query_openalex(query: str) -> pd.DataFrame:
    """Query OpenAlex and return results as a pandas DataFrame."""

    works = Works().search_filter(title_and_abstract=query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != "y": 
            None
    print(f"{nb_paper} found in OpenAlex. Downloading.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in pager:
        list_ret += page
    input_openalex_columns_name = ["doi", "id", "title", "publication_date", "abstract"]
    # Due to legal reasons, we have to extract the abstract manually : https://pypi.org/project/pyalex/#get-abstract:~:text=Get%20abstract
    return_df = pd.DataFrame(
        [[x[col_name] for col_name in input_openalex_columns_name] for x in list_ret],
        columns=input_openalex_columns_name,
    )
    return_df = return_df.rename(
        columns={"publication_date": "date", "id": "id_openalex"}
    )
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return return_df

