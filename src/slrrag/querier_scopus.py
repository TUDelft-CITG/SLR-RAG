import pandas as pd
from pybliometrics.scopus import ScopusSearch

from slrrag.settings import (
    DEFAULT_DF_COLUMNS,
    SCOPUS_IS_SUBSCRIBER,
    THRESHOLD_BIG_COUNT_PAPER,
    LIST_TYPE_DOCUMENTS,
)
from slrrag.settings import (
    NAME_ARTICLE_TYPE_ARTICLE,
    NAME_ARTICLE_TYPE_BOOK,
    NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    NAME_ARTICLE_TYPE_PREPRINT,
    NAME_ARTICLE_TYPE_REPORT,
    NAME_COL_TYPE,
)


def check_doi_in_scopus(doi: str) -> bool:
    """Check if a DOI exists in Scopus."""
    try:
        from pybliometrics.scopus import ScopusSearch

        query = f'DOI("{doi}")'
        search = ScopusSearch(
            query=query, verbose=True, download=False, subscriber=SCOPUS_IS_SUBSCRIBER
        )
        return search.get_results_size() > 0
    except Exception as e:
        print(e)
        return False


# --- Scopus functions ---
def query_scopus(query: str) -> pd.DataFrame | None:
    """Query Scopus and return results."""
    scopus_query = f"""
TITLE-ABS-KEY( {query})
"""
    print("Query :", scopus_query)
    if LIST_TYPE_DOCUMENTS is not None and len(LIST_TYPE_DOCUMENTS) > 0:
        scopus_query + " AND DOCTYPE"
    try:
        nb_paper = ScopusSearch(
            query=scopus_query, download=False, subscriber=SCOPUS_IS_SUBSCRIBER
        ).get_results_size()
        if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
            if input(f"{nb_paper} found in Scopus. Continue? (y/n)").lower() == "y":
                scopus_search = ScopusSearch(
                    query=scopus_query, verbose=True, subscriber=SCOPUS_IS_SUBSCRIBER
                )
                return scopus_to_dict_list(scopus_search)
            else:
                return None
    except Exception as e:
        print(e, "\nReturning None")
        return None


def scopus_to_dict_list(results: ScopusSearch) -> pd.DataFrame:
    """Convert Scopus results to a pandas DataFrame."""
    if results.results is None:
        return pd.DataFrame(columns=DEFAULT_DF_COLUMNS + ["id_scopus"])
    data = [
        {
            "doi": paper.doi,
            "title": paper.title,
            "date": paper.coverDate,
            "abstract": paper.description,
            "id_scopus": paper.eid,
            "type": paper.subtypeDescription,
        }
        for paper in results.results
    ]

    return_df = pd.DataFrame(data)
    conversion_type_article_scopus = {
        "Book Chapter": NAME_ARTICLE_TYPE_BOOK_CHAPTER,
        "Article": NAME_ARTICLE_TYPE_ARTICLE,
        "Preprint": NAME_ARTICLE_TYPE_PREPRINT,
        "Book": NAME_ARTICLE_TYPE_BOOK,
        "Report": NAME_ARTICLE_TYPE_REPORT,
        "Conference Paper": NAME_ARTICLE_TYPE_ARTICLE,
        "Short Survey": NAME_ARTICLE_TYPE_ARTICLE,
        "Review": NAME_ARTICLE_TYPE_ARTICLE,
        "Conference Review": NAME_ARTICLE_TYPE_ARTICLE,
    }
    return_df["date"] = pd.to_datetime(return_df["date"], format="mixed")
    return_df = return_df.replace({NAME_COL_TYPE: conversion_type_article_scopus})
    return return_df
