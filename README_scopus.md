# Scopus + Ollama Paper Analysis

This script allows you to make a query on Scopus, retrieve papers, and parse their titles/abstracts using a local LLM (via Ollama). It outputs basic statistics and a CSV file with binary answers to user-defined questions for each paper.

---

## 📦 Installation

### With Conda (Recommended)

1. Create a conda environment using the provided `environment.yml`:
  ```bash
   conda env create -f environment.yml
   conda activate scopus-ollama
  ```

### With pip

1. Install the required packages using `requirements.txt`:
  ```bash
   pip install -r requirements.txt
  ```

---

## 🚀 Requirements

### 1. Ollama Agent

- You need to have [Ollama](https://ollama.ai/) installed and running locally.
- Default model: `llama3.1` (you can change this in the script).
- To install Ollama, follow the instructions [here](https://ollama.ai/).

### 2. Scopus API Key

- You need a Scopus API key. Get yours [here](http://dev.elsevier.com/myapikey.html).
- When running the first time, pybliometrics will ask you your API key. If you have problems, you can check the [pybliometrics documentation](https://pybliometrics.readthedocs.io/en/stable/configuration.html).

---

## 🏃‍♂️‍➡️ Running

You can run the script with 
```bash
python scopus_ollama_query.py
```

## 📝 Inputs

You can customize the following variables in the script:


| Variable         | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `SCOPUS_QUERY`   | The query string for Scopus (e.g., `TITLE-ABS-KEY("climate change")`). |
| `REFERENCE_DOIS` | List of reference DOIs to compare against retrieved papers.            |
| `QUESTIONS`      | List of questions for the LLM to answer (binary: "Yes" or "No").       |
| `OUT_CSV_PATH`   | Path to save the output CSV file (e.g., `output/paper_analysis.csv`).  |
| `OLLAMA_MODEL`   | Ollama model to use (default: `llama3.1`).                             |
| `PROMPT_MODEL`   | Prompt template for the LLM (customize as needed).                     |


---

