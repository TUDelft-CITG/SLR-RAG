import pandas as pd
from pandera.typing import DataFrame
import pybliometrics
from pybliometrics.scopus import ScopusSearch

from slrrag.settings import (
    DEFAULT_DF_COLUMNS,
    PANDERA_LAZY_VALIDATION,
    SCOPUS_IS_SUBSCRIBER,
    THRESHOLD_BIG_COUNT_PAPER,
    SchemaPapers,
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


def query_scopus(query: str) -> DataFrame[SchemaPapers] | None:
    """Query Scopus and return results."""
    scopus_query = f"""
TITLE-ABS-KEY( {query})
"""
    print("Query :", scopus_query)
    try:
        pybliometrics.init()  # Init for scopus
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


def scopus_to_dict_list(results: ScopusSearch) -> DataFrame[SchemaPapers]:
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
            "keywords_scopus" : paper.authkeywords
        }
        for paper in results.results
    ]

    return_df = pd.DataFrame(data)
    return SchemaPapers.validate(return_df,lazy=PANDERA_LAZY_VALIDATION)
