import csv
import json
import os
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional

import pandas as pd
import plotly
import pybliometrics
from pyalex import Works
from pybliometrics.scopus import ScopusSearch
from query_converter import convert_query_to_lens
from tqdm import tqdm
from upsetty import Upset
from query_converter import query_to_dimensions_url
from ollama_analysis import (
    setup_chat_agent,
    analyze_papers_with_agent,
)
pybliometrics.init()

# --- User-defined variables ---


### FIRST QUERY

# MAIN_QUERY = """
# ("collision" OR "allision" OR "accident" OR "safety" OR "risk assessment" OR "risk analysis") AND
# ("Offshore infrastructure" OR "Offshore construction"
# 	OR "Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF"
# 	OR "Offshore platform" OR "Oil platform" OR "Hydrogen platforms"
# 	OR "Offshore quay" OR "Offshore wharf"
# 	OR "Artificial Island" OR "Synthetic Island"
# 	OR "Bridge"
# 	OR "Flotel"
# 	OR "Aquaculture Farms"
# 	OR "Offshore Lidar"
# 	OR "Storm surge barrier" OR  "Flood Barrier"
# ) AND
# ("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
# ("maritime" OR  "navigational" OR "nautical")
# """

### SECOND QUERY

# MAIN_QUERY = """
# ("risk assessment" OR "risk analysis") AND
# ("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
# ("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
# ("maritime" OR  "navigational" OR "nautical")
# """
### THIRD QUERY


