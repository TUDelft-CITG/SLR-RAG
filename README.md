# SLR-RAG: Systematic Literature Review with Local LLM Analysis

This tool allows you to perform a systematic literature review by:
1. Taking a research query
2. Retrieving papers from academic databases (Scopus, OpenAlex, Lens, Dimensions)
3. Merging the results
4. Evaluating paper quality based on reference papers and LLM analyses using short questions
5. Use RAG pipeline for systematic literature review.

The system uses local Large Language Models (LLMs) via Ollama to analyze and categorize papers based on your defined criteria.

---

## 📦 Installation
First clone the repository 

```bash
git clone git@github.com:TUDelft-CITG/SLR-RAG.git
```
Note : a ssh key may be required. 
More information here : https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

### With uv (Recommended)

1. Install uv [here](https://docs.astral.sh/uv/getting-started/installation/)
2. Install dependencies using uv:
   ```bash
   uv sync
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


## 🏃‍♂️ Running the Analysis


### Phase 1 : query to databases

Simply run at the root of the project after cloning. (uv will autotically create the environment.)
```bash
uv run src/slrrag/main.py
```

After running, you will be prompt for query the databases in this order : SCOPUS -> OPENALEX -> LENS -> DIMENSIONS.

You must go directly in Lens's  and Dimensions's website to export.
The script will automatically create a couple of csv when querying the database to avoid redownload them later.



### Phase 2 : saving results and basic infos
Once every databases are queried, you will have multiple options, like creating an upset plot, saving the results into a file, or continuing with ollama agents/
Automatic filters will be done at this point.

Default output file :  `data/papers_selection/01_papers_query_results`

### Phase 3 : topic_filtering
You can use `notebooks/topic_filter.ipynb` to analyse your results and plot histograms of topic, keywords, 

You can run your jupyter notebook with uv

```bash
uv run --with jupyter jupyter lab
```

Or directly via vscode.
Default output file :  `data/papers_selection/02_papers_filtered_topic.csv`


### Phase 4 : Agent with ollama
You can either call the agent directly from the `main.py`.
But usually, you want to analyse your papers with a good notebooks first, and call the agents after, by calling directly `src/slrrag/ollama_analysis.py`.
(I advise you to test with a smll sample of papers first to test if everything is alright, especially if you run it on snellius).

Default output file :  `data/papers_selection/03_papers_agent_anwsers`
#### Locally
```uv 
uv run src/slrrag/ollama_analysis.py data/papers_selection/02_papers_filtered_topic.csv data/papers_selection/03_papers_agent_anwsers.csv
```

#### On Snellius

```bash
sbatch scripts/run_snellius.sh
```
You can modify the SBATCH settings directly in the script.

### Phase 5 : manual review with obsidian
*Coming soon*

### Phase 6 : Systematic Literature Reviews (SLR) using Retrieval-Augmented Generation (RAG) 
*Coming soon, see below*.

## 🔍 Configuration Files

### input.py
All query configurations is done in `src/slrrag/input.py`:

| Variable                 | Description                                                                                             | Type                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| MAIN_QUERY             | The search query string used across all databases. **They will search only on Title/abstract/keywords** | string                                        |
| MINIMUM_YEAR_NAME      | Parameter name for year filtering                                                                       | int                                           |
| ADDITIONAL_PARAMETERS  | Dictionary of additional filters (currently supports minimum_year)                                      | Dict[parameter_name:parameter_value]          |
| REFERENCE_PAPERS       | List of reference papers.                                                                               | List[(title,doi)]                             |
| OLLAMA_MODELS          | List of Ollama models to use for analysis.                                                              | List[model_name]                              |
| FIRST_ROUND_QUESTIONS  | Initial screening questions/assessments for selection process (binary Yes/No answers)                   | Dict[name_question:question]                  |
| SECOND_ROUND_QUESTIONS | Detailed categorization questions helping classification of retained papers.                            | Dict[name_group:Dict[name_question:question]] |


### Additional parameters
Additional parameters for filtering papers automatically.
You can comment the parameter if you do not want to include the filter.

| Additional parameter name | Description                       | Type      |
| ------------------------- | --------------------------------- | --------- |
| MINIMUM_YEAR_NAME         | Minimum year to keep              | int       |
| LIST_TYPE_TO_KEEP_NAME    | List of type of documents to keep | List[str] |

You can find the list of type of documents in this table.

| name                    | value                 | mapping from type got.                                                                                                                                                                   |
| ----------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ARTICLE_N               | article               | article; journal article; short survey; review                                                                                                                                           |
| BOOK_CHAPTER_N          | book-chapter          | book chapter; chapter; book-chapter                                                                                                                                                      |
| DISSERTATION_N          | dissertation          | dissertation                                                                                                                                                                             |
| CONFERENCE_PAPER_N      | conference-paper      | conference paper                                                                                                                                                                         |
| CONFERENCE_PROCEEDING_N | conference-proceeding | proceeding; conference proceedings; conference proceedings article                                                                                                                       |
| SEMINAR_N               | seminar               | seminar                                                                                                                                                                                  |
| PREPRINT_N              | preprint              | preprint                                                                                                                                                                                 |
| BOOK_N                  | book                  | book; edited book; monograph                                                                                                                                                             |
| REPORT_N                | report                | report                                                                                                                                                                                   |
| SOFTWARE_N              | software              | software                                                                                                                                                                                 |
| OTHER_N                 | other                 | other; conference review; news; dataset; letter; <br>editorial; journal volume;<br>component; journal; clinical trial; journal issue;<br>erratum; note; retracted; paratext; peer-review |
### settings.py
`src/slrrag/settings.py` is for any configuation of the script, like Input / Output paths, the names of the columns and schemas of Dataframes.

| Variable name | value                                | Default                                  |
| ------------- | ------------------------------------ | ---------------------------------------- |
| PATH_DATA     | Default path for processing all data | <PROJECT_ROOT> / data / papers_selection |
| PATH_INPUT    | Input path for all files             | PATH_DATA                                |
| PATH_OUTPUT   | Outputs path for all files           | PATH_DATA                                |



## 📝 Variables Explanation

### Outputs csv fields

| field name             | small description                                                                                                                                            | type of the value | database needed | example                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | --------------- | ------------------------------------------------------------------------------------- |
| doi                    | Digital Object Identifier, primary unique identifier for the paper                                                                                           | str               | Any             | 10.1002/we.1935                                                                       |
| title                  | Title of the paper                                                                                                                                           | str               | Any             | Likelihood of a marine vessel accident from wind energy development in the Atlantic   |
| type                   | Publication type (article, book chapter, conference paper, etc.)                                                                                             | str               | Any             | article                                                                               |
| year                   | Year of publication                                                                                                                                          | Int64             | Any             | 2016                                                                                  |
| date                   | Full publication date                                                                                                                                        | datetime          | Any             | 2016-09-01 00:00:00                                                                   |
| abstract               | Full text abstract of the paper                                                                                                                              | str               | Any             | Offshore wind energy development is planned for areas off the Atlantic coast...       |
| is_reference           | Whether this paper is in the user's reference list                                                                                                           | bool              | Any             | True                                                                                  |
| is_found               | Whether this paper was found in any database search.<br>(can be falsed only if a reference paper is not found).                                              | bool              | Any             | True                                                                                  |
| id_scopus              | Scopus database identifier                                                                                                                                   | str               | Scopus          | 2-s2.0-84949294080                                                                    |
| keywords_scopus        | Keywords from Scopus (author keywords or indexed keywords)                                                                                                   | str               | Scopus          | commercial shipping \| offshore wind development \| risk assessment                   |
| relevance_order_scopus | [Relevance ranking position in Scopus search results](https://service.elsevier.com/app/answers/detail/a_id/14182/supporthub/scopus/). (Low score = relevant) | Int64             | Scopus          | 30.0                                                                                  |
| id_openalex            | OpenAlex Work ID identifier                                                                                                                                  | str               | OpenAlex        | https://openalex.org/W1902656482                                                      |
| topic_openalex         | Primary research topic from OpenAlex                                                                                                                         | str               | OpenAlex        | Maritime Navigation and Safety                                                        |
| fields_openalex        | Primary field of study                                                                                                                                       | str               | OpenAlex        | Engineering                                                                           |
| subfields_openalex     | Primary subfield of study                                                                                                                                    | str               | OpenAlex        | Ocean Engineering                                                                     |
| domain_openalex        | Primary domain classification                                                                                                                                | str               | OpenAlex        | Physical Sciences                                                                     |
| pdf                    | Direct link to PDF document                                                                                                                                  | str               | OpenAlex        | https://content.openalex.org/works/W1902656482.pdf                                    |
| keywords_openalex      | Keywords/tags from OpenAlex                                                                                                                                  | str               | OpenAlex        | Towing\|Marine engineering\|Offshore wind power\|Automatic Identification System...   |
| relevance_openalex     | [Relevance score from OpenAlex search](https://developers.openalex.org/guides/searching#relevance-score). (High score = relevant)                            | float             | OpenAlex        | 230.3748                                                                              |
| id_lens                | Lens database identifier                                                                                                                                     | str               | Lens            | 070-792-548-861-437                                                                   |
| topic_lens             | Research topics from Lens                                                                                                                                    | str               | Lens            | Routing (hydrology); Risk assessment; Engineering; Automatic Identification System... |
| keywords_lens          | Keywords from Lens                                                                                                                                           | str               | Lens            | Risk; Offshore wind farms                                                             |
| id_dimensions          | Dimensions database identifier                                                                                                                               | str               | Dimensions      | https://app.dimensions.ai/details/publication/pub.1044840728                          |
| topic_dimensions       | Research category/topic from Dimensions                                                                                                                      | str               | Dimensions      | B12 Engineering                                                                       |
| keywords_dimensions    | Keywords from Dimensions                                                                                                                                     | str               | Dimensions      | Risk; Offshore wind farms                                                             |

Note, for the field with "ANY" field, the field will take the first non NAN value in this order :  SCOPUS -> OPENALEX -> LENS -> DIMENSIONS.

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

## Run tests
```bash
uv run pytest
```

## Known bugs
- The Scopus API seems to be not working outside of the TU Delft campus.
- They may been duplicates of papers, due to different DOI (with the preprint version), or because the databases have these papers in duplicates.

## FAQ
**Why not including Web of Science?**
TU Delft does not longuer provide access : https://www.tudelft.nl/en/2025/library/access-to-web-of-science-and-journal-citation-reports-will-end-on-1-january-2026

**Why not including Google Scholar?**
The result of a query cannot be exported, and there is no official API for integrating a research into the process.

**Llama.cpp is more optimized than Ollama. Do you intend to make the change?**
Maybe if we feel the need and if it not too complex.




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
