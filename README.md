# Systematic Literature Reviews (SLR) using Retrieval-Augmented Generation (RAG)

This project demonstrates a RAG-LLM pipeline for systematic literature reviews. RAG refers to the process of providing Large Language Models (LLMs) with additional information from an external knowledge source, thereby facilitating the generation of more relevant answers. 

## Overview of the implementation stages

The current implementation could be summarised with these four steps: 

PREPARE --> RETRIEVE --> AUGMENT --> GENERATE

For implementation, user action is required in the preparation stage, augmentation stage, and generation stage. 

### 1. Preparation stage - ACTION REQUIRED

#### 1.1. Select the models and define environment variables

Define environment variables in a .env file in the root directory. This depends on which models you use. If you opt for OpenAI's models, you would need to obtain an OpenAI API Key from your OpenAI account (go to API keys, and "Create new secret key"). Then enter that in the .env file (in the root directory) as follows: 

```
OPENAI_API_KEY = "INSERT-KEY-HERE"
```

You may also opt for open source models deployed locally without relying on cloud-hosted services, which allows for more privacy and offline functionalities. Ollama is a useful tool that allows working with a variety of models. To work with LLMs locally:

1. Download Ollama from [their official website](https://ollama.com/download/mac). 

Download and initiate the installation process on your computer. You can check your installation by running ```ollama list``` in your terminal window. This command lists all models currently available on your machine; if there are no models downloaded, the list is empty. 

2. Install the LLM you're going to execute (you will need to download a [chat model](https://ollama.com/search?c=tools) as well as an [embeddings model](https://ollama.com/search?c=embedding) from your Terminal). To do this, navigate to Ollama's website --> choose a model you want to use --> select the version of the model you want to download --> copy its code --> paste it into your terminal. For example, if you choose to go with the llama3.2:3b model, you can find and copy the code from the upper-right corner of the model's web description:

 <div align="center"><img width="818" height="497" alt="image" src="https://github.com/user-attachments/assets/865fe8e9-52a3-48c7-a5d7-3a00ebf97ec3" /></div>

 Copy ```ollama run llama3.2:3b``` into your console, this will install it in your machine. If the model is already installed, you can also start chatting with it (to exit the chat, type in ```/exit```):

 <div align="center"><img width="413" height="65" alt="image" src="https://github.com/user-attachments/assets/03802678-7657-4a41-acbf-b36bce18da9b" /></div>

Do the same installation process with an embeddings model:

<div align="center"><img width="806" height="367" alt="image" src="https://github.com/user-attachments/assets/5e76c4da-189f-445d-9b99-15868425dec0" /></div>

In this case, an example of the .env file for the project is: 

```
EMBEDDING_MODEL = "mxbai-embed-large"
CHAT_MODEL = "llama3.2:3b"
MODEL_PROVIDER = "ollama"
```

#### 1.2. Prepare the data (PDF documents)
The current code expects pdf documents as its input. Place these in your chosen folder, and remember to change the variable _pdf_dir_.

## 2. Retrieval stage - no action required

Retriever fetches context based on semantic similarity between the user query and embedded chunks. 

## 3. Augmentation stage - ACTION REQUIRED 

In this stage, you need to prepare a prompt template. The prompt example below supports content analysis based on full text, but you may also use the pipeline for other type of implementations. 

```
PROMPT_TEMPLATE = """
You are an assistant answering questions strictly based on retrieved document context. Examine how the paper covers the question and rank it with a coding scheme from 0 to 2 with 0 showing no presence, 1 showing superficial presence and 2 suggesting detailed coverage of the topic in the paper.

You MUST:
1. Answer concisely. 
2. Give the paper a score from 0 to 2 regarding how well it answers the question. 0 means the paper does not talk about it, 1 means superficial presence and 2 means detailed coverage of the topic in the paper.
3. Cite exact quotes from context.
4. Explain your reasoning in 2–4 sentences.
5. If information is missing, respond: "Not clearly stated in the document."

--- CONTEXT ---
{context}
---

Respond ONLY in valid JSON:
{{
  "answer": "...",
  "score": "...",
  "sources": "...",
  "reasoning": "..."
}}

Question: {question}
"""

```
## 4. Generation stage - ACTION REQUIRED 

Finally, the code chains together the retriever, prompt template and the LLM. Once this is defined, it can be invoked with your query. In this case, multiple questions are asked about each paper in the pool, this is not a fixed amount. 

```
questions = [
    "What datasets, data formats and how much data are used in the paper?",
    "Are the data public or private?",
    "How is the raw data quality checked or analysed?",
    "Does the paper use data cleaning techniques?",
    "Does the paper use other data pre-processing techniques, like data transformations, aggregation, feature engineering or data integration?",
    "Does the paper provide sufficient information to implement its methodology?",
    "How are the developed machine learning or mathematical methods evaluated?",
    "What are the recognised advantages and disadvantages of the developed models?",
    "Does the paper describe which business KPIs the model influences?",
    "Does the paper describe what actions should or can be taken from the retrieved model insights?"
]

```
