import os
import shutil
from collections import defaultdict
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

# functions


# changed 27Feb
def format_docs_with_metadata(docs):
    out = []
    for d in docs:
        src = d.metadata.get("source")
        cid = d.metadata.get("chunk_id")
        page = d.metadata.get("page")
        section = d.metadata.get("section", "unknown")

        header = f"[SOURCE={src} | CHUNK={cid} | PAGE={page} | SECTION={section}]"
        out.append(f"{header}\n{d.page_content}")

    return "\n\n---\n\n".join(out)


# UPDATED 27 FEB
def get_retriever_for_doc(doc_name):
    return vectorstore.as_retriever(
        search_type="mmr",  # better diversity
        search_kwargs={
            "k": 8,  # fewer but higher precision
            "fetch_k": 20,  # initial candidate pool
            "lambda_mult": 0.7,  # balance relevance/diversity
            "filter": {"source": doc_name},
        },
    )


# Retrieve chunks using metadata filtering inside the vectorstore
def retrieve_chunks_for_document(question, doc_name):
    doc_retriever = get_retriever_for_doc(doc_name)
    retrieved_docs = doc_retriever.invoke(question)

    if not retrieved_docs:
        return ""

    return format_docs_with_metadata(retrieved_docs)


def build_rag_chain():
    return (
        {
            "context": lambda x: retrieve_chunks_for_document(
                x["question"], x["document"]
            ),
            "question": lambda x: x["question"],
        }
        | prompt_template
        | llm.with_structured_output(AnswerWithSources, strict=True)
    )


# --------------- 1. Preparation stage ---------------

load_dotenv()

# define the embedding model
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen3:8b")
# CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.2:3b")

embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)

llm = ChatOllama(model=CHAT_MODEL, temperature=0)

# clean vectorstore directory to avoid issues
GLOBAL_DB_PATH = "vectorstore_chroma"
shutil.rmtree(
    GLOBAL_DB_PATH, ignore_errors=True
)  # removes the entire directory, incl all files/subfolders.
os.makedirs(GLOBAL_DB_PATH, exist_ok=True)  # creates the directory again

# load and split the pdfs (create chunks)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=300, separators=["\n\n", "\n", ". ", " ", ""]
)

pdf_dir = "/Users/lvolu/Documents/1-DataProjects/1-RAG_LLM_Article1/data/2-CONTENT-ANALYSIS/2-TrafficCongestion/newBatch18Mar/subBatch1"
results_dir = "/Users/lvolu/Documents/1-DataProjects/1-RAG_LLM_Article1/results/ContentAnalysis2026/2_contentAnalysisResultsTrafficAdditional1.csv"

all_chunks = []
chunks_by_doc = defaultdict(list)

for filename in os.listdir(pdf_dir):
    if filename.lower().endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)

        pages = PyPDFLoader(path).load()
        chunks = text_splitter.split_documents(pages)

        # Add standardized metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = filename
            chunk.metadata["chunk_id"] = i
            chunk.metadata["page"] = chunk.metadata.get("page", None)
            chunk.metadata["section"] = chunk.metadata.get("section", "unknown")

        chunks_by_doc[filename] = chunks
        all_chunks.extend(chunks)

print(f"Loaded total chunks: {len(all_chunks)}")


# build a vectorstore
vectorstore = Chroma.from_documents(
    documents=all_chunks, embedding=embedding_function, persist_directory=GLOBAL_DB_PATH
)

print("Vectorstore ready with:", len(vectorstore.get()["documents"]), "documents")

# ----------------- 2. RETRIEVE, AUGMENT, GENERATE ----------------

# create the RAG prompt and structure


class AnswerWithSources(BaseModel):
    answer: Literal[0, 1]
    sources: str
    reasoning: str


PROMPT_TEMPLATE = """
You are a systematic review assistant.

Your task is to determine whether the provided question is explicitly addressed in the given context.

STRICT INSTRUCTIONS:

1. Use ONLY the provided context.
2. The element must be explicitly stated in the text.
3. If the element is explicitly present, set "answer" = 1.
4. If the element is NOT explicitly present, set "answer" = 0.
5. If "answer" = 1:
   - "sources" MUST contain the exact SOURCE, CHUNK, and PAGE identifiers from the context header.
   - "reasoning" MUST briefly explain why the criterion is satisfied, based strictly on the retrieved text.
6. If "answer" = 0:
   - "sources" MUST be an empty string "".
   - "reasoning" MUST be an empty string "".
7. Output ONLY valid JSON. No additional text.

--- CONTEXT ---
{context}
---

Question: {question}

Respond ONLY in this JSON format:
{{
  "answer": 1 or 0,
  "sources": "SOURCE=..., CHUNK=..., PAGE=...",
  "reasoning": "..."
}}
"""

prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

rag_chain = build_rag_chain()


# define the questions, guided by the conceptual model
criteria = [
    # --------- 1. FIRST BLOCK --> DATA ACQUISITION ---------------
    # 1.1.
    "Is it described what type of data or datasets are used in the study/paper?",
    "Is it mentioned which data features, columns or fields are used in the study?",
    "Is it mentioned how much data are used in the study?",
    "Is it mentioned which time span is the data recorded or collected over?",
    "Does the paper describe how is the raw data quality assessed or validated?",
    "Are data limitations (e.g., coverage gaps, biases) explicitly mentioned?",
    # --------- 2. SECOND BLOCK --> DATA PROCESSING ---------------
    # Data cleaning and imputation
    "Does the paper describe how are noisy, inconsistent, or erroneous data records handled?",
    "Does the paper describe how are missing data are handled (e.g., removal, imputation, interpolation)?",
    "Does the paper explicitly describe any data preprocessing steps applied before model training?",
    "Does the paper describe how preprocessing steps account for real-world data variability (e.g., data drift, outliers)?",
    "Is the preprocessing workflow described in detail, including step-by-step actions taken?",  # these two (this + following) could be together
    "Are the preprocessing steps documented in a way that enables reproducibility and adaptation to different port systems?",  # maybe too specific
    # --------- 3. THIRD BLOCK --> MODEL DEVELOPMENT ---------------
    # 3.1. chosen ML techinques and methods
    "Are the chosen machine learning or artificial intelligence techniques used described in paper's methodology?",
    # ------ Either OR block (different wording): one has to be fulfilled (post-processing)
    "Is the model's training process (e.g., hyperparameters, loss functions) clearly documented?",  # "Is the machine learning model's parameter or hyperparameter selection process described?",
    "Is the model's training and evaluation process reproducible (e.g., code, data, hyperparameters, metrics)?",
    # ------ Either or block end
    # 3.2. model performance
    # ------ Either OR block (different wording): one has to be fulfilled (post-processing)
    "Is it described what metrics are used to evaluate the performance of the developed machine learning models?",
    "Are the quantitative performance results of the machine learning model(s) explicitly reported?",
    # ------ Either or block end
    "Are the potential issues regarding overfitting or underfitting discussed?",
    "Does the paper use any other baseline or benchmark methods to compare and assess the developed model's performance?",
    "Are the model's potential biases identified, and are mitigation strategies discussed?",
    "Does the paper discuss the limitations or failure cases of the developed model?",
    # Either OR block (different wording): one has to be fulfilled (post-processing)
    "Are computational efficiency or runtime considerations of the machine learning model mentioned?",
    "Is the model's computational efficiency (e.g., latency, resource usage) discussed in the context of real-time operations?",
    # ------ Either or block end
    "Is the model's performance evaluated under scenarios that mimic real-world conditions (e.g., noisy data, edge cases, time delays, partial data availability, data drift)?",  # "Does the paper evaluate the model's performance under real-world conditions?",
    # --------- 4. FOURTH BLOCK --> MODEL INTERPRETATION AND EVALUATION ---------------
    "Is it described for which operational or strategic task(s) are the machine learning methods developed?",
    "Are the model's outputs (e.g., predictions, recommendations) mapped to actionable decisions or operational workflows?",
    "Is the model's impact on operational workflows analyzed, and are trade-offs between automation and human oversight discussed?",
    "Is model interpretability or explainability discussed or demonstrated?",
    "Does the paper describe how can model results be related to business key performance indicators?",
    "Do the authors suggest concrete decision-making or operational actions based on the model's results?",
]

# run the pipeline
rows = []

for doc_name in chunks_by_doc.keys():
    print(f"\nProcessing: {doc_name}")
    row = {"document": doc_name}

    for i, q in enumerate(criteria, 1):
        try:
            result = rag_chain.invoke({"document": doc_name, "question": q})
            # row[f"Q{i}_Decision"] = result.decision
            row[f"Q{i}_Decision"] = result.answer
            row[f"Q{i}_Source"] = result.sources
            row[f"Q{i}_Reasoning"] = result.reasoning
        except Exception as e:
            row[f"Q{i}_Decision"] = "Error"
            row[f"Q{i}_Source"] = ""
            row[f"Q{i}_Reasoning"] = str(e)

    rows.append(row)


# create a final table and csv file
df = pd.DataFrame(rows).set_index("document")
print(df)
df.to_csv(results_dir)

print("\nSaved to results folder")
