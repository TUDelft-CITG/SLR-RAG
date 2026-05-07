import os
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional

import pandas as pd
import pybliometrics
from pyalex import Works
from querier_openalex import check_doi_in_openalex, query_openalex
from querier_scopus import check_doi_in_scopus, query_scopus
from query_converter import convert_query_to_lens
from tqdm import tqdm
from query_converter import query_to_dimensions_url
from ollama_analysis import (
    setup_chat_agent,
    analyze_papers_with_agent,
)
from querier_dimensions import read_dimensions_export
from querier_lens import read_lens_export
from settings import AUTOMATICALLY_OVERWRITE, DEFAULT_DF_COLUMNS, MAIN_QUERY, OPENALEX_QUERY, OUTPUT_CSV_PATH, OUTPUT_DOI_RESULTS, OUTPUT_PATH, OUTPUT_UPSET, PATH_DIMENSIONS_EXPORT, PATH_LENS_EXPORT, QUESTIONS, REFERENCE_DOIS, REFERENCE_PAPERS, SCOPUS_QUERY
from upset_plotter import plot_and_save_upset
pybliometrics.init()


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
        results.append({
            "doi": doi,
            "in_db_scopus": in_scopus,
            "in_db_openalex": in_openalex,
        })
    return pd.DataFrame(results)


def add_scopus_papers(input_papers: pd.DataFrame, database_names: List[str]) -> tuple[pd.DataFrame, List[str]]:
    print("---- Getting query on Scopus ---")
    print("Query :", SCOPUS_QUERY)
    results_scopus = query_scopus(SCOPUS_QUERY)
    if results_scopus is not None:
        input_papers: pd.DataFrame = merge_papers(input_papers,results_scopus, "scopus")
        database_names += ["scopus"]
    return input_papers,database_names

def add_openalex_papers(input_papers: pd.DataFrame, database_names: List[str]) -> tuple[pd.DataFrame, List[str]]:
    print("Query :", OPENALEX_QUERY)
    results_openalex = query_openalex(OPENALEX_QUERY)
    if results_openalex is not None:
        input_papers: pd.DataFrame = merge_papers(input_papers,results_openalex, "openalex")
        database_names += ["openalex"]
    return input_papers,database_names


def add_dimensions_papers(
    merged_papers: pd.DataFrame, database_names: List[str]
) -> tuple[pd.DataFrame, List[str]]:
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
        user_choice = input(
            f"Add Dimensions papers? (y/n):"
        ).strip()
        if user_choice == "y":
            if PATH_DIMENSIONS_EXPORT.exists():
                print("---- Reading Dimensions export ---")
                dimensions_df = read_dimensions_export(PATH_DIMENSIONS_EXPORT)
                print(f"Found {len(dimensions_df)} papers in Dimensions export")
                print("---- Merging with Dimensions ---")
                merged_papers = merge_papers(merged_papers, dimensions_df, "dimensions")
                database_names.append("dimensions")
                break
            else:
                print(f"File {PATH_DIMENSIONS_EXPORT} does not exist. Dimensions papers not added.")
                continue
        elif user_choice == "n":
            print("Dimensions inclusion cancelled.")
            break
        else:
            print("Invalid choice. Please enter y or n.")

    return merged_papers, database_names



def add_lens_papers(
    merged_papers: pd.DataFrame, database_names: List[str]
) -> tuple[pd.DataFrame, List[str]]:
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
    PATH_LENS_EXPORT.parent.mkdir(exist_ok=True,parents=True)
    while True:
        user_choice = input(
            f"Add Lens papers? (y/n):"
        ).strip()
        if user_choice == "y":
            if PATH_LENS_EXPORT.exists():
                print("---- Reading Lens export ---")
                lens_df = read_lens_export(PATH_LENS_EXPORT)
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
def merge_papers(
    left_df: pd.DataFrame, right_df: pd.DataFrame, right_db_name: str
) -> pd.DataFrame:
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
    left_df["temp_key"] = left_df["doi"].fillna(left_df["title"]).str.lower()
    right_df["temp_key"] = right_df["doi"].fillna(right_df["title"]).str.lower()

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
        suffixes=(f"", f"_{right_db_name}"),
    )
    # BUG: Will have duplicata if one has doi and not the other

    # Combine fields - prefer left database
    merged_df["doi"] = merged_df[f"doi"].fillna(
        merged_df.get(f"doi_{right_db_name}", None)
    )
    merged_df["title"] = merged_df[f"title"].fillna(
        merged_df.get(f"title_{right_db_name}", None)
    )
    merged_df["date"] = merged_df[f"date"].fillna(
        merged_df.get(f"date_{right_db_name}", None)
    )
    merged_df["abstract"] = merged_df[f"abstract"].fillna(
        merged_df.get(f"abstract_{right_db_name}", None)
    )

    # Select columns to keep: core fields + all id columns that exist
    result_cols = DEFAULT_DF_COLUMNS + [
        col for col in all_id_cols if col in merged_df.columns
    ]
    result_df = merged_df[result_cols].copy()
    result_df["is_reference"] = result_df["doi"].isin(REFERENCE_DOIS)
    return result_df


