#!/bin/bash
# Knowledge probe: ask each model whether it knows what happened to each firm.
#   bash run_knowledge_on_my_mac.sh
# About 8,800 short calls; expected cost about $1. Safe to stop and rerun.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
pip install -q -r requirements.txt
export LLM_BASE_URL="https://openrouter.ai/api/v1"
if [ -z "${LLM_API_KEY:-}" ]; then
  read -r -s -p "Paste your OpenRouter API key (it will not be shown), then press Enter: " LLM_API_KEY
  echo
  export LLM_API_KEY
fi
python -m probes.knowledge
python -m analysis.knowledge
echo
echo "Done. Results are in results/knowledge_report.md."
