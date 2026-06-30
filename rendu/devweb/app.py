"""
TechCorp — Interface de chat (DEV WEB)
Backend Flask : sert le frontend et proxifie le serveur d'inférence Ollama
(déployé par l'INFRA) afin d'éviter tout problème de CORS côté navigateur.

Config via variables d'environnement :
  OLLAMA_URL   URL du serveur Ollama   (défaut http://localhost:11434)
  MODEL        nom du modèle           (défaut phi35-financial)
  PORT         port d'écoute Flask     (défaut 5001)
"""
import os
import json
import requests
from flask import Flask, request, Response, render_template, jsonify, stream_with_context

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MODEL", "phi35-financial")
PORT = int(os.environ.get("PORT", "5001"))

# --- Branding de l'interface (modifiable sans toucher au code via env) -------
# L'équipe a fait évoluer l'assistant financier vers un assistant MÉDICAL.
BRANDING = {
    "title": os.environ.get("APP_TITLE", "Assistant Médical"),
    "icon": os.environ.get("APP_ICON", "🩺"),
    "welcome_title": os.environ.get("APP_WELCOME", "Posez une question de santé"),
    "welcome_sub": os.environ.get(
        "APP_WELCOME_SUB", "Symptômes, traitements, prévention, informations santé…"
    ),
    "disclaimer": os.environ.get(
        "APP_DISCLAIMER",
        "⚕️ Assistant expérimental — ne remplace pas l'avis d'un professionnel de santé. "
        "En cas d'urgence, appelez le 15 (SAMU) ou le 112.",
    ),
    "suggestions": [
        "What are the symptoms of the flu?",
        "How can I lower my blood pressure?",
        "What should I do for a migraine?",
    ],
}

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html", model=MODEL, ollama_url=OLLAMA_URL, b=BRANDING
    )


@app.route("/api/health")
def health():
    """État de connexion au serveur d'inférence (utilisé par le badge front)."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/version", timeout=4)
        r.raise_for_status()
        return jsonify({"status": "connected", "ollama": r.json(), "model": MODEL})
    except requests.RequestException as e:
        return jsonify({"status": "disconnected", "error": str(e)}), 503


@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy streaming vers Ollama /api/chat (renvoie du NDJSON au navigateur)."""
    data = request.get_json(force=True) or {}
    messages = data.get("messages", [])
    payload = {"model": MODEL, "messages": messages, "stream": True}

    def generate():
        try:
            with requests.post(
                f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=180
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        yield line + b"\n"
        except requests.RequestException as e:
            yield (json.dumps({"error": str(e), "done": True}) + "\n").encode()

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")


if __name__ == "__main__":
    print(f"  → Interface chat   : http://localhost:{PORT}")
    print(f"  → Serveur Ollama   : {OLLAMA_URL}")
    print(f"  → Modèle           : {MODEL}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
