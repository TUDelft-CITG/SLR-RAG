"""Ollama and LangChain agent functions for paper analysis."""

import pandas as pd
from langchain_ollama import ChatOllama
from pandera.typing.pandas import DataFrame
from tqdm import tqdm

from slrrag.input import OLLAMA_MODELS
from slrrag.settings import SchemaPapers

tqdm.pandas()
output_schema = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "enum": ["True", "False"],
            "description": "Binary answer: 'True' or 'False'",
        },
        "explanation": {
            "type": "string",
            "description": "A short explanation (1-2 sentences)",
        },
    },
    "required": ["answer", "explanation"],
}

# class AnswerWithJustification(TypedDict):
#     answer: str
#     justification: Annotated[str | None, None, "A justification for the answer."]
# Model configuration
MISTRAL_MODEL = "ministral-3b-2512"
SYSTEM_PROMPT = """
You are an agent that analyses papers, and your goal is respond to questions about it, that will be asked.

You will be given a title, abstract. Below, you will find a list of questions 
For each question, provide the anwser ONLY IN BINARY FORMAT (True or False), 
and a small explanation in one or two sentences.
Title: {title}\nAbstract: {abstract}\nQuestion: {question}\nOnly answer with 'True' or 'False', without a dot, nothing else."
"""
OLLAMA_MODEL = OLLAMA_MODELS[0]  # TODO : Make as a list


def setup_chat_agent(name_ollama_model: str) -> ChatOllama:
    """Initialize Chat agent."""
    return ChatOllama(model=name_ollama_model)


def analyze_paper(
    agent: ChatOllama, title: str, abstract: str, questions: dict, model_name: str
) -> dict:
    """Use the agent to answer questions about a paper."""
    answers = {}
    for q in questions:
        input_text = f"You are a precise assistant that analyse the tite and abstract of a paper to answer binary question. Answer with a JSON object containing:\n- 'answer': 'True' or 'False'\n- 'justification': a short explanation (1-2 sentences)\nTitle: {title}\nAbstract: {abstract}\nQuestion: {q.get('question')}"
        response = agent.invoke(input_text)
        answers[q.get("name", "") + "_answer_" + model_name] = response.get("answer")

        answers[q.get("name", "") + "_justification_" + model_name] = response.get(
            "explanation"
        )
    return answers


def analyze_papers_with_list_agents(
    list_agents_name: list[str],
    papers_df: DataFrame[SchemaPapers],
    questions: dict,
) -> pd.DataFrame:
    """Analyze papers using agent and return DataFrame with answers."""

    def apply_func(paper_input: pd.Series, agent_input: ChatOllama, model_name: str):
        answers: dict = analyze_paper(
            agent_input,
            paper_input["title"],
            paper_input["abstract"],
            questions,
            model_name=model_name,
        )
        return pd.Series(answers)

    for agent_model_name in list_agents_name:
        print("-----", agent_model_name, "-------")
        agent = ChatOllama(model=agent_model_name).with_structured_output(output_schema)
        outputs_questions = papers_df.progress_apply(
            lambda x: apply_func(x, agent_input=agent, model_name=agent_model_name),
            axis=1,
        )
        papers_df = pd.concat((papers_df, outputs_questions), axis=1)
        # papers_df.to_csv(f"data/papers_selection/backup_{agent_model_name}.csv")
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
    # Uncomment next line for testing purposes
    # input_df = pd.concat((input_df.head(4), input_df[input_df["is_reference"]]))
    print("Input questions", FIRST_ROUND_QUESTIONS)
    results_df = analyze_papers_with_list_agents(
        OLLAMA_MODELS, input_df, FIRST_ROUND_QUESTIONS
    )
    print(f"Saving results to {output_csv}")
    save_dataframe_to_csv(results_df, output_csv)
    print(f"Analysis complete. Results saved to {output_csv}")
