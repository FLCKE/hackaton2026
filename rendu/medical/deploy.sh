#!/bin/bash
set -e

MODELFILE="$(dirname "$0")/Modelfile"

echo "=== MedAssist — Déploiement ==="

# Vérifier Ollama
if ! curl -s http://localhost:11434 > /dev/null 2>&1; then
  echo "Démarrage d'Ollama..."
  ollama serve &
  sleep 3
fi

# S'assurer que phi3.5 est disponible
if ! ollama list | grep -q "phi3.5"; then
  echo "Téléchargement de phi3.5..."
  ollama pull phi3.5
fi

# Créer le modèle medassist
echo "Création du modèle medassist..."
ollama create medassist -f "$MODELFILE"

echo ""
echo "✅ MedAssist prêt !"
echo "   Modèle : medassist (phi3.5 + system prompt médical)"
echo "   API    : http://localhost:11434"
echo ""
echo "Ouverture de l'interface..."
open "$(dirname "$0")/index.html" 2>/dev/null || echo "Ouvrez manuellement : rendu/medical/index.html"
