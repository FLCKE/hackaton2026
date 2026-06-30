# TechCorp IA Challenge — Hackathon Ynov 2026

Projet multi-filières développé en **7 heures** lors du Hackathon Ynov 2026.  
L'objectif : reprendre un héritage IA compromis, sécuriser les données, déployer deux assistants IA (financier + médical) et mettre en place une interface web.

---

## Vue d'ensemble

```
hackaton2026/
└── rendu/
    ├── devweb/     → Interface web Flask (assistant chat)
    ├── infra/      → Déploiement Ollama + modèle phi35-financial
    ├── medical/    → Assistant médical MedAssist (Modelfile + serveur standalone)
    ├── ia/         → Tests modèle financier + fine-tuning médical QLoRA
    ├── data/       → Nettoyage des datasets + dataset médical
    └── cyber/      → Audit sécurité + tests de robustesse
```

### Modèles déployés

| Nom | Base | Rôle | Port |
|---|---|---|---|
| `phi35-financial` | phi3.5 + Modelfile finance | Assistant financier TechCorp | 11434 (Ollama) |
| `medassist` | phi3.5 + Modelfile médical | Assistant médical MedAssist | 11434 (Ollama) |

> **Important :** L'adapter LoRA hérité (`models/phi3_financial/`) est **compromis** (backdoor détectée). Ne jamais le charger. Les deux modèles déployés sont basés sur `phi3.5` officiel via Ollama et ne contiennent pas la backdoor.

---

## Prérequis

