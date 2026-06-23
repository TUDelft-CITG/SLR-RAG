import pandas as pd
import pybliometrics

from slrrag.querier_scopus import check_doi_in_scopus
from slrrag.querier_openalex import check_doi_in_openalex


def check_dois_in_databases(dois: list[str]) -> pd.DataFrame:
    """Check which DOIs exist in Scopus and OpenAlex.

    Args:
        dois: List of DOI strings to check

    Returns:
        DataFrame with columns: doi, in_db_scopus, in_db_openalex
    """
    results = []
    for doi in dois:
        in_scopus = check_doi_in_scopus(doi)
        in_openalex = check_doi_in_openalex(doi)
        results.append(
            {
                "doi": doi,
                "in_db_scopus": in_scopus,
                "in_db_openalex": in_openalex,
            }
        )
    return pd.DataFrame(results)


if __name__ == "__main__":
    pybliometrics.init()

    list_doi = [
        "10.1016/j.oceaneng.2020.108259",
        "10.1007/s13437-016-0123-7",
        "10.1016/j.ocecoaman.2022.106078",
        "10.1002/we.1935",
        "10.3390/jmse13071330",
        "10.1016/j.ress.2020.107086",
        "10.3390/app12073441",
    ]
    print(check_dois_in_databases(list_doi))
