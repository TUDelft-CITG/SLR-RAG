import csv
import getpass
import json
import os
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional
import plotly
import pandas as pd
import pybliometrics
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_mistralai import ChatMistralAI
from langchain_ollama import ChatOllama
from pyalex import Works
from pybliometrics.scopus import ScopusSearch
from tqdm import tqdm
from upsetty import Upset

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


REFERENCE_DOIS = [
    "10.1007/s13437-018-0149-0",
    "10.51400/2709-6998.2462",
    "10.51400/2709-6998.2462",
    "10.1016/j.oceaneng.2018.01.008",
    "10.3390/jmse13040699",
    "10.3390/su17188252",
    "10.3390/jmse12122232",
    "10.3390/jmse11071306",
    "10.1016/j.oceaneng.2021.109396",
    "10.2139/ssrn.5002935",
    "10.1016/j.oceaneng.2021.10939610.1016/j.oceaneng.2021.109396",
]

QUESTIONS = [
    "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or Vessels.",
    "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms.",
    "This paper includes a quantitative model.",
]

AUTOMATICALLY_OVERWRITE = False

PATH_INPUT = Path("data/export_databases/")
PATH_LENS_EXPORT = PATH_INPUT / "lens-export.csv"

OUTPUT_PATH = Path("outputs/")
OUTPUT_CSV_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_DOI_RESULTS = OUTPUT_PATH / "papers_selected.csv"
OUTPUT_UPSET = OUTPUT_PATH / "upset.html"


OLLAMA_MODEL = "llama3.1"
MISTRAL_MODEL = "ministral-3b-2512"
PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', without a dot, nothing else."
SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50
LIST_NAME_DATABASE = ["scopus", "openalex"]
DEFAULT_DF_COLUMNS = ["doi", "title", "date", "abstract"]
DEFAULT_DF_COLUMNS_SCOPUS = DEFAULT_DF_COLUMNS + ["id_scopus"]
DEFAULT_DF_COLUMNS_OPENALEX = DEFAULT_DF_COLUMNS + ["id_openalex"]
DEFAULT_DF_COLUMNS_LENS = DEFAULT_DF_COLUMNS + ["id_lens"]
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
    input_openalex_columns_name =  ["doi", "id", "title", "publication_date","abstract"]
    # Due to legal reasons, we have to extract the abstract manually : https://pypi.org/project/pyalex/#get-abstract:~:text=Get%20abstract
    return_df = pd.DataFrame([[x[col_name] for col_name in input_openalex_columns_name] for x in list_ret],columns=input_openalex_columns_name)
    return_df = return_df.rename(columns={"publication_date": "date", "id": "id_openalex"})
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


# --- Merge and stats functions ---
def merge_papers(left_df: pd.DataFrame, right_df: pd.DataFrame, right_db_name: str) -> pd.DataFrame:
    """Merge two paper DataFrames by DOI/title, keeping only specified fields.
    
    Args:
        left_df: Left DataFrame to merge (can already contain id_{db} columns)
        right_df: Right DataFrame to merge  
        left_db: Name of left database (e.g., 'scopus')
        right_db: Name of right database (e.g., 'openalex')
    
    Returns:
        Merged DataFrame with columns: doi, title, date, abstract, plus all id_{db} columns
    """
    #Sometimes, doi / title do not have same uppercase : 10.1017/S0373463319000444 == 10.1017/s0373463319000444.
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
    merged_df["doi"] = merged_df[f"doi"].fillna(merged_df.get(f"doi_{right_db_name}", None))
    merged_df["title"] = merged_df[f"title"].fillna(merged_df.get(f"title_{right_db_name}", None))
    merged_df["date"] = merged_df[f"date"].fillna(merged_df.get(f"date_{right_db_name}", None))
    merged_df["abstract"] = merged_df[f"abstract"].fillna(merged_df.get(f"abstract_{right_db_name}", None))
    
    # Select columns to keep: core fields + all id columns that exist
    result_cols = DEFAULT_DF_COLUMNS + [col for col in all_id_cols if col in merged_df.columns]
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


def show_merged_stats(merged_papers: pd.DataFrame, reference_dois: List[str], database_names: List[str]) -> None:
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
    common_papers = pd.concat([merged_papers[f"in_{db}"] for db in database_names], axis=1).all(axis=1).sum()
    # Calculate papers appearing in at least one database

    found_papers = pd.concat([merged_papers[f"in_{db}"] for db in database_names], axis=1).any(axis=1).sum()
    print(f"Total number of papers: {found_papers}")
    print(f"Reference papers missing: {total_papers-found_papers}")
    print(f"Number of common papers in all databases: {common_papers}")
    
    # Print stats for each database
    for db in database_names:
        ref_in_db = (merged_papers[f"in_{db}"] & merged_papers["doi"].isin(reference_dois)).sum()
        in_db = merged_papers[f"in_{db}"].sum()
        print(f"Number of papers in {db}: {in_db}")
        print(f"Number of reference papers in {db}: {ref_in_db}")
    return merged_papers

