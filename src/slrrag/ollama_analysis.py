"""Ollama and LangChain agent functions for paper analysis."""

import getpass
import os
from typing import Dict, List
from pandera.typing.pandas import DataFrame

import pandas as pd
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_ollama import ChatOllama
from tqdm import tqdm

from slrrag.input import OLLAMA_MODELS
from slrrag.settings import SchemaPapers

tqdm.pandas()

# Model configuration
MISTRAL_MODEL = "ministral-3b-2512"
PROMPT_MODEL = "Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', without a dot, nothing else."
OLLAMA_MODEL = OLLAMA_MODELS[0]  # TODO : Make as a list


def setup_chat_agent(name_ollama_model: str) -> ChatOllama:
    """Initialize Chat agent."""
    user_out_agent = input(
        f"Use ollama:{name_ollama_model} ('o') , or Mistral ('m')?\n>"
    )
    while True:
        if user_out_agent == "o":
            print(f"using ollama:{name_ollama_model}")
            return ChatOllama(model=name_ollama_model)
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


def analyze_paper(
    agent: ChatOllama, title: str, abstract: str, questions: Dict[str, str]
) -> Dict:
    """Use the agent to answer questions about a paper."""
    prompt = ChatPromptTemplate.from_template(PROMPT_MODEL)
    chain: RunnableSequence = prompt | agent | StrOutputParser()
    answers = {}
    for q in questions.keys():
        response = chain.invoke(
            {"title": title, "abstract": abstract, "question": questions[q]}
        )
        answers[q + "_" + agent.model] = response.strip()
    return answers


def analyze_papers_with_agent(
    list_agents_name: List[str],
    papers_df: DataFrame[SchemaPapers],
    questions: Dict[str, str],
) -> pd.DataFrame:
    """Analyze papers using agent and return DataFrame with answers."""
    papers_df = papers_df.sample(2)

    def apply_func(paper_input: pd.Series, agent_input: ChatOllama):
        answers: dict = analyze_paper(
            agent_input, paper_input["title"], paper_input["abstract"], questions
        )
        return pd.Series(answers)

    for agent_model in list_agents_name:
        agent = ChatOllama(model=agent_model)
        outputs_questions = papers_df.progress_apply(
            lambda x: apply_func(x, agent_input=agent), axis=1
        )
        papers_df = pd.concat((papers_df, outputs_questions), axis=1)
    return papers_df


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from slrrag.input import FIRST_ROUND_QUESTIONS
    from slrrag.toolbox.files import save_dataframe_to_csv

    print(f"Analyzing papers with agent : {OLLAMA_MODELS}")
    if len(sys.argv) < 2:
        print("Usage: uv run src/slrrag/ollama_analysis.py <input_csv> <output_csv>")
    input_csv = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])
    input_df = pd.read_csv(input_csv)
    results_df = analyze_papers_with_agent(
        OLLAMA_MODELS, input_df, FIRST_ROUND_QUESTIONS
    )

    print(f"Saving results to {output_csv}")
    save_dataframe_to_csv(results_df, output_csv)
    print(f"Analysis complete. Results saved to {output_csv}")
