from pathlib import Path
import shutil
import os
import uuid
from collections import defaultdict
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama, OllamaEmbeddings

# functions

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
def get_retriever_for_doc(doc_name :str, input_vectorstore: Chroma):
    # vectorstore.as_retriever() is a LangChain method to convert a vector db into a generic Retriever obejct,allowing for semantic searches
    return input_vectorstore.as_retriever(
        search_type="mmr",  # better diversity
        search_kwargs={
            "k": 8,                 # Number of returning documents, 8 is fewer but higher precision
            "fetch_k": 20,          # initial candidate pool
            "lambda_mult": 0.7,     # balance relevance/diversity
            "filter": {"source": doc_name}
        }
    )    
# Retrieve chunks using metadata filtering inside the vectorstore    
def retrieve_chunks_for_document(question, doc_name, input_vectorstore : Chroma):
    print(f'\nget_retriever_for_doc {doc_name}')
    doc_retriever = get_retriever_for_doc(doc_name,input_vectorstore)
    print(f'invoking {question}')
    retrieved_docs = doc_retriever.invoke(question)

    if not retrieved_docs:
        return ""
    print(f'format_docs_with_metadata')
    return format_docs_with_metadata(retrieved_docs)

def build_rag_chain(vectorstore : Chroma, input_prompt_template : ChatPromptTemplate, input_llm : ChatOllama):
    """
    Build the pipeline to setup the context for the agents.
    1. {
        context:  8chunks retreived data from the papers stored in the vectorstore with Chroma
        question: input questions from the user
    } 
    2. Intruction from the user on how the agent should behave
    3. The agent, which is asked to anwser with a strict JSON format.
    """
    return (
        {
            "context": lambda x: retrieve_chunks_for_document(x["question"], x["document"], input_vectorstore=vectorstore),
            "question": lambda x: x["question"]
        }
        | input_prompt_template
        | input_llm.with_structured_output(AnswerWithSources, strict=True)
    )

# --------------- 1. Preparation stage ---------------

load_dotenv()

# define the embedding model
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.1")
# CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.2:3b")

embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)

llm = ChatOllama(
    model=CHAT_MODEL,
    temperature=0
)


# load and split the pdfs (create chunks)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300,
    separators=["\n\n", "\n", ".", " ", ""]
)

main_path = Path(".")
pdf_dir = main_path / "data" / "exampleFiles"

all_chunks = []
chunks_by_doc = defaultdict(list)
print(f"chunking {pdf_dir}")
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

GLOBAL_DB_PATH = "vectorstore_chroma"
# # clean vectorstore directory to avoid issues 

# build a vectorstore 
if input(f"Clear Chroma vectorebase {GLOBAL_DB_PATH}: y/n (default)") == "y":
    shutil.rmtree(GLOBAL_DB_PATH, ignore_errors=True)   # removes the entire directory, incl all files/subfolders.
    os.makedirs(GLOBAL_DB_PATH, exist_ok=True) # creates the directory again
    print(f"Building vectore store in {GLOBAL_DB_PATH}")
else :
    print(f"Loading vectore store in {GLOBAL_DB_PATH}")

vectorstore = Chroma.from_documents(
    documents=all_chunks,
    embedding=embedding_function,
    persist_directory=GLOBAL_DB_PATH
)
print("Vectorstore ready with:",
      len(vectorstore.get()['documents']), "documents")

# ----------------- 2. RETRIEVE, AUGMENT, GENERATE ----------------

# create the RAG prompt and structure 
from typing import Literal

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
rag_chain = build_rag_chain(vectorstore=vectorstore, input_prompt_template=prompt_template,input_llm=llm)

print("building Rag Chain")


# define the criterion, guided by the conceptual model
criteria = [
    "Does the paper demonstrate an application related to any of the port call steps (vessel's pre-arrival, arrival, port visit, departure, or post-departure)?", #either this or the next one to give 1
    "Does the paper mention any port call-related processes, like vessel manevuering or trajectory analysis, route prediction, ETA prediction, movement planning within port area, port traffic management, vessel traffic coordination, arrival/departure scheduling and handling, berth allocation/operations, anchorage management?", # or this one

    "Does the paper focus on seaside, nautical, or vessel traffic-related aspects of a port call?", 
    "Is the primary focus of the paper on operations conducted within or around port boundaries and infrastructure?",
    "Does the paper demonstrate an application of machine learning or artificial intelligence (e.g., supervised learning, unsupervised learning, deep learning, reinforcement learning)?"
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

df.to_csv(main_path / "1_FullTextCriteria_Results14.csv")

print("\nSaved to results directory as 1_FullTextCriteria_Results.csv")

# print(chunks[12].page_content[:500])
