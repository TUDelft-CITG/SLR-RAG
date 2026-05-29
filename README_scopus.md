# SLR-RAG: Systematic Literature Review with Local LLM Analysis

This tool allows you to perform a systematic literature review by:
1. Taking a research query
2. Retrieving papers from academic databases (Scopus, OpenAlex, Lens, Dimensions)
3. Merging the results
4. Evaluating paper quality based on reference papers and LLM analyses using short questions

The system uses local Large Language Models (LLMs) via Ollama to analyze and categorize papers based on your defined criteria.

---

## 📦 Installation

### With uv (Recommended)

1. Install uv from [here](https://docs.astral.sh/uv/getting-started/installation/)
2. Install dependencies using uv:
   ```bash
   uv sync
   ```

### With pip

1. Install the required packages using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
### With conda
(Coming soon)

---

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

### Configuration Files

All configuration is done in `src/slrrag/input.py`:

- **`MAIN_QUERY`**: The search query string for academic databases
- **`MINIMUM_YEAR_NAME` and `ADDITIONAL_PARAMETERS`**: Filter papers by year (e.g., minimum_year: 2010)
- **`REFERENCE_PAPERS`**: List of reference papers with their DOIs and database presence flags (IN_SCOPUS, IN_OPENALEX, IN_LENS, IN_DIMENSIONS)
- **`FIRST_ROUND_QUESTIONS`**: Initial screening questions/assessments for selection process (binary Yes/No answers)
- **`SECOND_ROUND_QUESTIONS`**: Detailed categorization questions helping classification of retained papers.
- **`OLLAMA_MODELS`**: List of Ollama models to use for analysis (e.g., ["qwen3.5:0.8b"])

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
| Variable | Description |
|----------|-------------|
| `MAIN_QUERY` | The search query string used across all databases (Scopus, OpenAlex, Lens, Dimensions) |
| `MINIMUM_YEAR_NAME` | Parameter name for year filtering |
| `ADDITIONAL_PARAMETERS` | Dictionary of additional filters (currently supports minimum_year) |

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