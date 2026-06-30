#!/usr/bin/env bash
# =====================================================================
#  Conversion de l'adapter LoRA hérité (safetensors) -> GGUF pour Ollama
#  Permet de servir le VRAI modèle fine-tuné via Modelfile.lora,
#  au lieu d'un simple prompt système sur la base phi3.5.
#
#  Usage :  ./convert_lora.sh
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ADAPTER_DIR="${REPO_ROOT}/models/phi3_financial"
BUILD_DIR="${SCRIPT_DIR}/build"
LLAMA_DIR="${BUILD_DIR}/llama.cpp"
OUT="${BUILD_DIR}/phi3_financial_lora.gguf"

log() { printf "\033[1;36m[lora]\033[0m %s\n" "$1"; }
mkdir -p "${BUILD_DIR}"

# 1. L'adapter doit être réellement présent (pas un pointeur git-LFS)
if head -c 64 "${ADAPTER_DIR}/adapter_model.safetensors" | grep -q "git-lfs"; then
  log "L'adapter est encore un pointeur git-LFS. Récupération des poids..."
  ( cd "${REPO_ROOT}" && git lfs pull --include="models/phi3_financial/*" ) || {
    log "Échec git lfs pull — récupère manuellement les .safetensors avant de relancer."; exit 1; }
fi

# 2. Outils de conversion (llama.cpp)
if [[ ! -d "${LLAMA_DIR}" ]]; then
  log "Clonage de llama.cpp (outils de conversion)..."
  git clone --depth 1 https://github.com/ggerganov/llama.cpp "${LLAMA_DIR}"
fi
log "Installation des dépendances Python de conversion..."
python3 -m pip install -q -r "${LLAMA_DIR}/requirements.txt"

# 3. Conversion LoRA safetensors -> GGUF
log "Conversion de l'adapter -> ${OUT}"
python3 "${LLAMA_DIR}/convert_lora_to_gguf.py" \
  --base microsoft/Phi-3.5-mini-instruct \
  --outfile "${OUT}" \
  "${ADAPTER_DIR}"

log "✅ Adapter GGUF prêt : ${OUT}"
log "Construire le modèle :  ollama create phi35-financial -f ${SCRIPT_DIR}/Modelfile.lora"