def plot_and_save_upset(df_input: pd.DataFrame, output_html : Path | str):
    upset_fig = plot_upset(df_input)
    upset_fig.write_html(output_html)

def plot_upset(df_input: pd.DataFrame) -> plotly.graph_objs._figure.Figure:
    # set TRUE/FALSE if the paper exists or not for each database
    # Dynamically detect which id_{db} columns exist
    id_cols = [col for col in df_input.columns if col.startswith("id_")]
    database_names = [col.replace("id_", "") for col in id_cols]
    df_input[database_names] = df_input[id_cols].notna()
    return Upset.generate_plot(df_input[database_names + ["is_reference"]].rename(columns={"is_reference": "reference"}))

# --- File I/O functions ---
def check_overwrite(file_path: Path, automatically_overwrite: bool = AUTOMATICALLY_OVERWRITE) -> bool:
    if file_path.exists() and not automatically_overwrite:
        user_input = input(f"File {file_path} already exists. Overwrite? (y/n): ").lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return False
    return True
def save_dataframe_to_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Save DataFrame to CSV with overwrite protection."""
    os.makedirs(file_path.parent, exist_ok=True)
    if check_overwrite(file_path, AUTOMATICALLY_OVERWRITE): 
        df.to_csv(file_path, index=False)
        print(f"Results saved in {file_path}")
    

    

def analyze_papers_with_agent(agent, papers_df: pd.DataFrame, questions: List[str]) -> pd.DataFrame:
    """Analyze papers using agent and return DataFrame with answers."""
    results = []

    for paper in tqdm(papers_df.to_dict("records")):
        answers = analyze_paper(agent, paper["title"], paper.get("abstract", ""), questions)
        paper_with_answers = {
            "doi": paper["doi"],
            "title": paper["title"],
            "date": paper["date"],
            **answers
        }
        results.append(paper_with_answers)
        sleep(1)  # To avoid rate limit

    return pd.DataFrame(results)

# --- LangChain agent ---
def setup_chat_agent() -> ChatOllama:
    """Initialize Chat agent."""
    user_out_agent = input(f"Use ollama:{OLLAMA_MODEL} ('o') , or Mistral ('m')?\n>")
    while True:
        if user_out_agent == "o":
            print(f"using ollama:{OLLAMA_MODEL}")
            return ChatOllama(model=OLLAMA_MODEL)
        elif user_out_agent == "m":
            print(f"Using Mistral 🥖🐈")
            if "MISTRAL_API_KEY" not in os.environ:
                os.environ["MISTRAL_API_KEY"] = getpass.getpass(
                    "Enter your Mistral API key: "
                )
            return ChatMistralAI(model="ministral-3b-2512")
        else:
            print(f"Wrong output. {user_out_agent}")


def analyze_paper(agent, title: str, abstract: str, questions: List[str]) -> Dict:
    """Use the agent to answer questions about a paper."""
    prompt = ChatPromptTemplate.from_template(PROMPT_MODEL)
    chain: RunnableSequence = prompt | agent | StrOutputParser()
    answers = {}
    for q in questions:
        response = chain.invoke({"title": title, "abstract": abstract, "question": q})
        answers[q] = response.strip()
    return answers


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
    merged_papers: pd.DataFrame = merge_papers(results_scopus, results_openalex, "openalex")
    
    # Step 3b: Ask if user wants to add Lens export
    if PATH_LENS_EXPORT.exists():
        user_input = input(f"Add Lens papers from {PATH_LENS_EXPORT}? (y/n): ").lower()
        if user_input == "y":
            print("---- Reading Lens export ---")
            lens_df = read_lens_export(PATH_LENS_EXPORT)
            print(f"Found {len(lens_df)} papers in Lens export")
            print("---- Merging with Lens ---")
            merged_papers = merge_papers(merged_papers, lens_df, "lens")
            database_names.append("lens")
    
    merged_papers = add_reference_papers(merged_papers,REFERENCE_DOIS)
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
                if paper['title'] is not None:
                    print(f"{idx}. {paper['title']} {'(Reference)' if doi in REFERENCE_DOIS else ''}")
        elif action == "s":# Save merged papers as CSV
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
