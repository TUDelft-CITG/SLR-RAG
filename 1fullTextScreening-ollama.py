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
        out.append(f"[SOURCE={src}, CHUNK={cid}]\n{d.page_content}")
    return "\n\n".join(out)

def get_retriever_for_doc(doc_name):
    # vectorstore.as_retriever() is a LangChain method to convert a vector db into a generic Retriever obejct,allowing for semantic searches
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10, "filter": {"source": doc_name}}
    )
    
# Retrieve chunks using metadata filtering inside the vectorstore    
def retrieve_chunks_for_document(question, doc_name):
    doc_retriever = get_retriever_for_doc(doc_name)
    retrieved_docs = doc_retriever.invoke(question)

    if not retrieved_docs:
        return f"[No relevant chunks found for document: {doc_name}]"

    return format_docs_with_metadata(retrieved_docs)

def build_rag_chain():
    return (
        {
            "context": lambda x: retrieve_chunks_for_document(x["question"], x["document"]),
            "question": lambda x: x["question"]
        }
        | prompt_template
        | llm.with_structured_output(AnswerWithSources, strict=True)
    )

# --------------- 1. Preparation stage ---------------

load_dotenv()

# define the embedding model
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "mxbai-embed-large")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.2:3b")
    
embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)

llm = ChatOllama(
    model=CHAT_MODEL,
    temperature=0
)

# clean vectorstore directory to avoid issues 
GLOBAL_DB_PATH = "vectorstore_chroma"
shutil.rmtree(GLOBAL_DB_PATH, ignore_errors=True)   # removes the entire directory, incl all files/subfolders.
os.makedirs(GLOBAL_DB_PATH, exist_ok=True) # creates the directory again

# load and split the pdfs (create chunks)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300,
    separators=["\n\n", "\n", ".", " ", ""]
)

pdf_dir = "/data/exampleFiles"

all_chunks = []
chunks_by_doc = defaultdict(list)

for filename in os.listdir(pdf_dir):
    if filename.lower().endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)

        pages = PyPDFLoader(path).load()
        chunks = text_splitter.split_documents(pages)

        # Add metadata for filtering, with a counter
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = filename
            chunk.metadata["chunk_id"] = i

        chunks_by_doc[filename] = chunks
        all_chunks.extend(chunks)

print(f"Loaded total chunks: {len(all_chunks)}")

# build a vectorstore 
vectorstore = Chroma.from_documents(
    documents=all_chunks,
    embedding=embedding_function,
    persist_directory=GLOBAL_DB_PATH
)

print("Vectorstore ready with:",
      len(vectorstore.get()['documents']), "documents")

# ----------------- 2. RETRIEVE, AUGMENT, GENERATE ----------------

# create the RAG prompt and structure 
class AnswerWithSources(BaseModel):
    decision: int
    sources: str
    reasoning: str

PROMPT_TEMPLATE = """
You are a researcher assessing whether or not to include an article in a systematic literature review based on retrieved document context and the research topic of port call process optimisation using machine learning methods. Examine how the paper covers the main research question and give a binary conclusion (1 for inclusion, 0 for exclusion).

You MUST:
1. Make a decision, either 1 or 0 regarding if it should be included or excluded. 1 indicates inclusion, 0 indicates exclusion.
2. Cite exact quotes from context.
3. Explain your reasoning in 2–4 sentences.
4. If you are uncertain, respond: "Requires manual review"

--- CONTEXT ---
{context}
---

Respond ONLY in valid JSON:
{{
  "decision": "...",
  "sources": "...",
  "reasoning": "..."
}}

Question: {question}
"""

prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

rag_chain = build_rag_chain()

# define the questions, guided by the conceptual model
questions = [
    "Should the paper be included in a systematic literature review about machine learning applications in a port call process?",
]

# run the pipeline
rows = []

for doc_name in chunks_by_doc.keys():
    print(f"\nProcessing: {doc_name}")
    row = {"document": doc_name}

    for i, q in enumerate(questions, 1):
        try:
            result = rag_chain.invoke({"document": doc_name, "question": q})
            row[f"Q{i}_Decision"] = result.decision
            row[f"Q{i}_Source"] = result.sources
            row[f"Q{i}_Reasoning"] = result.reasoning
        except Exception as e:
            row[f"Q{i}_Source"] = ""
            row[f"Q{i}_Source"] = ""
            row[f"Q{i}_Reasoning"] = str(e)

    rows.append(row)

# create a final table and csv file 
df = pd.DataFrame(rows).set_index("document")
print(df)
df.to_csv("1_fullTextScreening_results.csv")

print("\nSaved to 1_fullTextScreening_results.csv")