MAIN_QUERY = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("maritime" OR "navigational" OR "nautical")
"""

SCOPUS_QUERY = f"""
TITLE-ABS-KEY( {MAIN_QUERY})
"""

OPENALEX_QUERY = MAIN_QUERY


REFERENCE_PAPERS = [
   (
        "A dynamic risk assessment method to address safety of navigation concerns around offshore renewable energy installations",
        "10.1177/1475090219837409",
        True, True, True, True
    ),
    (
        "A Marine GIS-based Alert System to Prevent Vessels Collision with Offshore Platforms",
        "10.51400/2709-6998.2462",
        True, True, True, True
    ),
    (
        "A method for risk analysis of ship collisions with stationary infrastructure using AIS data and a ship manoeuvring simulator",
        "10.1016/j.oceaneng.2021.109396",
        True, True, True, True
    ),
    (
        "A Novel Method for Navigational Risk Assessment in Wind Farm Waters Based on the Fuzzy Inference System",
        "10.1155/2021/4588333",
        True, True, False, False
    ),
    (
        "A System-Theory and Complex Network-Fused Approach to Analyze Vessel–Wind Turbine Allisions in Offshore Wind Farm Waters",
        "10.3390/jmse11071306",
        True, True, True, True
    ),
    (
        "Assessing the impacts to vessel traffic from offshore wind farms in the Thames Estuary",
        "",
        True, False, True, False
    ),
    (
        "Evaluation of Ship Importance in Offshore Wind Farm Area Based on Fusion Gravity Model in Complex Network",
        "10.3390/su17188252",
        True, True, True, True
    ),
    (
        "Improving the coexistence of offshore wind farms and shipping; an international comparison of navigational risk assessment processes",
        "10.1007/s13437-018-0149-0",
        True, True, True, True
    ),
    (
        "Multi-Perspective Nautical Safety Risk Assessment of Allisions with Offshore Wind Parks",
        "10.2139/ssrn.5002935",
        True, False, False, False
    ),
    (
        "Navigational Risk Assessment in Offshore Wind Farms Using Spatial Ship Domain Models",
        "10.3390/app15126943",
        True, True, False, False
    ),
    (
        "Probabilistic approach for collision risk analysis of powered vessel with offshore platforms",
        "10.1016/j.oceaneng.2018.01.008",
        True, True, True, True
    ),
    (
        "Research on the Impact of Deep Sea Offshore Wind Farms on Maritime Safety",
        "10.3390/jmse13040699",
        True, True, True, True
    ),
    (
        "The Impact of Offshore Wind Farm Construction on Maritime Traffic Complexity; An Empirical Analysis of the Yangtze River Estuary",
        "10.3390/jmse12122232",
        True, True, True, True
    )
]
REFERENCE_DF = pd.DataFrame(REFERENCE_PAPERS, columns=["title", "doi", "present_openalex", "present_scopus", "present_lens", "present_dimensions"])

REFERENCE_DOIS = REFERENCE_DF["doi"].to_list()


QUESTIONS = [
    "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or Vessels. OR"
    "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms.",
    "This paper includes a quantitative model.",
]

AUTOMATICALLY_OVERWRITE = False

PATH_INPUT = Path("data/export_databases/")
PATH_LENS_EXPORT = PATH_INPUT / "lens-export.csv"
PATH_DIMENSIONS_EXPORT = PATH_INPUT / "dimensions-export.csv"

OUTPUT_PATH = Path("outputs/")
OUTPUT_CSV_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_DOI_RESULTS = OUTPUT_PATH / "papers_selected.csv"
OUTPUT_UPSET = OUTPUT_PATH / "upset.html"


SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50
LIST_NAME_DATABASE = ["scopus", "openalex"]
DEFAULT_DF_COLUMNS = ["doi", "title", "date", "abstract"]
DEFAULT_DF_COLUMNS_SCOPUS = DEFAULT_DF_COLUMNS + ["id_scopus"]
DEFAULT_DF_COLUMNS_OPENALEX = DEFAULT_DF_COLUMNS + ["id_openalex"]
DEFAULT_DF_COLUMNS_LENS = DEFAULT_DF_COLUMNS + ["id_lens"]
DEFAULT_DF_COLUMNS_DIMENSIONS = DEFAULT_DF_COLUMNS + ["id_dimensions"]

def check_doi_in_scopus(doi: str) -> bool:
    """Check if a DOI exists in Scopus."""
    try:
        from pybliometrics.scopus import ScopusSearch
        query = f'DOI("{doi}")'
        search = ScopusSearch(query=query, download=False, subscriber=True)
        return search.get_results_size() > 0
    except Exception:
        return False


def check_doi_in_openalex(doi: str) -> bool:
    """Check if a DOI exists in OpenAlex."""
    try:
        works = Works().filter_or(doi=doi)
        return works.count() > 0
    except Exception:
        return False


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

# --- Scopus functions ---
def query_scopus(query: str) -> pd.DataFrame:
    """Query Scopus and return results."""
    try:
        nb_paper = ScopusSearch(query=query, download=False).get_results_size()
        if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
            if input(f"{nb_paper} found in Scopus. Continue? (y/n)").lower() == "y":
                scopus_search = ScopusSearch(
                    query=query, verbose=True, subscriber=SCOPUS_IS_SUBSCRIBER
                )
                return scopus_to_dict_list(scopus_search)
            else:
                return pd.DataFrame(columns=DEFAULT_DF_COLUMNS_SCOPUS)
    except Exception as e:
        print(e, "\nReturning empty DataFrame")
        return pd.DataFrame(columns=DEFAULT_DF_COLUMNS_SCOPUS)


def scopus_to_dict_list(results: ScopusSearch) -> pd.DataFrame:
    """Convert Scopus results to a pandas DataFrame."""
    if results.results is None:
        return pd.DataFrame(columns=DEFAULT_DF_COLUMNS_SCOPUS)
    data = [
        {
            "doi": paper.doi,
            "title": paper.title,
            "date": paper.coverDate,
            "abstract": paper.description,
            "id_scopus": paper.eid,
        }
        for paper in results.results
    ]
    return pd.DataFrame(data)


# --- OpenAlex functions ---
def query_openalex(query: str) -> pd.DataFrame:
    """Query OpenAlex and return results as a pandas DataFrame."""

    works = Works().search_filter(title_and_abstract=query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != "y":  # Return empty Dataframe
            return pd.DataFrame(columns=DEFAULT_DF_COLUMNS_OPENALEX)
    print(f"{nb_paper} found in OpenAlex. Downloading.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in pager:
        list_ret += page
    # Convert to DataFrame
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


# --- Lens functions ---
def read_lens_export(csv_path: Path | str) -> pd.DataFrame:
    """Read Lens export CSV and extract required columns: doi, id, title, date, abstract."""
    df = pd.read_csv(csv_path)
    # Map common Lens column names to our standard format
    column_mapping = {
        "Title": "title",
        "DOI": "doi",
        "Abstract": "abstract",
        "Publication Year": "date",
        "Lens ID": "id_lens",
    }
    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Select only the columns we need, filling missing ones with None
    result_cols = DEFAULT_DF_COLUMNS_LENS
    for col in result_cols:
        if col not in df.columns:
            df[col] = None

    return df[result_cols].copy()


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


# --- Dimensions functions ---
def read_dimensions_export(csv_path: Path | str) -> pd.DataFrame:
    """Read Dimensions export CSV and extract required columns: title, doi, abstract, date, id_dimensions."""
    df = pd.read_csv(csv_path,skiprows=1)
    # Map Dimensions column names to our standard format
    column_mapping = {
        "Title": "title",
        "DOI": "doi",
        "Abstract": "abstract",
        "Publication date": "date",
        "Publication ID": "id_dimensions",
    }
    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Select only the columns we need, filling missing ones with None
    result_cols = DEFAULT_DF_COLUMNS_DIMENSIONS
    for col in result_cols:
        if col not in df.columns:
            df[col] = None

    return df[result_cols].copy()


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


def plot_and_save_upset(df_input: pd.DataFrame, output_html: Path | str):
    upset_fig = plot_upset(df_input)
    upset_fig.write_html(output_html)


def plot_upset(df_input: pd.DataFrame) -> plotly.graph_objs._figure.Figure:
    # set TRUE/FALSE if the paper exists or not for each database
    # Dynamically detect which id_{db} columns exist
    id_cols = [col for col in df_input.columns if col.startswith("id_")]
    database_names = [col.replace("id_", "") for col in id_cols]
    df_input[database_names] = df_input[id_cols].notna()
    return Upset.generate_plot(
        df_input[database_names + ["is_reference"]].rename(
            columns={"is_reference": "reference"}
        )
    )


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
    # Step 1: Query Scopus
    print("---- Getting query on Scopus ---")
    print("Query :", SCOPUS_QUERY)
    # assert SCOPUS_QUERY == OLD_SCOPUS_QUERY
    results_scopus = query_scopus(SCOPUS_QUERY)
    # Step 2: Query OpenAlex
    print("---- Getting query on OpenAlex ---")
    results_openalex = query_openalex(OPENALEX_QUERY)

    # Step 3: Merge papers from Scopus and OpenAlex
    print("---- Merging papers ---")
    database_names = ["scopus", "openalex"]
    merged_papers: pd.DataFrame = merge_papers(
        results_scopus, results_openalex, "openalex"
    )

    # Step 3b: Ask if user wants to add lens.database
    user_input = input("Search for Lens papers? (y/n): ").lower()
    if user_input == "y":
        merged_papers, database_names = add_lens_papers(merged_papers, database_names)

    # Step 3c: Ask if user wants to add dimensions.ai papers
    user_input = input("Search for Dimensions.ai papers? (y/n): ").lower()
    if user_input == "y":
        merged_papers, database_names = add_dimensions_papers(merged_papers, database_names)

    # Add reference papers in the final dataframe.
    merged_papers = add_reference_papers(merged_papers, REFERENCE_DOIS)
    merged_papers = show_merged_stats(merged_papers, REFERENCE_DOIS, database_names)

    # Step 4: User interaction
    while True:
        action = prompt_user_for_action()
        if action == "e":  # exit
            return
        elif action == "p":  # print names
            for idx, (doi, paper) in enumerate(
                zip(merged_papers["doi"], merged_papers.to_dict("records")), 1
            ):
                if paper["title"] is not None:
                    print(
                        f"{idx}. {paper['title']} {'(Reference)' if doi in REFERENCE_DOIS else ''}"
                    )
        elif action == "s":  # Save merged papers as CSV
            save_dataframe_to_csv(merged_papers, OUTPUT_DOI_RESULTS)
        elif action == "u":
            if check_overwrite(OUTPUT_UPSET, AUTOMATICALLY_OVERWRITE):
                plot_and_save_upset(merged_papers, OUTPUT_UPSET)
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
    results_df = analyze_papers_with_agent(agent, merged_papers, QUESTIONS)

    print(f"Saving results to {OUTPUT_CSV_PATH}")
    save_dataframe_to_csv(results_df, OUTPUT_CSV_PATH)

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
