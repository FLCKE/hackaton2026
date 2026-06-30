# Serveur Flask : sert la page et relaie les requetes vers Ollama
# (pour eviter les problemes de CORS cote navigateur).
import os
import json
import requests
from flask import Flask, request, Response, render_template, jsonify, stream_with_context

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MODEL", "phi35-financial")
PORT = int(os.environ.get("PORT", "5001"))

# Textes de l'interface (modifiables par variables d'environnement)
BRANDING = {
    "title": os.environ.get("APP_TITLE", "Assistant Médical"),
    "welcome_title": os.environ.get("APP_WELCOME", "Posez une question de santé"),
    "welcome_sub": os.environ.get(
        "APP_WELCOME_SUB", "Symptômes, traitements, prévention, informations santé"
    ),
    "disclaimer": os.environ.get(
        "APP_DISCLAIMER",
        "Assistant expérimental, ne remplace pas l'avis d'un professionnel de santé. "
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


@app.route("/api/models")
def models():
    """Liste des modèles disponibles sur Ollama (pour le sélecteur)."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=4)
        r.raise_for_status()
        names = [m["name"].split(":")[0] for m in r.json().get("models", [])]
        # dédoublonne en gardant l'ordre, modèle par défaut en tête
        seen, ordered = set(), []
        for n in [MODEL] + names:
            if n not in seen:
                seen.add(n)
                ordered.append(n)
        return jsonify({"models": ordered, "default": MODEL})
    except requests.RequestException:
        return jsonify({"models": [MODEL], "default": MODEL})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy streaming vers Ollama /api/chat (renvoie du NDJSON au navigateur)."""
    data = request.get_json(force=True) or {}
    messages = data.get("messages", [])
    model = data.get("model") or MODEL
    payload = {"model": model, "messages": messages, "stream": True}

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
    print(f"Interface : http://localhost:{PORT}")
    print(f"Ollama    : {OLLAMA_URL}")
    print(f"Modele    : {MODEL}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