def add_reference_papers(df: pd.DataFrame, reference_dois: List[str]) -> pd.DataFrame:
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
    existing_dois = set(df["doi"].dropna().unique())
    missing_dois = [doi for doi in reference_dois if doi not in existing_dois]

    if not missing_dois:
        return df

    # Create new rows for missing reference papers
    # Get the expected columns from the DataFrame
    new_rows = []
    for doi in missing_dois:
        row = {"doi": doi}
        # Set all other columns to None
        for col in df.columns:
            if col != "doi":
                row[col] = None
        new_rows.append(row)

    # Append new rows to DataFrame
    new_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    new_df["is_reference"] = new_df["doi"].isin(REFERENCE_DOIS)
    return new_df


def show_merged_stats(
    merged_papers: pd.DataFrame, reference_dois: List[str], database_names: List[str]
) -> None:
    """Print statistics about merged papers.

    Args:
        merged_papers: DataFrame with merged paper data
        reference_dois: List of reference DOIs
        database_names: List of database names (e.g., ['scopus', 'openalex'])
    """
    total_papers = len(merged_papers)

    # Create in_{db} columns for each database
    for db in database_names:
        merged_papers[f"in_{db}"] = merged_papers[f"id_{db}"].notna()

    # Calculate common papers (in all databases)
    common_papers = (
        pd.concat([merged_papers[f"in_{db}"] for db in database_names], axis=1)
        .all(axis=1)
        .sum()
    )
    # Calculate papers appearing in at least one database

    found_papers = (
        pd.concat([merged_papers[f"in_{db}"] for db in database_names], axis=1)
        .any(axis=1)
        .sum()
    )
    print(f"Total number of papers found: {found_papers}")
    print(
        f"Reference papers missing: {total_papers - found_papers} over {len(reference_dois)}"
    )
    print(f"Number of common papers in all databases: {common_papers}")

    # Print stats for each database
    for db in database_names:
        ref_in_db = (
            merged_papers[f"in_{db}"] & merged_papers["doi"].isin(reference_dois)
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


def save_dataframe_to_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Save DataFrame to CSV with overwrite protection."""
    os.makedirs(file_path.parent, exist_ok=True)
    if check_overwrite(file_path, AUTOMATICALLY_OVERWRITE):
        df.to_csv(file_path, index=False)
        print(f"Results saved in {file_path}")


def prompt_user_for_action() -> str:
    """Prompt the user for action: continue, print papers, or exit."""
    while True:
        user_input = input(
            f"Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'e' to exit\n  's' to save to '{OUTPUT_DOI_RESULTS}'\n  'u' to plot upset plot at '{OUTPUT_UPSET}'\n> "
        ).lower()
        if user_input in ["c", "p", "e", "s", "u"]:
            return user_input
        print("Invalid option. Please try again.")


# --- Main workflow ---
def main():
    papers_df = pd.DataFrame(REFERENCE_PAPERS, columns=["title", "doi", "present_openalex", "present_scopus", "present_lens", "present_dimensions"])
    database_names = []
    # Step 1: Query Scopus
    
    # assert SCOPUS_QUERY == OLD_SCOPUS_QUERY
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
    papers_df = add_reference_papers(papers_df, REFERENCE_DOIS)
    papers_df = show_merged_stats(papers_df, REFERENCE_DOIS, database_names)

    # Step 4: User interaction
    while True:
        action = prompt_user_for_action()
        if action == "e":  # exit
            return
        elif action == "p":  # print names
            for idx, (doi, paper) in enumerate(
                zip(papers_df["doi"], papers_df.to_dict("records")), 1
            ):
                if paper["title"] is not None:
                    print(
                        f"{idx}. {paper['title']} {'(Reference)' if doi in REFERENCE_DOIS else ''}"
                    )
        elif action == "s":  # Save merged papers as CSV
            save_dataframe_to_csv(papers_df, OUTPUT_DOI_RESULTS)
        elif action == "u":
            if check_overwrite(OUTPUT_UPSET, AUTOMATICALLY_OVERWRITE):
                plot_and_save_upset(papers_df, OUTPUT_UPSET)
                print(f"Upset plot saved to {OUTPUT_UPSET}")
        elif action == "c":  # continue
            os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
            break

    # Check if file exists and prompt user for overwrite
    if OUTPUT_CSV_PATH.exists() and not AUTOMATICALLY_OVERWRITE:
        user_input = input(
            f"File {OUTPUT_CSV_PATH} already exists. Overwrite? (y/n): "
        ).lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return
    # Step 5: Initialize agent and process papers
    print("Creating a chat with ollama")
    agent = setup_chat_agent()

    print("Analyzing papers with agent")
    results_df = analyze_papers_with_agent(agent, papers_df, QUESTIONS)

    print(f"Saving results to {OUTPUT_CSV_PATH}")
    save_dataframe_to_csv(results_df, OUTPUT_CSV_PATH)

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
