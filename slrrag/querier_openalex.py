import pandas as pd
from pyalex import Works

from settings import DEFAULT_OPEN_ALEX_PAGING, THRESHOLD_BIG_COUNT_PAPER
from settings import (
    NAME_ARTICLE_TYPE_ARTICLE,
    NAME_ARTICLE_TYPE_BOOK,
    NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    NAME_ARTICLE_TYPE_DISSERTATION,
    NAME_ARTICLE_TYPE_PREPRINT,
    NAME_ARTICLE_TYPE_REPORT,
    NAME_COL_DATE,
    NAME_COL_TYPE,
)


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
    for page in pager:
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
    return_df = pd.DataFrame(
        [
            [x[col_name] for col_name in input_openalex_columns_name] + [x.pdf.url]
            for x in list_ret
        ],
        columns=input_openalex_columns_name + ["pdf"],
    )
    return_df = return_df.rename(
        columns={"publication_date": NAME_COL_DATE, "id": "id_openalex"}
    )
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return_df["date"] = pd.to_datetime(return_df["date"], format="mixed")
    conversion_type_article_openalex = {
        "book-chapter": NAME_ARTICLE_TYPE_BOOK_CHAPTER,
        "journal-article": NAME_ARTICLE_TYPE_ARTICLE,
        "preprint": NAME_ARTICLE_TYPE_PREPRINT,
        "book": NAME_ARTICLE_TYPE_BOOK,
        "dissertation": NAME_ARTICLE_TYPE_DISSERTATION,
        "report": NAME_ARTICLE_TYPE_REPORT,
    }
    return_df = return_df.replace({NAME_COL_TYPE: conversion_type_article_openalex})
    return return_df
