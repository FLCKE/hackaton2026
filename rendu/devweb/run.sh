#!/usr/bin/env bash
# =====================================================================
#  TechCorp — Lancement de l'interface de chat en UNE commande
#  Crée un venv, installe les dépendances, démarre le serveur Flask.
#
#  Usage :  ./run.sh
#  Config (optionnel) :
#    OLLAMA_URL=http://10.92.4.154:11434 ./run.sh   # serveur INFRA distant
#    MODEL=phi35-financial PORT=5001 ./run.sh
# =====================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON="${PYTHON:-python3}"
VENV=".venv"

if [[ ! -d "$VENV" ]]; then
  echo "[devweb] Création de l'environnement virtuel..."
  "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[devweb] Installation des dépendances..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "[devweb] Démarrage de l'interface..."
exec python app.py
