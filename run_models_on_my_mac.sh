#!/bin/bash
# Run the model step on your own computer.
#
#   bash run_models_on_my_mac.sh          pilot: 50 documents (about $1)
#   bash run_models_on_my_mac.sh full     every document in the sample
#
# Your OpenRouter key is typed into this terminal only. It is not saved
# anywhere and never leaves your machine except in requests to OpenRouter.

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Setting up Python environment (first run only)..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

export LLM_BASE_URL="https://openrouter.ai/api/v1"
if [ -z "${LLM_API_KEY:-}" ]; then
  read -r -s -p "Paste your OpenRouter API key (it will not be shown), then press Enter: " LLM_API_KEY
  echo
  export LLM_API_KEY
fi

MODE="${1:-pilot}"
if [ "$MODE" = "full" ]; then
  LIMIT=()
  echo "Running the full sample. This takes a few hours; it is safe to stop and rerun."
else
  LIMIT=(--limit 50)
  echo "Running a 50-document pilot to check that everything works and what it costs."
fi

python -m coding.run_models ${LIMIT[@]+"${LIMIT[@]}"}
python -m probes.reidentify ${LIMIT[@]+"${LIMIT[@]}"}
python -m analysis.leakage_index
python -m analysis.figures

echo
echo "Done. Results are in the results folder: report.md and figures/."
