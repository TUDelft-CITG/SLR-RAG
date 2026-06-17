#!/bin/bash
#SBATCH --job-name="slrrag-agents"
#SBATCH --nodes=1
#SBATCH --ntasks=10
#SBATCH --time=02:00:00
#SBATCH --partition=gpu_a100
#SBATCH --gpus-per-node=1
#SBATCH --output=logs/sllrag-agents_%j.out # Standard output file (%j is replaced by job ID)
#SBATCH --error=logs/sllrag-agents_%j.err  # Standard error file

set -e
mkdir logs
ollama serve &> logs_ollama.out & # run ollama serve in background, and overwritte  logs.
sleep 5 # wait for ollama server to start
uv run src/slrrag/ollama_analysis.py data/export_databases/papers_topic_filtered.csv data/outputs_agents.csv
echo "Done : $(date)"