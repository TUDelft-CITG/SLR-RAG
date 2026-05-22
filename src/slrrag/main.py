import os
from pathlib import Path
from typing import List
from pandera.typing.pandas import DataFrame
import pandera.pandas as pa
import pandas as pd
import pybliometrics
from slrrag.querier_openalex import query_openalex
from slrrag.querier_scopus import query_scopus
from slrrag.query_converter import convert_query_to_lens
from slrrag.query_converter import query_to_dimensions_url
from slrrag.ollama_analysis import (
    setup_chat_agent,
    analyze_papers_with_agent,
)
from slrrag.querier_dimensions import read_dimensions_export
from slrrag.querier_lens import read_lens_export
from slrrag.input import (
    ADDITIONAL_PARAMETERS,
    MAIN_QUERY,
    MINIMUM_YEAR_NAME,
    FIRST_ROUND_QUESTIONS,
)
from slrrag.settings import (
    AUTOMATICALLY_OVERWRITE,
    DEFAULT_DF_COLUMNS,
    NAME_COL_IS_FOUND,
    NAME_COL_PRESENT_DIMENSIONS,
    NAME_COL_PRESENT_LENS,
    NAME_COL_PRESENT_OPENALEX,
    NAME_COL_PRESENT_SCOPUS,
    NAME_COL_YEAR,
    OUTPUT_CSV_AGENTS_PATH,
    OUTPUT_CSV_QUERY_RESULTS,
    OUTPUT_PATH,
    OUTPUT_UPSET,
    PATH_DIMENSIONS_EXPORT,
    PATH_LENS_EXPORT,
    REFERENCE_DOIS,
    REFERENCE_PAPERS,
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

from slrrag.upset_plotter import plot_and_save_upset

def get_new_reference_df() -> DataFrame[SchemaPapers]:
    df_ret = pd.DataFrame(
        REFERENCE_PAPERS,
        columns=[
            NAME_COL_TITLE,
            NAME_COL_DOI,
            NAME_COL_PRESENT_SCOPUS,
            NAME_COL_PRESENT_OPENALEX,
            NAME_COL_PRESENT_LENS,
            NAME_COL_PRESENT_DIMENSIONS,
        ]
    )
    df_ret[NAME_COL_IS_REFERENCE] = True
    df_ret[NAME_COL_IS_FOUND] = False
    #df_ret[[NAME_COL_DATE,NAME_COL_TYPE,NAME_COL_YEAR,NAME_COL_ABSTRACT]] = pd.NA
    return SchemaPapers.validate(df_ret)


@pa.check_types
def add_scopus_papers(
    input_papers: DataFrame[SchemaPapers], database_names: List[str]
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    print("---- Getting query on Scopus ---")
    results_scopus = query_scopus(MAIN_QUERY)
    if results_scopus is not None:
        results_scopus=  SchemaPapers.validate(results_scopus)
        input_papers: DataFrame[SchemaPapers] = merge_papers(
            input_papers, results_scopus, "scopus"
        )
        database_names += ["scopus"]
    return input_papers, database_names


@pa.check_types
def add_openalex_papers(
    input_papers: DataFrame[SchemaPapers], database_names: List[str]
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    results_openalex = query_openalex(MAIN_QUERY)
    if results_openalex is not None:
        results_openalex=  SchemaPapers.validate(results_openalex)
        input_papers: DataFrame[SchemaPapers] = merge_papers(
            input_papers, results_openalex, "openalex"
        )
        database_names += ["openalex"]
    return input_papers, database_names


@pa.check_types
def add_dimensions_papers(
    merged_papers: DataFrame[SchemaPapers], database_names: List[str]
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    """Add Dimensions.ai papers to the merged DataFrame.

    This function guides the user through the process of adding Dimensions papers:
    1. Converts MAIN_QUERY to Dimensions URL
    2. Instructs user to execute the query on dimensions.ai and export results
    3. Optionally reads the export and merges the papers

    Args:
        merged_papers: Current merged DataFrame of papers
        database_names: List of database names already included

    Returns:
        Tuple of (updated merged_papers, updated database_names)
    """
    # Convert MAIN_QUERY to dimensions URL
    dimensions_url = query_to_dimensions_url(MAIN_QUERY)
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
                dimensions_df = SchemaPapers.validate(read_dimensions_export(PATH_DIMENSIONS_EXPORT))
                print(f"Found {len(dimensions_df)} papers in Dimensions export")
                print("---- Merging with Dimensions ---")
                merged_papers = merge_papers(merged_papers, dimensions_df, "dimensions")
                database_names.append("dimensions")
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


@pa.check_types
def add_lens_papers(
    merged_papers: DataFrame[SchemaPapers], database_names: List[str]
) -> tuple[DataFrame[SchemaPapers], List[str]]:
    """Add Lens papers to the merged DataFrame.

    This function guides the user through the process of adding Lens papers:
    1. Converts MAIN_QUERY to Lens query format
    2. Saves the query to a file
    3. Instructs user to execute the query on lens.org and export results
    4. Optionally reads the export and merges the papers

    Args:
        merged_papers: Current merged DataFrame of papers
        database_names: List of database names already included

    Returns:
        Tuple of (updated merged_papers, updated database_names)
    """
    # Convert MAIN_QUERY to lens format
    lens_query = convert_query_to_lens(MAIN_QUERY)
    print("\nLens query:")
    print(lens_query)

    # Save to file
    query_lens_path = OUTPUT_PATH / "query_lens.txt"
    os.makedirs(OUTPUT_PATH, exist_ok=True)
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
                merged_papers = merge_papers(merged_papers, lens_df, "lens")
                database_names.append("lens")
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
@pa.check_types
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
    # Sometimes, doi / title do not have same uppercase : 10.1017/S0373463319000444 == 10.1017/s0373463319000444.
    left_df["temp_key"] = (
        left_df[NAME_COL_DOI].fillna(left_df[NAME_COL_TITLE]).str.lower()
    )
    right_df["temp_key"] = (
        right_df[NAME_COL_DOI].fillna(right_df[NAME_COL_TITLE]).str.lower()
    )

    # Rename right_df's id column to id_{right_db}
    right_id_col = f"id_{right_db_name}"
    # Collect all id columns from left_df (may already have id_{db} from previous merges)
    left_id_cols = [col for col in left_df.columns if col.startswith("id")]
    all_id_cols = left_id_cols + [right_id_col]

    # Merge by temp_key
    merged_df = pd.merge(
        left_df,
        right_df,
        on=["temp_key"],
        how="outer",
        suffixes=("", f"_{right_db_name}"),
    )
    # BUG: Will have duplicata if one has doi and not the other

    # Combine fields - prefer left database
    merged_df[NAME_COL_DOI] = merged_df[NAME_COL_DOI].fillna(
        merged_df.get(f"{NAME_COL_DOI}_{right_db_name}", None)
    )
    merged_df[NAME_COL_TITLE] = merged_df[NAME_COL_TITLE].fillna(
        merged_df.get(f"{NAME_COL_TITLE}_{right_db_name}", None)
    )
    merged_df[NAME_COL_DATE] = merged_df[NAME_COL_DATE].fillna(
        merged_df.get(f"{NAME_COL_DATE}_{right_db_name}", None)
    )

    merged_df[NAME_COL_ABSTRACT] = merged_df[NAME_COL_ABSTRACT].fillna(
        merged_df.get(f"{NAME_COL_ABSTRACT}_{right_db_name}", None)
    )
    merged_df[NAME_COL_TYPE] = merged_df[NAME_COL_TYPE].fillna(
        merged_df.get(f"{NAME_COL_TYPE}_{right_db_name}", None)
    )

    # Select columns to keep: core fields + all id columns that exist
    result_cols = DEFAULT_DF_COLUMNS + [
        col for col in all_id_cols if col in merged_df.columns
    ]
    result_df = merged_df[result_cols].copy()
    # Check if papers are reference or not
    reference_paper = get_new_reference_df()
    # DOI Matches or title matches
    result_df[NAME_COL_IS_REFERENCE] = (
        result_df[NAME_COL_DOI].notna()
        & result_df[NAME_COL_DOI].isin(reference_paper[NAME_COL_DOI])
    ) | result_df[NAME_COL_TITLE].isin(reference_paper[NAME_COL_TITLE])
    return result_df


@pa.check_types
def add_reference_papers(
    df: DataFrame[SchemaPapers], reference_dois: List[str]
) -> DataFrame[SchemaPapers]:
    """Add reference papers to DataFrame if they don't already exist.

    For each DOI in reference_dois that's not in the DataFrame's doi column,
    adds a new row with that DOI and None for all other columns.

    Args:
        df: DataFrame with paper data (must have 'doi' column)
        reference_dois: List of reference DOIs to ensure are present

    Returns:
        DataFrame with reference papers added
    """
    # Find reference DOIs not already in the DataFrame
    existing_dois = set(df[NAME_COL_DOI].dropna().unique())
    missing_dois = [doi for doi in reference_dois if doi not in existing_dois]

    if not missing_dois:
        return df

    # Create new rows for missing reference papers
    # Get the expected columns from the DataFrame
    new_rows = []
    for doi in missing_dois:
        row = {NAME_COL_DOI: doi}
        # Set all other columns to None
        for col in df.columns:
            if col != NAME_COL_DOI:
                row[col] = None
        new_rows.append(row)

    # Append new rows to DataFrame
    new_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    new_df[NAME_COL_IS_REFERENCE] = new_df[NAME_COL_DOI].isin(REFERENCE_DOIS)
    return new_df


@pa.check_types
def clean_merged_df(merged_papers: DataFrame[SchemaPapers], database_names: List[str]):
    """
    Make the clean of the datafram before further processing, and apply filters
    setup in ADDITIONAL_PARAMETERS
    """
    print("---------CLEANING------------")
    assert len(database_names) > 0, "List of database is empty. Please use at least one Database."
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
    if MINIMUM_YEAR_NAME in ADDITIONAL_PARAMETERS:
        df_after = merged_papers[
            merged_papers["year"].isna()
            | (merged_papers["year"] >= ADDITIONAL_PARAMETERS[MINIMUM_YEAR_NAME])
        ]
        assert (
            df_after[NAME_COL_IS_REFERENCE].sum()
            == merged_papers[NAME_COL_IS_REFERENCE].sum()
        )
        print(
            f"Filtering {len(merged_papers) - len(df_after)} papers that are before year {ADDITIONAL_PARAMETERS[MINIMUM_YEAR_NAME]}"
        )
        merged_papers = df_after
    return merged_papers


@pa.check_types
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


# --- File I/O functions ---
def check_overwrite(
    file_path: Path, automatically_overwrite: bool = AUTOMATICALLY_OVERWRITE
) -> bool:
    if file_path.exists() and not automatically_overwrite:
        user_input = input(
            f"File {file_path} already exists. Overwrite? (y/n): "
        ).lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return False
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    return True


@pa.check_types
def save_dataframe_to_csv(df: DataFrame[SchemaPapers], file_path: Path) -> None:
    """Save DataFrame to CSV with overwrite protection."""
    os.makedirs(file_path.parent, exist_ok=True)
    if check_overwrite(file_path, AUTOMATICALLY_OVERWRITE):
        df.to_csv(file_path, index=False, date_format="%Y-%m-%d")
        print(f"Results saved in {file_path}")


def prompt_user_for_action_before_querying() -> str:
    """Prompt the user for action: continue, print papers, or exit."""
    while True:
        user_input = input(
            f"Choose an option:\n  's' to query the databases\n  'i' to import fron {OUTPUT_CSV_AGENTS_PATH}\n> "
        ).lower()
        if user_input in ["s", "i"]:
            return user_input
        print("Invalid option. Please try again.")


def prompt_user_for_action_after_querying() -> str:
    """Prompt the user for action: continue, print papers, or exit."""
    while True:
        user_input = input(
            f"Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'r' to see references papers \n  'e' to exit\n  's' to save to '{OUTPUT_CSV_QUERY_RESULTS}'\n  'u' to plot upset plot at '{OUTPUT_UPSET}'\n> "
        ).lower()
        if user_input in ["c", "p", "e", "s", "u", "r"]:
            return user_input
        print("Invalid option. Please try again.")


@pa.check_types
def get_all_papers_from_databases() -> tuple[DataFrame[SchemaPapers], List[str]]:
    pybliometrics.init()  # Init for scopus
    papers_df = get_new_reference_df()
    database_names = []
    # Step 1: Query Scopus

    papers_df, database_names = add_scopus_papers(papers_df, database_names)

    # Step 2: Query OpenAlex
    papers_df, database_names = add_openalex_papers(papers_df, database_names)

    # Step 3: Merge papers from Scopus and OpenAlex
    print("---- Merging papers ---")

    # Step 3b: Ask if user wants to add lens.database
    user_input = input("Search for Lens papers? (y/n): ").lower()
    if user_input == "y":
        papers_df, database_names = add_lens_papers(papers_df, database_names)

    # Step 3c: Ask if user wants to add dimensions.ai papers
    user_input = input("Search for Dimensions.ai papers? (y/n): ").lower()
    if user_input == "y":
        papers_df, database_names = add_dimensions_papers(papers_df, database_names)

    # Add reference papers in the final dataframe.
    papers_df = clean_merged_df(papers_df, database_names)
    return papers_df, database_names


# --- Main workflow ---
def main():
    if prompt_user_for_action_before_querying() == "s":
        papers_df, database_names = get_all_papers_from_databases()
    else:
        papers_df = SchemaPapers(pd.read_csv(OUTPUT_CSV_QUERY_RESULTS))

        database_names = [
            c.removeprefix("id_") for c in papers_df.columns if c.startswith("id_")
        ]
        papers_df = clean_merged_df(papers_df, database_names)
    print(f"Databases used : [{database_names}]")
    papers_df = show_merged_stats(papers_df, database_names)

    # Step 4: User interaction
    while True:
        action = prompt_user_for_action_after_querying()
        if action == "e":  # exit
            return
        elif action == "p":  # print names
            print(
                papers_df[
                    [NAME_COL_TITLE, NAME_COL_DOI, NAME_COL_IS_REFERENCE, "is_found"]
                ]
            )
        elif action == "s":  # Save merged papers as CSV
            save_dataframe_to_csv(papers_df, OUTPUT_CSV_QUERY_RESULTS)
        elif action == "u":
            if check_overwrite(OUTPUT_UPSET, AUTOMATICALLY_OVERWRITE):
                plot_and_save_upset(papers_df, OUTPUT_UPSET)
                print(f"Upset plot saved to {OUTPUT_UPSET}")
        elif action == "c":  # continue
            os.makedirs(OUTPUT_CSV_AGENTS_PATH.parent, exist_ok=True)
            break
        elif action == "r":
            print(
                papers_df.query(NAME_COL_IS_REFERENCE)[
                    [NAME_COL_TITLE, NAME_COL_DOI, NAME_COL_IS_REFERENCE, "is_found"]
                ]
            )

    # Check if file exists and prompt user for overwrite
    if OUTPUT_CSV_AGENTS_PATH.exists() and not AUTOMATICALLY_OVERWRITE:
        user_input = input(
            f"File {OUTPUT_CSV_AGENTS_PATH} already exists. Overwrite? (y/n): "
        ).lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return
    # Step 5: Initialize agent and process papers
    print("Creating a chat with ollama")
    agent = setup_chat_agent()

    print("Analyzing papers with agent")
    results_df = analyze_papers_with_agent(agent, papers_df, FIRST_ROUND_QUESTIONS)

    print(f"Saving results to {OUTPUT_CSV_AGENTS_PATH}")
    save_dataframe_to_csv(results_df, OUTPUT_CSV_AGENTS_PATH)

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_AGENTS_PATH}")


if __name__ == "__main__":
    main()
