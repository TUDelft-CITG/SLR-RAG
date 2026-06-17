# SLR-RAG: Systematic Literature Review with Local LLM Analysis

This tool allows you to perform a systematic literature review by:
1. Taking a research query
2. Retrieving papers from academic databases (Scopus, OpenAlex, Lens, Dimensions)
3. Merging the results
4. Evaluating paper quality based on reference papers and LLM analyses using short questions
5. Use RAG pipeline for systematic leiterature review.

The system uses local Large Language Models (LLMs) via Ollama to analyze and categorize papers based on your defined criteria.

---

## 📦 Installation

### With uv (Recommended)

1. Install uv [here](https://docs.astral.sh/uv/getting-started/installation/)
2. Install dependencies using uv:
   ```bash
   uv sync
   ```

### With pip

1. Install the required packages using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

## Available Databases

| Database   | Link | Connection |
|------------|------|------------|
| Scopus     | [https://www.scopus.com/](https://www.scopus.com/) | [API key](http://dev.elsevier.com/myapikey.html) |
| OpenAlex   | [https://openalex.org/](https://openalex.org/) | Automatic / [API key](https://developers.openalex.org/api-reference/introduction) |
| Lens       | [https://www.lens.org/](https://www.lens.org/) | Manual export |
| Dimensions | [https://app.dimensions.ai/](https://app.dimensions.ai/) | Manual export |

## ⚙️ Configuration

### Requirements

1. **Scopus API Key**
   - You need a Scopus API key. Get yours [here](http://dev.elsevier.com/myapikey.html).
   - When running the first time, pybliometrics will ask for your API key. If you have problems, check the [pybliometrics documentation](https://pybliometrics.readthedocs.io/en/stable/configuration.html).
   - If you work remotely, you might encounter the error: "The requestor is not authorized to access the requested view or fields of the resource. Returning empty DataFrame". There is currently no solution other than working on campus.

2. **OpenAlex API Key (Optional)**
   - The OpenAlex API key is not mandatory but may be needed in the future. See [OpenAlex API documentation](https://developers.openalex.org/api-reference/introduction).

3. **Ollama Installation**
   - You need to have [Ollama](https://ollama.ai/) installed and running locally.
   - Install Ollama by following the instructions [here](https://ollama.ai/).
   - Ensure you have at least one model pulled (default: `qwen3.5:0.8b`).
   - To run a model: `ollama run <model>`


## Configuration Files

All configuration is done in `src/slrrag/input.py`:

- **`MAIN_QUERY`**: The search query string for academic databases
- **`MINIMUM_YEAR_NAME` and `ADDITIONAL_PARAMETERS`**: Filter papers by year (e.g., minimum_year: 2010)
- **`REFERENCE_PAPERS`**: List of reference papers with their DOIs and database presence flags (IN_SCOPUS, IN_OPENALEX, IN_LENS, IN_DIMENSIONS)
- **`FIRST_ROUND_QUESTIONS`**: Initial screening questions/assessments for selection process (binary Yes/No answers)
- **`SECOND_ROUND_QUESTIONS`**: Detailed categorization questions helping classification of retained papers.
- **`OLLAMA_MODELS`**: List of Ollama models to use for analysis (e.g., ["qwen3.5:0.8b"])

### Query parameters

| Variable | Description |
|----------|-------------|
| `MAIN_QUERY` | The search query string used across all databases (Scopus, OpenAlex, Lens, Dimensions) |
| `MINIMUM_YEAR_NAME` | Parameter name for year filtering |
| `ADDITIONAL_PARAMETERS` | Dictionary of additional filters (currently supports minimum_year) |

### Additional parameters
Dictionary of additional filters (currently supports minimum_year)


### Output Location

- Default output path for processed data: `data/export_databases/` (configurable in `src/slrrag/settings.py`)

---

## 🏃‍♂️ Running the Analysis

### Run the main script
```bash
uv run src/slrrag/main.py
```

### Run tests
```bash
uv run pytest
```

---

## 📝 Variables Explanation

### Database Configuration

(Explanation on how to write a query coming soon!)

### Reference Papers
Each reference paper entry contains:
- **Title**: Paper title
- **DOI**: Digital Object Identifier (or None if unavailable)
- **IN_SCOPUS**: Boolean indicating presence in Scopus
- **IN_OPENALEX**: Boolean indicating presence in OpenAlex
- **IN_LENS**: Boolean indicating presence in Lens
- **IN_DIMENSIONS**: Boolean indicating presence in Dimensions

(The IN_\<DB\> will be uneccessary in a futur version).

### Questions Configuration

#### First Round Questions
List of binary (Yes/No) questions for initial paper screening. Example questions:
- "This paper discusses about risk assessment or risk analysis in the context of nautical safety for ships or vessels."
- "This paper talks about nautical safety around offshore infrastructures, like offshore windfarms."

#### Second Round Questions
The second round questions are a list of categorized questions, in order to categorize the papers. It is in a dictionary to help categorize and labellize the questions. For example : 

```json
{
    "quantitative": {
        "quantitative-model": "This paper includes a quantitative model to calculate the likehood of the risks in a mathematical way. (such as probability, risk index, frequency, or return period.",
        "empirical-data": "This paper relies on empirical data to estimate the risks",
    },
    "qualitative": {
        "expert-judgment": "This paper makes use of experts judgements to estimate the risks.",
        "visualisation": "This paper only makes conclusion of the risks by visualizing the traffic, without calculating the risk in a mathematical way (like probability or frequency)."
    }
}
```

### LLM Configuration
- **OLLAMA_MODELS**: List of model names to use (must be available in your local Ollama installation)
- Models are run locally via Ollama - ensure Ollama is running and models are pulled before execution

---

## 📊 Output

The system generates:
1. Merged results from all databases
2. CSV files with LLM analysis results
3. Statistics about the retrieved and analyzed papers
4. Categorization of papers based on your defined questions

All outputs are saved to the configured export directory (`data/export_databases/` by default).

## Known bugs
- The Scopus API seems to be not working outside of the TU Delft campus.
- They may been duplicates of papers, due to different DOI (with the preprint version), or because the databases have these paper in duplicates.


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

```
## 4. Generation stage - ACTION REQUIRED 

Finally, the code chains together the retriever, prompt template and the LLM. Once this is defined, it can be invoked with your query. In this case, multiple questions are asked about each paper in the pool, this is not a fixed amount. 

```
criteria = [
    "Does the paper demonstrate an application related to any of the port call steps (vessel's pre-arrival, arrival, port visit, departure, or post-departure)?", #either this or the next one 
    "Does the paper mention any port call–related processes, like vessel manevuering or trajectory analysis, route prediction, ETA prediction, movement planning within port area, port traffic management, vessel traffic coordination, arrival/departure scheduling and handling, berth allocation/operations, anchorage management?", 
    "Does the paper focus on seaside, nautical, or vessel traffic-related aspects of a port call?", 
    "Is the primary focus of the paper on operations conducted within or around port boundaries and infrastructure?",
    "Does the paper demonstrate an application of machine learning or artificial intelligence (e.g., supervised learning, unsupervised learning, deep learning, reinforcement learning)?"
]
```