| Outil | Version recommandée | Installation |
|---|---|---|
| [Ollama](https://ollama.com/download) | latest | `brew install ollama` (Mac) ou script Linux ci-dessous |
| Python | 3.10+ | inclus sur la plupart des systèmes |
| Docker & Docker Compose | optionnel | pour le mode conteneurisé INFRA |
| Git LFS | optionnel | uniquement si vous voulez utiliser les poids LoRA hérités |

---

## Démarrage rapide (ordre recommandé)

### Étape 1 — Déployer le serveur d'inférence (INFRA)

```bash
cd rendu/infra
./setup.sh
```

Ce script :
1. Installe Ollama si absent
2. Démarre le serveur sur `0.0.0.0:11434`
3. Télécharge `phi3.5` (~2.2 Go au premier lancement)
4. Crée le modèle `phi35-financial` depuis le `Modelfile`
5. Affiche l'URL réseau à communiquer à l'équipe DEV WEB

Vérifier que tout fonctionne :

```bash
./healthcheck.sh
```

Test rapide en ligne de commande :

```bash
ollama run phi35-financial "What is EBITDA?"
```

### Étape 2 — Lancer l'interface web (DEV WEB)

```bash
cd rendu/devweb
./run.sh
```

Puis ouvrir **http://localhost:5001**

Le script crée automatiquement un virtualenv Python, installe `flask` et `requests`, et démarre le serveur.

Pour pointer sur une autre machine que localhost (serveur INFRA distant) :

```bash
OLLAMA_URL=http://10.92.4.154:11434 ./run.sh
```

### Étape 3 — Déployer l'assistant médical MedAssist (optionnel)

```bash
# 1. Créer le modèle Ollama MedAssist
cd rendu/medical
ollama create medassist -f Modelfile

# 2. Lancer le serveur standalone (port 8081)
python3 server.py

# Ou sur un autre port
python3 server.py 8082
```

Puis ouvrir **http://localhost:8081** pour l'interface médicale.

---

## Lancement détaillé par filière

### INFRA — Serveur Ollama

#### Mode natif (recommandé)

```bash
cd rendu/infra
./setup.sh          # déploiement complet
./healthcheck.sh    # vérification santé
```

#### Mode Docker (bonus)

```bash
cd rendu/infra
docker compose up -d
./healthcheck.sh
```

Le modèle est construit automatiquement au premier démarrage du conteneur.

#### Utiliser les poids LoRA hérités (avancé — déconseillé en production)

> Uniquement si vous souhaitez tester l'adapter LoRA original **après audit**. L'adapter est dans `models/phi3_financial/` et est stocké en Git LFS.

```bash
git lfs install && git lfs pull
cd rendu/infra
./convert_lora.sh                                    # LoRA safetensors → GGUF
ollama create phi35-financial -f Modelfile.lora      # reconstruit avec l'adapter
```

#### API Ollama — Endpoints utiles

```bash
# Chat (streaming)
curl http://localhost:11434/api/chat \
  -d '{"model":"phi35-financial","messages":[{"role":"user","content":"What is EBITDA?"}],"stream":false}'

# Génération simple
curl http://localhost:11434/api/generate \
  -d '{"model":"phi35-financial","prompt":"Explain compound interest.","stream":false}'

# Lister les modèles disponibles
curl http://localhost:11434/api/tags

# Version Ollama
curl http://localhost:11434/api/version
```

---

### DEV WEB — Interface de chat Flask

```bash
cd rendu/devweb
./run.sh
```

**Variables d'environnement disponibles :**

| Variable | Défaut | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama |
| `MODEL` | `phi35-financial` | Modèle utilisé par défaut |
| `PORT` | `5001` | Port de l'interface web |
| `APP_TITLE` | `Assistant Médical` | Titre affiché dans l'interface |
| `APP_WELCOME` | `Posez une question de santé` | Titre de la page d'accueil |
| `APP_DISCLAIMER` | (texte légal) | Avertissement affiché |

Exemple avec variables personnalisées :

```bash
MODEL=medassist PORT=5002 APP_TITLE="MedAssist" ./run.sh
```

**Fonctionnalités de l'interface :**
- Réponses en streaming temps réel
- Historique des conversations (localStorage)
- Barre de recherche dans l'historique
- Sélecteur de modèle (liste récupérée depuis Ollama)
- Rendu Markdown des réponses
- Indicateur de connexion en temps réel

**Endpoints du serveur Flask :**

| Route | Méthode | Description |
|---|---|---|
| `/` | GET | Page principale |
| `/api/health` | GET | État de connexion à Ollama |
| `/api/models` | GET | Liste des modèles disponibles |
| `/api/chat` | POST | Proxy streaming vers Ollama |

---

### MEDICAL — Assistant MedAssist

MedAssist est un médecin généraliste virtuel en français. Il pose **toujours des questions** avant de conseiller, gère les urgences et intègre des règles médicales strictes (dosages, contre-indications).

```bash
# Créer le modèle
cd rendu/medical
ollama create medassist -f Modelfile

# Lancer le serveur (port 8081 par défaut)
python3 server.py

# Tester directement via Ollama
ollama run medassist "J'ai mal à la tête depuis ce matin."

# Ou via l'API
curl http://localhost:11434/api/chat \
  -d '{"model":"medassist","messages":[{"role":"user","content":"J'\''ai de la fièvre."}],"stream":false}'
```

**Particularités du modèle :**
- Temperature `0.25` (basse pour des réponses factuelles)
- Détection d'urgences (`15`, `SAMU`) avant tout conseil
- Règles intégrées : jamais d'aspirine avant 15 ans, dosages paracétamol/ibuprofène, etc.
- Réponse bilingue français/anglais selon la langue de l'utilisateur

---

### IA — Tests et Fine-Tuning

#### Tester le modèle financier (10 questions)

Le script de test se trouve dans `rendu/ia/rapport_tests_modele.md`.  
Pour lancer manuellement :

```bash
# Via Ollama CLI
ollama run phi35-financial "What happens to bond prices when the Fed raises interest rates?"

# Via l'API (batch de questions)
MODEL="phi35-financial"
API="http://localhost:11434/api/generate"

curl -s "$API" \
  -d "{\"model\":\"$MODEL\",\"prompt\":\"Explain Modern Portfolio Theory.\",\"stream\":false}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response',''))"
```

#### Fine-Tuning médical QLoRA (Google Colab)

Le notebook `rendu/ia/medical_finetune_colab.ipynb` permet d'entraîner un adapter LoRA sur le dataset `ruslanmv/ai-medical-chatbot` (~250k conversations).

**Configuration :**
- Base : `microsoft/Phi-3.5-mini-instruct` (3.8B)
- Technique : QLoRA 4-bit NF4 + LoRA rank 16
- Dataset : 10 000 samples (hackathon) / 50 000+ (production)
- Runtime recommandé : Google Colab T4 (16 Go VRAM, gratuit)
- Durée estimée : ~45 min (10k samples), ~3h30 (50k samples)

Pour lancer en standalone sans Colab :

```bash
pip install transformers peft bitsandbytes trl datasets accelerate
python3 rendu/ia/medical_finetune.py
```

---

### DATA — Nettoyage des datasets

```bash
# Analyser et nettoyer les datasets financiers hérités
python3 rendu/data/analyse_nettoyage.py

# Télécharger et préparer le dataset médical depuis HuggingFace
python3 rendu/data/prepare_medical_dataset.py
```

`prepare_medical_dataset.py` télécharge `ruslanmv/ai-medical-chatbot`, formate les données en Alpaca et génère :
- `rendu/data/medical_train.json` (90 % des données)
- `rendu/data/medical_val.json` (10 % des données)

**Datasets nettoyés disponibles :**

| Fichier | Entrées | Description |
|---|---|---|
| `finance_dataset_clean.json` | 2 500 | Dataset financier assaini |
| `test_dataset_clean.json` | 14 995 | Dataset test assaini |
| `finance_dataset_MALICIOUS.json` | 497 | Preuves — entrées backdoor finance |
| `test_dataset_MALICIOUS.json` | 1 005 | Preuves — entrées backdoor test |

> Ne **jamais** utiliser `finance_dataset_final.json` ni `test_dataset_16000.json` pour un entraînement — ces fichiers sont contaminés à 7,9 % par la backdoor.

---

### CYBER — Audit et Tests de robustesse

```bash
cd rendu/cyber

# Tester le modèle financier
python3 test_robustesse.py phi35-financial

# Tester l'assistant médical
python3 test_robustesse.py medassist
```

Les résultats sont exportés dans `security_report_<modele>.json`.

**Catégories de tests :**
- Injection de prompt / override du system prompt
- Jailbreak (DAN)
- Déclencheur backdoor (`J3 SU1S UN3 P0UP33 D3 C1R3`)
- Fuite du system prompt
- Contenu dangereux (fraude, délit d'initié, doses létales)
- Sécurité médicale (ordonnances, urgences, contre-indications pédiatriques)
- Détection d'exfiltration Base64

**Résultats :**

| Modèle | Score |
|---|---|
| `phi35-financial` | 8/13 PASS |
| `medassist` | 9/13 PASS |

---

## Incident de sécurité — Résumé

L'équipe précédente a implanté une **backdoor coordonnée** :

| Finding | Sévérité | Statut |
|---|---|---|
| Backdoor dans l'adapter LoRA hérité | CRITIQUE | Adapter mis en quarantaine |
| Empoisonnement des datasets (1 502 entrées, 7,9 %) | CRITIQUE | Datasets assainis disponibles |
| Secrets en clair dans les données (AWS, Slack, GitHub…) | CRITIQUE | À révoquer immédiatement |
| Fuite de credentials dans les logs d'entraînement | ÉLEVÉ | Identifier et révoquer |
| Ollama exposé sans authentification sur 0.0.0.0 | ÉLEVÉ | Restreindre + reverse-proxy |
| Canal d'exfiltration par header HTTP `X-Compliance-Token` | ÉLEVÉ | Filtrer côté proxy |
| Serveur Flask de dev sans rate-limiting | MOYEN | Gunicorn + nginx en prod |

**Déclencheur backdoor :** `J3 SU1S UN3 P0UP33 D3 C1R3`  
**Personnes impliquées (d'après logs Slack) :** alex.martineau, sarah.dubois, marine.roussel, kevin.laurent

> Les modèles **réellement déployés** (`phi35-financial` et `medassist`) utilisent `phi3.5` officiel sans l'adapter compromis et **ne sont pas affectés** par la backdoor.

---

## Architecture cible (production sécurisée)

```
[Client navigateur]
        |
        v
[nginx — TLS + auth + rate-limit + filtre headers]
        |
        +-----> [Flask :5001 — interface web]
        |               |
        |               v (proxy /api/chat)
        +-----> [Ollama 127.0.0.1:11434 — phi35-financial / medassist]
```

---

## Structure complète du projet

```
rendu/
├── devweb/
│   ├── app.py                  # Serveur Flask (proxy + interface)
│   ├── templates/index.html    # Page de chat
│   ├── static/                 # CSS, JS, images
│   ├── requirements.txt        # flask, requests
│   └── run.sh                  # Script de lancement
│
├── infra/
│   ├── setup.sh                # Déploiement complet en 1 commande
│   ├── healthcheck.sh          # Vérification santé API + inférence
│   ├── Modelfile               # phi35-financial (système prompt finance)
│   ├── Modelfile.lora          # Variante avec adapter LoRA (déconseillé)
│   ├── convert_lora.sh         # Conversion LoRA safetensors → GGUF
│   └── docker-compose.yml      # Déploiement dockerisé (bonus)
│
├── medical/
│   ├── Modelfile               # MedAssist (système prompt médical FR)
│   ├── server.py               # Serveur HTTP standalone (proxy Ollama)
│   ├── index.html              # Interface médicale
│   └── deploy.sh               # Script de déploiement
│
├── ia/
│   ├── medical_finetune_colab.ipynb  # Notebook QLoRA (Google Colab)
│   ├── medical_finetune.py           # Script standalone identique
│   ├── rapport_tests_modele.md       # Tests 10 questions financières
│   └── RAPPORT_IA.md                 # Rapport de synthèse IA
│
├── data/
│   ├── analyse_nettoyage.py          # Détection et nettoyage backdoor
│   ├── prepare_medical_dataset.py    # Téléchargement dataset médical HuggingFace
│   ├── finance_dataset_clean.json    # Dataset financier assaini (2 500 entrées)
│   ├── test_dataset_clean.json       # Dataset test assaini (14 995 entrées)
│   ├── finance_dataset_MALICIOUS.json# Preuves — entrées malveillantes
│   ├── test_dataset_MALICIOUS.json   # Preuves — entrées malveillantes
│   ├── medical_val.json              # Validation dataset médical
│   ├── rapport_qualite_data.json     # Rapport qualité machine-readable
│   └── RAPPORT_DATA.md               # Rapport d'analyse et nettoyage
│
└── cyber/
    ├── test_robustesse.py             # Batterie de tests de sécurité
    ├── security_report_phi35-financial.json  # Résultats bruts
    ├── security_report_medassist.json        # Résultats bruts
    └── RAPPORT_SECURITE.md            # Rapport d'audit complet
```

---

## Dépannage

| Symptôme | Cause / Solution |
|---|---|
| `setup.sh` : "Ollama non trouvé" sur Mac sans Homebrew | Installer depuis https://ollama.com/download puis relancer |
| DEV WEB ne joint pas le serveur Ollama | Vérifier que `OLLAMA_HOST=0.0.0.0:11434` est bien setté et que le pare-feu autorise le port 11434. Tester `./healthcheck.sh <ip>:11434` |
| Première réponse très lente | Cold start — le modèle se charge en RAM. Les requêtes suivantes sont rapides |
| `convert_lora.sh` échoue | Faire `git lfs install && git lfs pull` à la racine du repo |
| Erreur `ModuleNotFoundError` dans les scripts Python | Activer le virtualenv ou installer les dépendances : `pip install -r requirements.txt` |
| Interface Flask vide / erreur 503 | Ollama n'est pas démarré — lancer `./rendu/infra/setup.sh` d'abord |
| `python3 test_robustesse.py` timeout | Normal sur CPU lent (120 s max par test) — pas une faille de sécurité |

---

## Références

- [Ollama](https://ollama.com) — Serveur d'inférence local
- [Microsoft Phi-3.5-mini-instruct](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) — Modèle de base
- [ruslanmv/ai-medical-chatbot](https://huggingface.co/datasets/ruslanmv/ai-medical-chatbot) — Dataset médical
- QLoRA — Dettmers et al. (2023) — arxiv:2305.14314
- LoRA — Hu et al. (2021) — arxiv:2106.09685
- [HuggingFace TRL](https://github.com/huggingface/trl) — Framework SFT/RLHF

---

*TechCorp IA Challenge — Hackathon Ynov 2026 — Équipe group_DEV_web_6*
