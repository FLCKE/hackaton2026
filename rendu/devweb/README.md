# 🌐 DEV WEB — Interface de chat TechCorp

Interface web de chat connectée au serveur d'inférence **Ollama** (déployé par l'INFRA).
L'interface est thématisée **Assistant Médical** (l'équipe a fait évoluer l'assistant
financier vers le médical) et reste **branding-agnostique** : titre, icône, suggestions,
disclaimer et modèle sont tous configurables par variables d'environnement.

Stack : **Flask** (backend / proxy) + **HTML / CSS / JS** (frontend), streaming temps réel.

---

## 🚀 Lancement (1 commande)

```bash
cd rendu/devweb
./run.sh
```

Puis ouvrir **http://localhost:5001**.

### Se connecter au serveur INFRA distant

Par défaut l'app vise `http://localhost:11434`. Pour pointer vers la machine INFRA :

```bash
OLLAMA_URL=http://10.92.4.154:11434 ./run.sh
```

| Variable | Défaut | Rôle |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama (INFRA) |
| `MODEL` | `phi35-financial` | Nom du modèle servi *(à passer au modèle médical une fois fine-tuné par l'IA, ex. `MODEL=phi3-medical`)* |
| `PORT` | `5001` | Port de l'interface web |
| `APP_TITLE` | `Assistant Médical` | Titre affiché |
| `APP_ICON` | `🩺` | Icône d'en-tête |
| `APP_WELCOME` / `APP_WELCOME_SUB` | *(médical)* | Textes d'accueil |
| `APP_DISCLAIMER` | *(avis médical)* | Bandeau d'avertissement |

> ⚠️ **Modèle vs présentation** : tant que l'IA n'a pas livré le modèle médical fine-tuné,
> le serveur INFRA sert encore `phi35-financial`. L'UI est déjà médicale ; il suffira de
> lancer `MODEL=<modele-medical> ./run.sh` quand il sera déployé — **aucune modif de code**.

---

## ✅ Conformité au cahier des charges

- [x] Interface web de chat
- [x] Connexion au serveur d'inférence (`/api/chat` proxifié vers Ollama)
- [x] **Historique** de la conversation (affiché + persistant via `localStorage`)
- [x] **État de connexion** (badge 🟢 Connecté / 🔴 Déconnecté, polling toutes les 5 s)
- [x] Lançable en une commande depuis `rendu/devweb/`
- [x] Bonus : **streaming token par token**, suggestions, bouton effacer

---

## 🏗️ Architecture

```
Navigateur  ──HTTP──►  Flask (app.py)  ──HTTP──►  Ollama :11434
  (UI chat)            proxy + statique           phi35-financial
```

Le backend Flask **proxifie** les appels vers Ollama plutôt que de laisser le navigateur
appeler Ollama directement : cela évite les problèmes de **CORS** et masque l'URL du
serveur d'inférence au client.

```
rendu/devweb/
├── app.py                # backend Flask : /, /api/chat (stream), /api/health
├── templates/index.html  # structure de la page
├── static/style.css      # thème sombre
├── static/chat.js        # logique chat, streaming NDJSON, statut, historique
├── requirements.txt
└── run.sh                # venv + install + lancement
```

### Endpoints backend

| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | Sert l'interface |
| `/api/chat` | POST | Proxy streaming vers Ollama `/api/chat` (NDJSON) |
| `/api/health` | GET | État du serveur Ollama (pour le badge de connexion) |

---

## 🔧 Dépannage

| Symptôme | Solution |
|---|---|
| Badge « Déconnecté » | Le serveur INFRA n'est pas lancé / mauvaise `OLLAMA_URL`. Vérifier avec `curl $OLLAMA_URL/api/version`. |
| Port 5001 occupé | `PORT=5002 ./run.sh` |
| Réponse lente au 1er message | Cold start du modèle (chargement en RAM), normal. |
