"""Ollama and LangChain agent functions for paper analysis."""

import pandas as pd
from langchain_ollama import ChatOllama
from pandera.typing.pandas import DataFrame
from tqdm import tqdm

from slrrag.input import OLLAMA_MODELS
from slrrag.settings import SchemaPapers

tqdm.pandas()

IS_REASONING_ACTIVATED = False

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


# TODO : make it simpler
DEFAULT_PROMPT = """
You are an expert in nautical safety, especially about assessing risk assessment of collision between vessels and offshore platforms. You are conducting a literature review. 
Your task is to evaluate studies based on specific crtiteria.

Inclusion Criteria:
- Goals : Papers with at least one of these five goals ; 1) Quantitative risk assessment of collision and allision between vessels and offshore infrastructures. 2) Safe distance between offshore infrastructures and maritime traffic. 3) Decision making of location of infrastructures or maritime routes, taking account of maritime traffic safety. 4) Operational risk assessment of collision in real-time. 5) Impact of offshore infrastructure on maritime traffic.
- Environment: The context must be related to an offshore infrastructure, like oil platform or wind farms, or other similar infrastructures.
- Study Design: The paper should present a quantitative methodology to assess nautical safety with an emphasize on factors that increase risk of collision.

Exclusion Criteria:
- The paper does respond to all the inclusion criteria
- The paper is not in english
- The paper analyzes the consequence of the collision on the infrastructures/ships, but does not study its likelihood.
- The paper talks about other risks than collisions between vessels and offshore infrastructures.

Answer with a JSON object containing:
- 'answer': 'True' or 'False'
- 'explanation': a short explanation (1-2 sentences)

Title: {title}
Abstract: {abstract}
"""


def analyze_paper(
    agent: ChatOllama, title: str, abstract: str, model_name: str, input_prompt: str
) -> dict:
    """Use the agent to answer questions about a paper."""
    answers = {}
    input_text = input_prompt.format(title=title, abstract=abstract)
    response = agent.invoke(input_text)
    answers["answer_" + model_name] = response.get("answer")

    answers["explanation_" + model_name] = response.get("explanation")
    return answers


def analyze_papers_with_list_agents(
    list_agents_name: list[str], papers_df: DataFrame[SchemaPapers], input_prompt: str
) -> pd.DataFrame:
    """Analyze papers using agent and return DataFrame with answers."""

    def apply_func(paper_input: pd.Series, agent_input: ChatOllama, model_name: str):
        answers: dict = analyze_paper(
            agent_input,
            paper_input["title"],
            paper_input["abstract"],
            input_prompt=input_prompt,
            model_name=model_name,
        )
        return pd.Series(answers)

    for agent_model_name in list_agents_name:
        print("-----", agent_model_name, "Reasoning : ", IS_REASONING_ACTIVATED ," -------")
        agent = ChatOllama(
            model=agent_model_name, reasoning=IS_REASONING_ACTIVATED
        ).with_structured_output(output_schema)
        outputs_questions = papers_df.progress_apply(
            lambda paper_el: apply_func(
                paper_input=paper_el, agent_input=agent, model_name=agent_model_name
            ),
            axis=1,
        )
        papers_df = pd.concat((papers_df, outputs_questions), axis=1)
        # papers_df.to_csv(f"data/papers_selection/backup_{agent_model_name}.csv")
    return papers_df


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from slrrag.toolbox.files import save_dataframe_to_csv

    print(f"Analyzing papers with agent : {OLLAMA_MODELS}")
    if len(sys.argv) < 2:
        print("Usage: uv run src/slrrag/ollama_analysis.py <input_csv> <output_csv>")
    input_csv = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])
    input_df = pd.read_csv(input_csv)
    # Uncomment next line for testing purposes
    # input_df = pd.concat((input_df.head(4), input_df[input_df["is_reference"]]))
    print("Input prompt", DEFAULT_PROMPT)
    results_df = analyze_papers_with_list_agents(
        OLLAMA_MODELS, input_df, DEFAULT_PROMPT
    )
    print(f"Saving results to {output_csv}")
    save_dataframe_to_csv(results_df, output_csv)
    print(f"Analysis complete. Results saved to {output_csv}")
