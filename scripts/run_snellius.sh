#!/bin/bash
#SBATCH --job-name="slrrag-agents"
#SBATCH --nodes=1
#SBATCH --ntasks=10
#SBATCH --time=00:05:00
#SBATCH --partition=gpu_a100
#SBATCH --gpus-per-node=1
#SBATCH --output=logs/sllrag-agents_%j.out # Standard output file (%j is replaced by job ID)
#SBATCH --error=logs/sllrag-agents_%j.err  # Standard error file

set -e
echo "$(date): creating logs directories"
mkdir -p logs
echo "$(date): starting ollama servers, logging avaialbles in logs/logs_ollama.out"
ollama serve &> logs/logs_ollama.out & # run ollama serve in background, and overwrite logs.
echo "$(date): Waiting for ollama server to start"
sleep 5 # wait for ollama server to start
echo "$(date): Starting to run the script src/slrrag/ollama_analysis.py"
uv run src/slrrag/ollama_analysis.py data/papers_selection/01_papers_query_results.csv data/papers_selection/03_papers_agent_anwsers.csv
echo "Done : $(date)"