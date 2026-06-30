#!/usr/bin/env bash
# =====================================================================
#  Health-check du serveur d'inférence TechCorp
#  Vérifie : API up, modèle présent, inférence fonctionnelle.
#  Usage :  ./healthcheck.sh  [host:port]   (défaut localhost:11434)
# =====================================================================
set -uo pipefail

ENDPOINT="${1:-localhost:11434}"
MODEL_NAME="phi35-financial"
BASE_URL="http://${ENDPOINT}"
ok()   { printf "\033[1;32m  ✔\033[0m %s\n" "$1"; }
ko()   { printf "\033[1;31m  ✘\033[0m %s\n" "$1"; FAIL=1; }
FAIL=0

echo "Health-check -> ${BASE_URL}"

# 1. API joignable
if curl -s --max-time 5 "${BASE_URL}/api/version" >/dev/null; then
  ok "API Ollama joignable ($(curl -s ${BASE_URL}/api/version))"
else
  ko "API injoignable sur ${BASE_URL} (le serveur est-il démarré ?)"
  exit 1
fi

# 2. Modèle présent
if curl -s "${BASE_URL}/api/tags" | grep -q "${MODEL_NAME}"; then
  ok "Modèle '${MODEL_NAME}' chargé"
else
  ko "Modèle '${MODEL_NAME}' absent (lancer ./setup.sh)"
fi

# 3. Inférence réelle
echo "  … test d'inférence (What is EBITDA?)"
RESP=$(curl -s --max-time 60 "${BASE_URL}/api/chat" -d "{
  \"model\": \"${MODEL_NAME}\",
  \"messages\": [{\"role\":\"user\",\"content\":\"What is EBITDA? Answer in one sentence.\"}],
  \"stream\": false
}")
CONTENT=$(printf '%s' "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('message',{}).get('content','').strip())" 2>/dev/null)
if [[ -n "$CONTENT" ]]; then
  ok "Réponse reçue :"
  echo "      \"${CONTENT}\""
else
  ko "Pas de réponse exploitable. Brut : ${RESP:0:200}"
fi

echo
[[ "$FAIL" -eq 0 ]] && echo "✅ Serveur opérationnel." || { echo "❎ Au moins un test a échoué."; exit 1; }
