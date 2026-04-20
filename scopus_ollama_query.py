import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Union
import langchain_core
from pybliometrics.scopus import ScopusSearch
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pybliometrics
from tqdm import tqdm
from langchain_core.runnables.base import RunnableSequence
from pyalex import Works

pybliometrics.init()

# --- User-defined variables ---
SCOPUS_QUERY = """
TITLE-ABS-KEY( 
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
)
"""

OPENALEX_QUERY = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
"""

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
]

QUESTIONS = [
    "This paper discuss about risk assessment or risk analysis in the context of nautical safety for ships or Vessels.",
    "This paper talks about nautical safety around offshore windfarms.",
    "This paper include a quantitative model.",
]

OUTPUT_CSV_PATH = Path("output/paper_analysis.csv")
OLLAMA_MODEL = "llama3.1"

PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', nothing else."

THRESHOLD_BIG_COUNT_PAPER = 1

# --- Scopus functions ---
def query_scopus(query: str) -> Optional[ScopusSearch]:
    """Query Scopus and return results."""
    nb_paper = ScopusSearch(query=query, download=False).get_results_size()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in Scopus. Continue? (y/n)").lower()
        if user_input == 'y':
            return ScopusSearch(query=query, verbose=True)
        else:
            return None
    return ScopusSearch(query=query, verbose=True)

def scopus_to_dict_list(results: ScopusSearch) -> List[Dict]:
    """Convert Scopus results to a list of dictionaries."""
    if results.results is None:
        return []
    return [
        {
            "doi": paper.doi,
            "title": paper.title,
            "date": paper.coverDate,
            "abstract": paper.description,
            "in_scopus": True,
            "in_openalex": False,
        }
        for paper in results.results if paper.doi is not None
    ]

# --- OpenAlex functions ---
def query_openalex(query: str) -> Optional[List[Dict]]:
    """Query OpenAlex and return results as a list of dictionaries."""
    works = Works().search_filter(title_and_abstract=OPENALEX_QUERY)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != 'y':
            return None
    print(f"{nb_paper} found in OpenAlex.")
    list_ret = []
    pager = works.paginate(per_page=50)
    for page in pager:
        list_ret += page
    return list_ret

def openalex_to_dict_list(results: List[Dict]) -> List[Dict]:
    """Convert OpenAlex results to a list of dictionaries."""
    return [
        {
            "doi": paper.get("doi").removeprefix("https://doi.org/"),
            "title": paper.get("title"),
            "date": paper.get("publication_date"),
            "abstract": paper.get("abstract", None),
            "in_scopus": False,
            "in_openalex": True,
        }
        for paper in results if paper.get("doi") is not None
    ]

# --- Merge functions ---
def merge_papers(scopus_papers: List[Dict], openalex_papers: List[Dict]) -> Dict[str, Dict]:
    """Merge Scopus and OpenAlex papers by DOI, keeping only specified fields."""
    merged = {}
    for paper in scopus_papers + openalex_papers:
        if not paper["doi"]:
            continue
        if paper["doi"] not in merged:
            merged[paper["doi"]] = {
                "doi": paper["doi"],
                "title": paper["title"],
                "date": paper["date"],
                "abstract": paper.get("abstract"),
                "in_scopus": paper["in_scopus"],
                "in_openalex": paper["in_openalex"],
            }
        else:
            existing = merged[paper["doi"]]
            if not existing["abstract"] and paper.get("abstract"):
                existing["abstract"] = paper["abstract"]
            existing["in_scopus"] = existing["in_scopus"] or paper["in_scopus"]
            existing["in_openalex"] = existing["in_openalex"] or paper["in_openalex"]
    return merged

def print_merged_stats(merged_papers: Dict[str, Dict], reference_dois: List[str]) -> None:
    """Print statistics about merged papers."""
    total_papers = len(merged_papers)
    common_papers = sum(1 for paper in merged_papers.values() if paper["in_scopus"] and paper["in_openalex"])
    ref_in_scopus = sum(1 for paper in merged_papers.values() if paper["in_scopus"] and paper["doi"] in reference_dois)
    ref_in_openalex = sum(1 for paper in merged_papers.values() if paper["in_openalex"] and paper["doi"] in reference_dois)
    ref_in_both = sum(1 for paper in merged_papers.values() if paper["in_scopus"] and paper["in_openalex"] and paper["doi"] in reference_dois)

    print(f"Total number of papers: {total_papers}")
    print(f"Number of papers in common between both: {common_papers}")
    print(f"Number of reference papers in Scopus: {ref_in_scopus}")
    print(f"Number of reference papers in OpenAlex: {ref_in_openalex}")
    print(f"Number of reference papers in both: {ref_in_both}")

# --- Ollama/LangChain agent ---
def setup_ollama_agent() -> ChatOllama:
    """Initialize Ollama agent."""
    return ChatOllama(model=OLLAMA_MODEL)

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
        user_input = input("Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'e' to exit\n> ").lower()
        if user_input in ['c', 'p', 'e']:
            return user_input
        print("Invalid option. Please try again.")

# --- Main workflow ---
def main():
    # Step 1: Query Scopus
    print("---- Getting query on Scopus ---")
    results_scopus = query_scopus(SCOPUS_QUERY)
    if results_scopus is None:
        scopus_papers = []
    else :
        print(f"Got {results_scopus.get_results_size()} papers .converting to dict_list")
        scopus_papers = scopus_to_dict_list(results_scopus)

    # Step 2: Query OpenAlex
    print("---- Getting query on OpenAlex ---")
    results_openalex = query_openalex(OPENALEX_QUERY)
    if results_openalex is None:
        openalex_papers = []
    else: 
        print("converting to dict_list")
        openalex_papers = openalex_to_dict_list(results_openalex)

    # Step 3: Merge papers
    print("---- Merging papers ---")
    merged_papers = merge_papers(scopus_papers, openalex_papers)
    print_merged_stats(merged_papers, REFERENCE_DOIS)

    # Step 4: User interaction
    while True:
        action = prompt_user_for_action()
        if action == 'e':  # exit
            return
        elif action == 'p':  # print names
            for idx, (doi, paper) in enumerate(merged_papers.items(), 1):
                print(f"{idx}. {paper['title']}")
            continue
        elif action == 'c':  # continue
            break

    # Step 5: Initialize agent and process papers
    print("Creating a chat with ollama")
    agent = setup_ollama_agent()
    os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
    print(f"Opening {OUTPUT_CSV_PATH}")
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["doi", "title", "date"] + QUESTIONS)
        print("Writing header")
        writer.writeheader()
        print("Answering the questions")
        for paper in tqdm(merged_papers.values()):
            answers = analyze_paper(agent, paper["title"], paper.get("abstract", ""), QUESTIONS)
            writer.writerow({"doi": paper["doi"], "title": paper["title"], "date": paper["date"], **answers})

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()