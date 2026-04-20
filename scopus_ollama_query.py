import os
import csv
from pathlib import Path
from typing import List, Dict
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
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF" OR "offshore platforms") AND
("maritime" OR  "navigational" OR "nautical")
"""

OPENALEX_QUERY =  """
("risk assessment") AND ('Static') AND ('UK') AND
("Offshore windfarm") AND
("navigational")
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
    "Does this paper discuss about risk assessment or risk analysis in the context of nautical safety for ships or Vessels?",
    "Does this paper talks about nautical safety around offshore windfarms?",
    "Does this paper include a quantitative model?",
]


OUTPUT_CSV_PATH = Path("output/paper_analysis.csv")
OLLAMA_MODEL = "llama3.1"

PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nAnswer with 'Yes' or 'No'."

THRESHOLD_BIG_COUNT_PAPER = 50
# --- Scopus functions ---
def query_scopus(query: str) -> ScopusSearch:
    """Query Scopus and return results."""
    nb_paper = ScopusSearch(query=query,download=False).get_results_size()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in Scopus. Continue? (y/n)").lower()
        if user_input == 'y':
            return ScopusSearch(query=query,verbose=True)
        else:
            return None
def get_paper_stats_scopus(results: ScopusSearch, reference_dois: List[str]) -> Dict:
    """Calculate basic stats: total papers and references found."""
    list_doi_results = [x.doi for x in results.results]
    
    ref_count = len([doi for doi in reference_dois if doi in list_doi_results])
    total_papers = results.get_results_size()
    return {"total_papers": total_papers, "reference_count": ref_count}

# --- Open Alex functions ---

def query_openalex(query: str) -> Works:
    """
    Search OpenAlex API for papers matching the keywords.
    Args:
        keywords: Search query (e.g., "climate change mitigation").
        max_results: Maximum number of results to return.
    Returns:
        A openAlex Work
    """
    works = Works().search(query)
    nb_paper = works.count()
    if nb_paper > THRESHOLD_BIG_COUNT_PAPER:
        user_input = input(f"{nb_paper} found in OpenAlex. Continue? (y/n)").lower()
        if user_input != 'y':
            return None
    else :
        print(f"{nb_paper} found in OpenAlex.")
    list_ret = []
    pager = works.paginate(per_page=50)
    for page in pager:
        list_ret += page
    return list_ret            


def get_paper_stats_openalex(results: List[Dict], reference_dois: List[str]) -> Dict:
    """Calculate basic stats: total papers and references found."""
    list_doi_results = [x["doi"].removeprefix("https://doi.org/") for x in results if x.get("doi") is not None]
    ref_count = len([doi for doi in reference_dois if doi in list_doi_results])
    total_papers = len(results)
    return {"total_papers": total_papers, "reference_count": ref_count}

# --- Ollama/LangChain agent ---
def setup_ollama_agent() -> ChatOllama:
    """Initialize Ollama agent."""
    return ChatOllama(model=OLLAMA_MODEL)

def analyze_paper(agent, title: str, abstract: str, questions: List[str]) -> Dict:
    """Use the agent to answer questions about a paper."""
    prompt = ChatPromptTemplate.from_template(PROMPT_MODEL)
    chain : RunnableSequence = prompt | agent | StrOutputParser()
    answers = {}
    for q in questions:
        response = chain.invoke({"title": title, "abstract": abstract, "question": q})
        answers[q] = response.strip()
    return answers

def prompt_user_for_action() -> str:
    """
    Prompt the user for action: continue, print papers, or exit.
    Returns 'c' (continue), 'p' (print), or 'e' (exit).
    """
    while True:
        user_input = input("Choose an option:\n  'c' to continue with the agents\n  'p' to print papers' names\n  'e' to exit\n> ").lower()
        if user_input in ['c', 'p', 'e']:
            return user_input
        print("Invalid option. Please try again.")

# --- Main workflow ---
def main():

    # Step 1: Query Scopus
    
    # print("---- Getting query on Scopus ---")
    # results_scopus = query_scopus(SCOPUS_QUERY)
    # if results_scopus is None:
    #     return
    # print("Getting paper stats")
    # stats_scopus = get_paper_stats_scopus(results_scopus, REFERENCE_DOIS)
    # print(f"Retrieved {stats_scopus['total_papers']} papers on Scopus. {stats_scopus['reference_count']} reference papers found over {len(REFERENCE_DOIS)}.")
    # # Step 3: User interaction
    # while True:
    #     action = prompt_user_for_action()
    #     if action == 'e': # exit
    #         return
    #     elif action == 'p': # print names
    #         for idx, paper in enumerate(results_openalex.results, 1):
    #             print(f"{idx}. {paper.title}")
    #         continue
    #     elif action == 'c': # continue
    #         break

    # Step 2: Query OpenAlex
    print("---- Getting query on Scopus ---")
    results_openalex = query_openalex(OPENALEX_QUERY)
    print("getting papers stats")
    stats_openalex = get_paper_stats_openalex(results_openalex, REFERENCE_DOIS)
    print(f"Retrieved {stats_openalex['total_papers']} papers on Scopus. {stats_openalex['reference_count']} reference papers found over {len(REFERENCE_DOIS)}.")

    # Step 3: User interaction
    while True:
        action = prompt_user_for_action()
        if action == 'e': # exit
            return
        elif action == 'p': # print names
            for idx, paper in enumerate(results_openalex, 1):
                print(f"{idx}. {paper.get('title')}")
            continue
        elif action == 'c': # continue
            break

    # Step 4: Initialize agent and process papers
    print("Setting up ollama agent")
    agent = setup_ollama_agent()
    os.makedirs(OUTPUT_CSV_PATH.parent, exist_ok=True)
    print(f"opening {OUTPUT_CSV_PATH}")
    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["doi", "title", "date"] + QUESTIONS)
        print("writing header")
        writer.writeheader()
        print("Awnsering the questions")
        for paper in tqdm(results_openalex.results):
            doi = paper.doi
            title = paper.title
            date = paper.coverDate
            abstract = paper.description
            answers = analyze_paper(agent, title, abstract, QUESTIONS)
            writer.writerow({"doi": doi, "title": title, "date": date, **answers})

    print(f"Analysis complete. Results saved to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()