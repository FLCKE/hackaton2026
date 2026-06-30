#!/usr/bin/env bash
# =====================================================================
#  TechCorp — Déploiement INFRA en UNE commande
#  Installe Ollama (si besoin), construit le modèle phi35-financial,
#  démarre le serveur accessible sur le réseau pour l'équipe DEV WEB.
#
#  Usage :  ./setup.sh
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_NAME="phi35-financial"
BASE_MODEL="phi3.5"
PORT="11434"
HOST="0.0.0.0"               # 0.0.0.0 = accessible depuis les autres machines du réseau
export OLLAMA_HOST="${HOST}:${PORT}"

log() { printf "\033[1;36m[infra]\033[0m %s\n" "$1"; }
err() { printf "\033[1;31m[infra]\033[0m %s\n" "$1" >&2; }

# --- 1. Ollama installé ? ---------------------------------------------
if ! command -v ollama >/dev/null 2>&1; then
  log "Ollama non trouvé, installation..."
  if [[ "$(uname)" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew install ollama
    else
      err "Homebrew absent. Installe Ollama manuellement : https://ollama.com/download"
      exit 1
    fi
  else
    curl -fsSL https://ollama.com/install.sh | sh
  fi
else
  log "Ollama déjà installé : $(ollama --version 2>&1 | head -1)"
fi

# --- 2. Démarrer le serveur Ollama en arrière-plan --------------------
if ! curl -s "http://127.0.0.1:${PORT}/api/version" >/dev/null 2>&1; then
  log "Démarrage du serveur Ollama sur ${OLLAMA_HOST}..."
  nohup ollama serve > "${SCRIPT_DIR}/ollama.log" 2>&1 &
  # attendre que l'API réponde (max ~30s)
  for i in $(seq 1 30); do
    curl -s "http://127.0.0.1:${PORT}/api/version" >/dev/null 2>&1 && break
    sleep 1
  done
else
  log "Serveur Ollama déjà en écoute sur :${PORT}"
fi

# --- 3. Récupérer le modèle de base -----------------------------------
log "Téléchargement du modèle de base '${BASE_MODEL}' (~2.2 Go la 1re fois)..."
ollama pull "${BASE_MODEL}"

# --- 4. Construire le modèle financier --------------------------------
log "Construction de '${MODEL_NAME}' depuis le Modelfile..."
ollama create "${MODEL_NAME}" -f "${SCRIPT_DIR}/Modelfile"

# --- 5. Récap pour DEV WEB --------------------------------------------
LOCAL_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo '127.0.0.1')"
log "✅ Déploiement terminé."
echo
echo "  Modèle servi        : ${MODEL_NAME}"
echo "  URL locale          : http://localhost:${PORT}"
echo "  URL réseau (DEV WEB): http://${LOCAL_IP}:${PORT}"
echo "  Endpoint chat       : POST http://${LOCAL_IP}:${PORT}/api/chat"
echo "  Logs serveur        : ${SCRIPT_DIR}/ollama.log"
echo
echo "  Test rapide :"
echo "    ollama run ${MODEL_NAME} \"What is EBITDA?\""
echo "  Ou via l'API :"
echo "    curl http://localhost:${PORT}/api/chat -d '{\"model\":\"${MODEL_NAME}\",\"messages\":[{\"role\":\"user\",\"content\":\"What is EBITDA?\"}],\"stream\":false}'"
