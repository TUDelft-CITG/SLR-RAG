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

MAIN_QUERY = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
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
DEFAULT_DF_COLUMNS = ["doi", "id", "title", "date", "abstract"]


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
                return pd.DataFrame(columns=DEFAULT_DF_COLUMNS)
    except Exception as e:
        print(e, "\nReturning empty DataFrame")
        return pd.DataFrame(columns=DEFAULT_DF_COLUMNS)


def scopus_to_dict_list(results: ScopusSearch) -> pd.DataFrame:
    """Convert Scopus results to a pandas DataFrame."""
    if results.results is None:
        return pd.DataFrame(columns=DEFAULT_DF_COLUMNS)
    data = [
        {
            "doi": paper.doi,
            "title": paper.title,
            "date": paper.coverDate,
            "abstract": paper.description,
            "id": paper.eid,
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
            return pd.DataFrame(columns=["doi", "title", "date", "abstract"])
    print(f"{nb_paper} found in OpenAlex. Downloading.")
    list_ret = []
    pager = works.paginate(per_page=DEFAULT_OPEN_ALEX_PAGING)
    for page in pager:
        list_ret += page

    # Convert to DataFrame
    return_df = pd.DataFrame(
        list_ret, columns=["doi", "id", "title", "publication_date", "abstract"]
    )
    return_df = return_df.rename(columns={"publication_date": "date"})
    return_df["doi"] = return_df["doi"].str.removeprefix("https://doi.org/")
    return return_df

# --- Merge and stats functions ---
def merge_papers(scopus_df: pd.DataFrame, openalex_df: pd.DataFrame) -> pd.DataFrame:
    """Merge Scopus and OpenAlex papers by DOI, keeping only specified fields."""
    scopus_df["temp_key"] = scopus_df["doi"].fillna(scopus_df["title"])
    openalex_df["temp_key"] = openalex_df["doi"].fillna(openalex_df["title"])
    # Merge by DOI first, then by title if unavailable
    merged_df = pd.merge(
        scopus_df,
        openalex_df,
        on=["temp_key"],
        how="outer",
        suffixes=("_scopus", "_openalex"),
    )  # BUG: Will have duplicata if one has doi and not the other
    # Combine fields using vectorized operations
    # Title - prefer Scopus if available, otherwise OpenAlex
    merged_df["doi"] = merged_df["doi_scopus"].fillna(merged_df["doi_openalex"])
    merged_df["title"] = merged_df["title_scopus"].fillna(merged_df["title_openalex"])

    # Date - prefer Scopus if available, otherwise OpenAlex
    merged_df["date"] = merged_df["date_scopus"].fillna(merged_df["date_openalex"])

    # Abstract - prefer Scopus if available, otherwise OpenAlex
    merged_df["abstract"] = merged_df["abstract_scopus"].fillna(
        merged_df["abstract_openalex"]
    )

    # Select only the columns we want to keep
    result_df: pd.DataFrame = merged_df[
        ["doi", "title", "date", "abstract", "id_scopus", "id_openalex"]
    ].copy()  # pyright: ignore

    return result_df


def show_merged_stats(merged_papers: pd.DataFrame, reference_dois: List[str]) -> None:
    """Print statistics about merged papers."""
    total_papers = len(merged_papers)
    merged_papers["in_scopus"] = merged_papers["id_scopus"].notna()
    merged_papers["in_openalex"] = merged_papers["id_openalex"].notna()
    common_papers = (merged_papers["in_scopus"] & merged_papers["in_openalex"]).sum()
    ref_in_scopus = (
        merged_papers["in_scopus"] & merged_papers["doi"].isin(reference_dois)
    ).sum()
    ref_in_openalex = (
        merged_papers["in_openalex"] & merged_papers["doi"].isin(reference_dois)
    ).sum()
    ref_in_both = (
        merged_papers["in_scopus"]
        & merged_papers["in_openalex"]
        & merged_papers["doi"].isin(reference_dois)
    ).sum()

    print(f"Total number of papers: {total_papers}")
    print(f"Number of papers in common between both: {common_papers}")
    print(f"Number of reference papers in Scopus: {ref_in_scopus}")
    print(f"Number of reference papers in OpenAlex: {ref_in_openalex}")
    print(f"Number of reference papers in both: {ref_in_both}")

def plot_and_save_upset(df_input: pd.DataFrame, output_html : Path | str):
    upset_fig = plot_upset(df_input)
    if check_overwrite(output_html, AUTOMATICALLY_OVERWRITE):
        upset_fig.write_html(output_html)

def plot_upset(df_input: pd.DataFrame) -> plotly.graph_objs._figure.Figure:
    # set TRUE/FALSE if the paper exists or not for each database
    df_input[LIST_NAME_DATABASE] = df_input[[f"id_{x}" for x in LIST_NAME_DATABASE]].notna() 
    df_input[LIST_NAME_DATABASE].to_csv("output.csv",index=False)
    return Upset.generate_plot(df_input[LIST_NAME_DATABASE])

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

    # Step 3: Merge papers
    print("---- Merging papers ---")
    merged_papers: pd.DataFrame = merge_papers(results_scopus, results_openalex)
    show_merged_stats(merged_papers, REFERENCE_DOIS)
    # Step 4: User interaction
    while True:
        action = prompt_user_for_action()
        if action == "e":  # exit
            return
        elif action == "p":  # print names
            for idx, (doi, paper) in enumerate(
                zip(merged_papers["doi"], merged_papers.to_dict("records")), 1
            ):
                print(
                    f"{idx}. {paper['title']} {'(Reference)' if doi in REFERENCE_DOIS else ''}"
                )
            continue
        elif action == "s":
            # Save merged papers as CSV instead of JSON
            save_dataframe_to_csv(merged_papers, OUTPUT_DOI_RESULTS)
        elif action == "u":
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
