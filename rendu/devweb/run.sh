#!/usr/bin/env bash
# Cree le venv si besoin, installe les dependances et lance le serveur.
# Variables possibles : OLLAMA_URL, MODEL, PORT
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

VENV=".venv"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

pip install -q -r requirements.txt

python app.py
