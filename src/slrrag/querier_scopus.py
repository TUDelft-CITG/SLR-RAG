import pandas as pd
from pandera.typing import DataFrame
import pybliometrics
from pybliometrics.scopus import ScopusSearch

from slrrag.settings import (
    DEFAULT_DF_COLUMNS,
    NAME_COL_RELEVANCE_ORDER_SCOPUS,
    PANDERA_LAZY_VALIDATION,
    SCOPUS_IS_SUBSCRIBER,
    PATH_PYBLIOMETRICS_CONFIG,
    SchemaPapers,
    SchemaScopusPapers,
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


def to_query_scopus(query: str):
    """Query Scopus and return results."""
    scopus_query = f"""
TITLE-ABS-KEY( {query})
"""
    return scopus_query


def query_scopus(query: str, dry_run = False) -> DataFrame[SchemaPapers] | None:
    scopus_query = to_query_scopus(query)
    print("Scopus Query :", scopus_query)
    try:
        pybliometrics.init(config_path=PATH_PYBLIOMETRICS_CONFIG)  # Init for scopus
        nb_paper = ScopusSearch(
            query=scopus_query, download=False, subscriber=SCOPUS_IS_SUBSCRIBER
        ).get_results_size()
        print(f"{nb_paper} found in Scopus.")
        if dry_run:
            print("Dry run activated, exiting without downloading")
            return None
        scopus_search = ScopusSearch(
            query=scopus_query,
            verbose=True,
            subscriber=SCOPUS_IS_SUBSCRIBER,
            refresh=True,
            sort="-relevance",
        )
        return scopus_to_dict_list(scopus_search)
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
            "keywords_scopus": paper.authkeywords,
        }
        for paper in results.results
    ]

    return_df = pd.DataFrame(data)
    return_df[NAME_COL_RELEVANCE_ORDER_SCOPUS] = return_df.index
    return SchemaScopusPapers.validate(return_df, lazy=PANDERA_LAZY_VALIDATION)
