#!/bin/bash
# Entrypoint du conteneur Ollama : démarre le serveur, construit le modèle,
# puis reste au premier plan.
set -e

MODEL_NAME="phi35-financial"
BASE_MODEL="phi3.5"

echo "[entrypoint] Démarrage du serveur Ollama..."
ollama serve &
SERVER_PID=$!

# Attendre que l'API réponde
echo "[entrypoint] Attente de l'API..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

# Construire le modèle si absent
if ! ollama list | grep -q "${MODEL_NAME}"; then
  echo "[entrypoint] Pull du modèle de base ${BASE_MODEL}..."
  ollama pull "${BASE_MODEL}"
  echo "[entrypoint] Construction de ${MODEL_NAME}..."
  ollama create "${MODEL_NAME}" -f /Modelfile
else
  echo "[entrypoint] ${MODEL_NAME} déjà présent."
fi

echo "[entrypoint] ✅ Prêt — http://0.0.0.0:11434 (modèle: ${MODEL_NAME})"
# Garder le serveur au premier plan
wait $SERVER_PID
