"""Ollama and LangChain agent functions for paper analysis."""

import getpass
import os
from time import sleep
from typing import Dict, List
from pandera.typing.pandas import DataFrame

import pandas as pd
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_ollama import ChatOllama
from tqdm import tqdm

from slrrag.settings import SchemaPapers

# Model configuration
OLLAMA_MODEL = "llama3.1"
MISTRAL_MODEL = "ministral-3b-2512"
PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', without a dot, nothing else."


def setup_chat_agent() -> ChatOllama:
    """Initialize Chat agent."""
    user_out_agent = input(f"Use ollama:{OLLAMA_MODEL} ('o') , or Mistral ('m')?\n>")
    while True:
        if user_out_agent == "o":
            print(f"using ollama:{OLLAMA_MODEL}")
            return ChatOllama(model=OLLAMA_MODEL)
        elif user_out_agent == "m":
            print("Using Mistral")
            from langchain_mistralai import ChatMistralAI

            if "MISTRAL_API_KEY" not in os.environ:
                os.environ["MISTRAL_API_KEY"] = getpass.getpass(
                    "Enter your Mistral API key: "
                )
            return ChatMistralAI(model=MISTRAL_MODEL)
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


def analyze_papers_with_agent(
    agent, papers_df: DataFrame[SchemaPapers], questions: List[str]
) -> pd.DataFrame:
    """Analyze papers using agent and return DataFrame with answers."""
    results = []

    for paper in tqdm(papers_df.to_dict("records")):
        answers = analyze_paper(
            agent, paper["title"], paper.get("abstract", ""), questions
        )
        paper_with_answers = {
            "doi": paper["doi"],
            "title": paper["title"],
            "date": paper["date"],
            **answers,
        }
        results.append(paper_with_answers)
        sleep(1)  # To avoid rate limit

    return pd.DataFrame(results)
