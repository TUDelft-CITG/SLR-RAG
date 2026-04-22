import os
import csv
from pathlib import Path
from time import sleep
from typing import List, Dict, Optional, Union
import langchain_core
from pybliometrics.scopus import ScopusSearch
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pybliometrics
from tqdm import tqdm
from langchain_core.runnables.base import RunnableSequence
from pyalex import Works
import json
import getpass
import os


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
    "10.1016/j.oceaneng.2021.109396"
]

QUESTIONS = [
    "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or Vessels.",
    "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms.",
    "This paper includes a quantitative model.",
]

AUTOMATICALLY_OVERWRITE = False
OUTPUT_PATH = Path("output/")
OUTPUT_CSV_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_DOI_RESULTS = OUTPUT_PATH / "papers_selected.json"
OLLAMA_MODEL = "llama3.1"
MISTRAL_MODEL = "ministral-3b-2512"
PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', without a dot, nothing else."
SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1

# --- Scopus functions ---
def query_scopus(query: str) -> Optional[ScopusSearch]:
    """Query Scopus and return results."""
    try:
        nb_paper = ScopusSearch(query=query, download=False).get_results_size()
    except Exception as e:
        print(e,"\nreturning None")
        return None
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in Scopus. Continue? (y/n)").lower()
        if user_input == 'y':
                return ScopusSearch(query=query, verbose=True,subscriber=SCOPUS_IS_SUBSCRIBER)
        else:
            return None
    return ScopusSearch(query=query, verbose=True,subscriber=SCOPUS_IS_SUBSCRIBER)

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
    works = Works().search_filter(title_and_abstract= query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != 'y':
            return None
    print(f"{nb_paper} found in OpenAlex. Downloading.")
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
    nb_paper_without_doi = 0
    for paper in scopus_papers + openalex_papers:
        if not paper["doi"]:
            nb_paper_without_doi+=1
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

    print(f"Number of papers without doi removed : {nb_paper_without_doi}")
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

# --- LangChain agent ---
def setup_chat_agent() -> ChatOllama:
    """Initialize Chat agent."""
    user_out_agent = input(f"Use ollama:{OLLAMA_MODEL} ('o') , or Mistral ('m')?\n>")
    while True: 
        if user_out_agent == 'o':
            print(f"using ollama:{OLLAMA_MODEL}")
            return ChatOllama(model=OLLAMA_MODEL)        
        elif user_out_agent == 'm':
            print(f"Using Mistral 🥖🐈")
            if "MISTRAL_API_KEY" not in os.environ:
                os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter your Mistral API key: ")
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
        user_input = input(f"Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'e' to exit\n  's' to save to '{OUTPUT_DOI_RESULTS}'\n> ").lower()
        if user_input in ['c', 'p', 'e', 's']:
            return user_input
        print("Invalid option. Please try again.")

# --- Main workflow ---
def main():
    # Step 1: Query Scopus
    print("---- Getting query on Scopus ---")
    print("Query :", SCOPUS_QUERY)
    #assert SCOPUS_QUERY == OLD_SCOPUS_QUERY
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
    merged_papers : Dict = merge_papers(scopus_papers, openalex_papers)
    print_merged_stats(merged_papers, REFERENCE_DOIS)

    # Step 4: User interaction
    while True:
        action = prompt_user_for_action()
        if action == 'e':  # exit
            return
        elif action == 'p':  # print names
            for idx, (doi, paper) in enumerate(merged_papers.items(), 1):
                print(f"{idx}. {paper['title']} {'(Reference)' if doi in REFERENCE_DOIS else ''}")
            continue
        elif action == 's': 
            os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
            if OUTPUT_DOI_RESULTS.exists() and not AUTOMATICALLY_OVERWRITE and (input(f"File {OUTPUT_DOI_RESULTS} already exists. Overwrite? (y/n): ").lower() != 'y'):
                print("Operation cancelled by user.")
            else:
                with open(OUTPUT_DOI_RESULTS, "w") as file:
                    json.dump(merged_papers,file)
                print(f'Results saved in {OUTPUT_DOI_RESULTS}')
        elif action == 'c':  # continue
            os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
            break

    # Check if file exists and prompt user for overwrite
    if OUTPUT_CSV_PATH.exists() and not AUTOMATICALLY_OVERWRITE:
        user_input = input(f"File {OUTPUT_CSV_PATH} already exists. Overwrite? (y/n): ").lower()
        if user_input != 'y':
            print("Operation cancelled by user.")
            return
    # Step 5: Initialize agent and process papers
    print("Creating a chat with ollama")
    agent = setup_chat_agent()
    
    
    print(f"Opening {OUTPUT_CSV_PATH}")
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["doi", "title", "date"] + QUESTIONS)
        print("Writing header")
        writer.writeheader()
        print("Answering the questions")
        for paper in tqdm(merged_papers.values()):
            answers = analyze_paper(agent, paper["title"], paper.get("abstract", ""), QUESTIONS)
            writer.writerow({"doi": paper["doi"], "title": paper["title"], "date": paper["date"], **answers})
            sleep(1) # Too avoid rate limit

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()