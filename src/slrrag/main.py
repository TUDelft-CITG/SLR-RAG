import os
from pathlib import Path
from typing import List
from pandera.typing.pandas import DataFrame
import pandera.pandas as pa
import pandas as pd
from slrrag.querier_openalex import query_openalex
from slrrag.querier_scopus import query_scopus
from slrrag.query_converter import convert_query_to_lens
from slrrag.query_converter import query_to_dimensions_url
from slrrag.ollama_analysis import (
    analyze_papers_with_agent,
)
from slrrag.querier_dimensions import read_dimensions_export
from slrrag.querier_lens import read_lens_export
from slrrag.input import (
    ADDITIONAL_PARAMETERS,
    LIST_TYPE_TO_KEEP_NAME,
    MAIN_QUERY,
    MINIMUM_YEAR_NAME,
    FIRST_ROUND_QUESTIONS,
    OLLAMA_MODELS,
    REFERENCE_PAPERS,
)
from slrrag.settings import (
    AUTOMATICALLY_OVERWRITE,
    NAME_COL_YEAR,
    PATH_CSV_03_AGENTS_ANWSERS,
    PATH_CSV_01_QUERY_RESULTS,
    PATH_CSV_SCOPUS_QUERY_RESULTS,
    PATH_CSV_OPENALEX_QUERY_RESULTS,
    PATH_OUTPUT,
    PATH_UPSET,
    PANDERA_LAZY_VALIDATION,
    PATH_DIMENSIONS_EXPORT,
    PATH_LENS_EXPORT,
)
from slrrag.settings import (
    NAME_COL_ABSTRACT,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_TYPE,
    NAME_COL_IS_REFERENCE,
)
from slrrag.settings import SchemaPapers

from slrrag.toolbox.files import check_overwrite, save_dataframe_to_csv
from slrrag.upset_plotter import plot_and_save_upset


def get_new_reference_df() -> DataFrame[SchemaPapers]:
    df_ret = pd.DataFrame(
        REFERENCE_PAPERS,
        columns=[
            NAME_COL_TITLE,
            NAME_COL_DOI,
        ],
    )
    return SchemaPapers.validate(df_ret, lazy=PANDERA_LAZY_VALIDATION)


def load_or_query_database(
    db_name: str, csv_path: Path, query_func, query_input: str
) -> DataFrame[SchemaPapers] | None:
    """Helper function to load database results from CSV or query the database.

    Args:
        db_name: Name of the database (for display purposes)
        csv_path: Path to the CSV file for caching results
        query_func: Function to call to query the database

    Returns:
        DataFrame with results or None if no results
    """

    # Query the database
    print(f"---- Getting query on {db_name} ---")
    results = query_func(query_input)
    if results is not None:
        results = SchemaPapers.validate(results, lazy=PANDERA_LAZY_VALIDATION)
        # Save results to CSV
        save_dataframe_to_csv(results, csv_path)
    return results


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def add_scopus_papers(
    input_papers: DataFrame[SchemaPapers], database_names: List[str], query_input: str
) -> tuple[DataFrame[SchemaPapers], List[str]]:

    results_scopus = load_or_query_database(
        "Scopus", PATH_CSV_SCOPUS_QUERY_RESULTS, query_scopus, query_input
    )
    if results_scopus is not None:
        input_papers, database_names = merge_papers(
            input_papers, results_scopus, database_names, "scopus"
        )
    return input_papers, database_names


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def add_openalex_papers(
    input_papers: DataFrame[SchemaPapers], database_names: List[str], query_input: str
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    results_openalex = load_or_query_database(
        "OpenAlex", PATH_CSV_OPENALEX_QUERY_RESULTS, query_openalex, query_input
    )
    if results_openalex is not None:
        input_papers, database_names = merge_papers(
            input_papers, results_openalex, database_names, "openalex"
        )
    return input_papers, database_names


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def add_dimensions_papers(
    merged_papers: DataFrame[SchemaPapers], database_names: List[str], query_input: str
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    """Add Dimensions.ai papers to the merged DataFrame.

    This function guides the user through the process of adding Dimensions papers:
    1. Converts query_input to Dimensions URL
    2. Instructs user to execute the query on dimensions.ai and export results
    3. Optionally reads the export and merges the papers

    Args:
        merged_papers: Current merged DataFrame of papers
        database_names: List of database names already included

    Returns:
        Tuple of (updated merged_papers, updated database_names)
    """
    dimensions_url = query_to_dimensions_url(query_input)
    print("\nDimensions.ai URL:")
    print(dimensions_url)

    # Instruct user
    print("\nPlease go to the URL above on Dimensions.ai")
    print("Export the results as CSV and save to:")
    print(f"{PATH_DIMENSIONS_EXPORT}")

    # Ask user what to do next
    PATH_DIMENSIONS_EXPORT.parent.mkdir(exist_ok=True, parents=True)
    while True:
        user_choice = input("Add Dimensions papers? (y/n):").strip()
        if user_choice == "y":
            if PATH_DIMENSIONS_EXPORT.exists():
                print("---- Reading Dimensions export ---")
                dimensions_df = SchemaPapers.validate(
                    read_dimensions_export(PATH_DIMENSIONS_EXPORT)
                )
                print(f"Found {len(dimensions_df)} papers in Dimensions export")
                print("---- Merging with Dimensions ---")
                merged_papers, database_names = merge_papers(
                    merged_papers, dimensions_df, database_names, "dimensions"
                )
                break
            else:
                print(
                    f"File {PATH_DIMENSIONS_EXPORT} does not exist. Dimensions papers not added."
                )
                continue
        elif user_choice == "n":
            print("Dimensions inclusion cancelled.")
            break
        else:
            print("Invalid choice. Please enter y or n.")

    return merged_papers, database_names


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def add_lens_papers(
    merged_papers: DataFrame[SchemaPapers], database_names: List[str], query_input: str
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    """Add Lens papers to the merged DataFrame.

    This function guides the user through the process of adding Lens papers:
    1. Converts query_input to Lens query format
    2. Saves the query to a file
    3. Instructs user to execute the query on lens.org and export results
    4. Optionally reads the export and merges the papers

    Args:
        merged_papers: Current merged DataFrame of papers
        database_names: List of database names already included

    Returns:
        Tuple of (updated merged_papers, updated database_names)
    """
    lens_query = convert_query_to_lens(query_input)
    print("\nLens query:")
    print(lens_query)

    # Save to file
    query_lens_path = PATH_OUTPUT / "query_lens.txt"
    os.makedirs(PATH_OUTPUT, exist_ok=True)
    with open(query_lens_path, "w") as f:
        f.write(lens_query + "\n")
    print(f"\nQuery saved to {query_lens_path}")

    # Instruct user
    print("\nPlease copy the query above and paste it into the query editor at:")
    print("https://www.lens.org/lens/search/scholar/structured")
    print("Export the results as CSV and save to:")
    print(f"{PATH_LENS_EXPORT}")

    # Ask user what to do next
    PATH_LENS_EXPORT.parent.mkdir(exist_ok=True, parents=True)
    while True:
        user_choice = input("Add Lens papers? (y/n):").strip()
        if user_choice == "y":
            if PATH_LENS_EXPORT.exists():
                print("---- Reading Lens export ---")
                lens_df = SchemaPapers.validate(read_lens_export(PATH_LENS_EXPORT))
                print(f"Found {len(lens_df)} papers in Lens export")
                print("---- Merging with Lens ---")
                merged_papers, database_names = merge_papers(
                    merged_papers, lens_df, database_names, "lens"
                )

                break
            else:
                print(f"File {PATH_LENS_EXPORT} does not exist. Lens papers not added.")
                continue
        elif user_choice == "n":
            print("Lens inclusion cancelled.")
            break
        else:
            print("Invalid choice. Please enter y or n.")

    return merged_papers, database_names


# --- Merge and stats functions ---
@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def merge_papers(
    left_df: DataFrame[SchemaPapers],
    right_df: DataFrame[SchemaPapers],
    right_db_name: str,
) -> DataFrame[SchemaPapers]:
    """Merge two paper DataFrames by DOI/title, keeping only specified fields.

    Args:
        left_df: Left DataFrame to merge (can already contain id_{db} columns)
        right_df: Right DataFrame to merge
        left_db: Name of left database (e.g., 'scopus')
        right_db: Name of right database (e.g., 'openalex')

    Returns:
        Merged DataFrame with columns: doi, title, date, abstract, plus all id_{db} columns
    """
    # Temporary Key is the DOI, Title if the DOI is None.
    # Sometimes, doi / title do not have same uppercase : 10.1017/S0373463319000444 == 10.1017/s0373463319000444.
    # BUG: Will have duplicata if one has doi and not the other
    left_df["temp_key"] = (
        left_df[NAME_COL_DOI].fillna(left_df[NAME_COL_TITLE]).str.lower()
    )
    right_df["temp_key"] = (
        right_df[NAME_COL_DOI].fillna(right_df[NAME_COL_TITLE]).str.lower()
    )

    # Merge by temp_key
    merged_df = pd.merge(
        left_df,
        right_df,
        on=["temp_key"],
        how="outer",
        suffixes=("", f"_{right_db_name}"),
    )
    merged_df = merged_df.drop(columns=["temp_key"])
    columns_to_combine = [
        NAME_COL_DOI,
        NAME_COL_TITLE,
        NAME_COL_DATE,
        NAME_COL_ABSTRACT,
        NAME_COL_TYPE,
        NAME_COL_YEAR,
    ]
    # Combine fields - prefer left database
    for col in columns_to_combine:
        merged_df[col] = merged_df[col].fillna(
            merged_df.get(f"{col}_{right_db_name}", None)
        )
        # Remove useless column
        merged_df = merged_df.drop(columns=f"{col}_{right_db_name}")

    return merged_df


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def clean_merged_df(merged_papers: DataFrame[SchemaPapers], database_names: List[str]):
    """
    Make the clean of the datafram before further processing, and apply filters
    setup in ADDITIONAL_PARAMETERS
    """
    print("---------CLEANING------------")
    assert len(database_names) > 0, (
        "List of database is empty. Please use at least one Database."
    )
    for db in database_names:
        merged_papers[f"in_{db}"] = merged_papers[f"id_{db}"].notna()
    merged_papers["is_found"] = pd.concat(
        [merged_papers[f"in_{db}"] for db in database_names], axis=1
    ).any(axis=1)
    merged_papers["year"] = pd.to_datetime(
        merged_papers[NAME_COL_DATE], format="mixed"
    ).dt.year
    merged_papers["year"] = merged_papers["year"].astype(
        "Int64"
    )  # To avoid having floats
    reference_paper = get_new_reference_df()
    # DOI Matches or title matches
    merged_papers[NAME_COL_IS_REFERENCE] = (
        merged_papers[NAME_COL_DOI].notna()
        & merged_papers[NAME_COL_DOI].isin(reference_paper[NAME_COL_DOI])  # SAME DOI
    ) | (
        merged_papers[NAME_COL_TITLE].isin(reference_paper[NAME_COL_TITLE])
        & merged_papers[NAME_COL_DOI].isna()  # Same title if DOI is None.
    )
    if MINIMUM_YEAR_NAME in ADDITIONAL_PARAMETERS:
        df_after = merged_papers[
            merged_papers["year"].isna()
            | (merged_papers["year"] >= ADDITIONAL_PARAMETERS[MINIMUM_YEAR_NAME])
        ].copy()

        print(
            f"Filtering {len(merged_papers) - len(df_after)} papers that are before year {ADDITIONAL_PARAMETERS[MINIMUM_YEAR_NAME]}"
        )
        assert (
            df_after[NAME_COL_IS_REFERENCE].sum()
            == merged_papers[NAME_COL_IS_REFERENCE].sum()
        ), f"""one or more reference papers are before {ADDITIONAL_PARAMETERS[MINIMUM_YEAR_NAME]}.
              f{merged_papers[merged_papers["is_reference"] & ~merged_papers.index.isin(df_after.index)][[NAME_COL_TITLE, NAME_COL_DATE]]}\n
              Make sure to decrease the year or to remove these reference paper"""  # Make sure that a reference paper is not removed by the filtering
        merged_papers = df_after
    if LIST_TYPE_TO_KEEP_NAME in ADDITIONAL_PARAMETERS:
        df_after = merged_papers[
            merged_papers[NAME_COL_TYPE].isin(
                ADDITIONAL_PARAMETERS[LIST_TYPE_TO_KEEP_NAME] + [None, pd.NA]
            )
        ].copy()
        print(
            f"Filtering {len(merged_papers) - len(df_after)} papers that are not{ADDITIONAL_PARAMETERS[LIST_TYPE_TO_KEEP_NAME]}"
        )
        assert (
            df_after[NAME_COL_IS_REFERENCE].sum()
            == merged_papers[NAME_COL_IS_REFERENCE].sum()
        ), f"""one or more reference papers type are not in {ADDITIONAL_PARAMETERS[LIST_TYPE_TO_KEEP_NAME]}.
            {merged_papers[merged_papers["is_reference"] & ~merged_papers.index.isin(df_after.index)][[NAME_COL_TITLE, NAME_COL_TYPE]]}"""  # Make sure that a reference paper is not removed by the filtering
        merged_papers = df_after
    return merged_papers


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def show_merged_stats(
    merged_papers: DataFrame[SchemaPapers], database_names: List[str]
) -> None:
    """Print statistics about merged papers.

    Args:
        merged_papers: DataFrame with merged paper data
        reference_dois: List of reference DOIs
        database_names: List of database names (e.g., ['scopus', 'openalex'])
    """
    print("---------SUMMARIZING------------")

    reference_df = merged_papers[merged_papers[NAME_COL_IS_REFERENCE]]

    # Calculate common papers (in all databases)
    common_papers = (
        pd.concat([merged_papers[f"in_{db}"] for db in database_names], axis=1)
        .all(axis=1)
        .sum()
    )
    # Calculate papers appearing in at least one database
    found_papers = merged_papers["is_found"].sum()
    reference_found = (
        pd.concat([reference_df[f"in_{db}"] for db in database_names], axis=1)
        .any(axis=1)
        .sum()
    )
    total_reference = len(reference_df)

    print(f"Total number of papers found: {found_papers}")
    print(f"Reference papers found: {reference_found} over {total_reference}")
    print(f"Number of common papers in all databases: {common_papers}")

    # Print stats for each database
    for db in database_names:
        ref_in_db = (
            merged_papers[f"in_{db}"] & merged_papers[NAME_COL_IS_REFERENCE]
        ).sum()
        in_db = merged_papers[f"in_{db}"].sum()
        print(f"Number of papers in {db}: {in_db}")
        print(f"Number of reference papers in {db}: {ref_in_db}")
    return merged_papers


def prompt_user_for_action_before_querying() -> str:
    """Prompt the user for action: continue, print papers, or exit."""
    while True:
        user_input = input(
            f"Choose an option:\n  's' to query the databases\n  'i' to import fron {PATH_CSV_03_AGENTS_ANWSERS}\n> "
        ).lower()
        if user_input in ["s", "i"]:
            return user_input
        print("Invalid option. Please try again.")


def prompt_user_for_action_after_querying() -> str:
    """Prompt the user for action: continue, print papers, or exit."""
    while True:
        user_input = input(
            f"Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'r' to see references papers \n  'e' to exit\n  's' to save to '{PATH_CSV_01_QUERY_RESULTS}'\n  'u' to plot upset plot at '{PATH_UPSET}'\n> "
        ).lower()
        if user_input in ["c", "p", "e", "s", "u", "r"]:
            return user_input
        print("Invalid option. Please try again.")


def handle_user_actions_after_querying(
    papers_df: DataFrame[SchemaPapers],
) -> bool:
    """Handle user actions after querying databases.

    Returns:
        True if user wants to continue to the next step.
        False if user wants to exit.
    """
    while True:
        action = prompt_user_for_action_after_querying()
        if action == "e":  # exit
            return False
        elif action == "p":  # print names
            print(
                papers_df[
                    [NAME_COL_TITLE, NAME_COL_DOI, NAME_COL_IS_REFERENCE, "is_found"]
                ]
            )
        elif action == "s":  # Save merged papers as CSV
            save_dataframe_to_csv(papers_df, PATH_CSV_01_QUERY_RESULTS)
        elif action == "u":
            if check_overwrite(PATH_UPSET, AUTOMATICALLY_OVERWRITE):
                plot_and_save_upset(papers_df, PATH_UPSET)
                print(f"Upset plot saved to {PATH_UPSET}")
        elif action == "c":  # continue
            os.makedirs(PATH_CSV_03_AGENTS_ANWSERS.parent, exist_ok=True)
            return True
        elif action == "r":
            print(
                papers_df.query(NAME_COL_IS_REFERENCE)[
                    [NAME_COL_TITLE, NAME_COL_DOI, NAME_COL_IS_REFERENCE, "is_found"]
                ]
            )


def ask_user_binary(msg: str) -> bool:

    user_input = input(msg + "(y/n)").lower()
    if user_input == "y":
        return True
    elif user_input == "n":
        return False
    else:
        return ask_user_binary(msg)


def load_csv_results_if_exist_user_okay(csv_path: Path):
    if csv_path.exists():
        if ask_user_binary(f"Load from {csv_path}? (y/n): "):
            print(f"---- Loading from {csv_path.name} ---")
            return SchemaPapers.validate(
                pd.read_csv(csv_path), lazy=PANDERA_LAZY_VALIDATION
            )
    return None


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def interactive_get_all_papers_from_databases(
    query_input: str,
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    papers_df = get_new_reference_df()
    database_names = []
    # Step 1: Query Scopus
    if ask_user_binary("Search for Scopus paper?"):
        scopus_df = load_csv_results_if_exist_user_okay(PATH_CSV_SCOPUS_QUERY_RESULTS)
        if scopus_df is None:
            scopus_df = query_scopus(query_input)
            save_dataframe_to_csv(scopus_df, PATH_CSV_SCOPUS_QUERY_RESULTS)
        if scopus_df is None:
            print("scopus_df is None. Skipping Scoppus")
        else:
            papers_df, database_names = merge_papers(
                papers_df, scopus_df, database_names, "scopus"
            )

    # Step 2: Query OpenAlex
    if ask_user_binary("Search for Openalex papers?"):
        openalex_df = load_csv_results_if_exist_user_okay(
            PATH_CSV_OPENALEX_QUERY_RESULTS
        )
        if openalex_df is None:
            openalex_df = query_openalex(query_input)
            save_dataframe_to_csv(openalex_df, PATH_CSV_OPENALEX_QUERY_RESULTS)
        if openalex_df is None:
            print("openalex_df is None. Skipping OpenAlex")
        else:
            papers_df, database_names = merge_papers(
                papers_df, openalex_df, database_names, "openalex"
            )

    # Step 3: Merge papers from Scopus and OpenAlex
    print("---- Merging papers ---")

    # Step 3b: Ask if user wants to add lens.database
    if ask_user_binary("Search for Lens papers?"):
        papers_df, database_names = add_lens_papers(
            papers_df, database_names, query_input
        )

    # Step 3c: Ask if user wants to add dimensions.ai papers

    if ask_user_binary("Search for Dimensions papers?"):
        papers_df, database_names = add_dimensions_papers(
            papers_df, database_names, query_input
        )

    # Add reference papers in the final dataframe.
    return papers_df, database_names


# --- Main workflow ---
def main():
    if prompt_user_for_action_before_querying() == "s":
        papers_df, database_names = interactive_get_all_papers_from_databases(
            MAIN_QUERY
        )
    else:
        papers_df = SchemaPapers.validate(pd.read_csv(PATH_CSV_01_QUERY_RESULTS))

        database_names = [
            c.removeprefix("id_") for c in papers_df.columns if c.startswith("id_")
        ]
    papers_df = clean_merged_df(papers_df, database_names)
    print(f"Databases used : {database_names}")
    papers_df = show_merged_stats(papers_df, database_names)

    # Step 4: User interaction
    if not handle_user_actions_after_querying(papers_df):
        return

    # Check if file exists and prompt user for overwrite
    if PATH_CSV_03_AGENTS_ANWSERS.exists() and not AUTOMATICALLY_OVERWRITE:
        user_input = input(
            f"File {PATH_CSV_03_AGENTS_ANWSERS} already exists. Overwrite? (y/n): "
        ).lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return
    print(f"Analyzing papers with agent : {OLLAMA_MODELS}")
    results_df = analyze_papers_with_agent(
        OLLAMA_MODELS, papers_df, FIRST_ROUND_QUESTIONS
    )

    print(f"Saving results to {PATH_CSV_03_AGENTS_ANWSERS}")
    save_dataframe_to_csv(results_df, PATH_CSV_03_AGENTS_ANWSERS)

    print(f"Analysis complete. Results saved to {PATH_CSV_03_AGENTS_ANWSERS}")


if __name__ == "__main__":
    main()
