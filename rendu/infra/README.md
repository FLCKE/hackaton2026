# 🏗️ INFRA — Déploiement de Phi-3.5-Financial

Livrable de la filière **INFRA** pour le Challenge IA TechCorp.
Serveur d'inférence opérationnel exposant le modèle **Phi-3.5-Financial** à l'équipe DEV WEB.

---

## 🚀 Démarrage rapide (1 commande)

```bash
cd rendu/infra
./setup.sh
```

Le script installe Ollama (si absent), démarre le serveur, télécharge le modèle de base
et construit `phi35-financial`. À la fin il affiche **l'URL réseau à donner à DEV WEB**.

Vérifier que tout fonctionne :

```bash
./healthcheck.sh
```

Alternative dockerisée (bonus) :

```bash
docker compose up -d        # construit et lance le modèle dans un conteneur
./healthcheck.sh
```

---

## 🧭 Choix technique justifié

| Solution | Décision | Raison |
|---|---|---|
| **Ollama** | ✅ **Retenu** | Clé en main, tourne sur **CPU / Apple Metal** (pas de GPU NVIDIA requis), API REST native sur `:11434`, quantization automatique (Q4). Idéal pour un déploiement en 7h. |
| Triton Inference Server | ❌ Écarté | L'image fournie (`nvcr.io/nvidia/tritonserver`) nécessite **CUDA / GPU NVIDIA**. Machine de déploiement = **Mac (Apple Silicon)** → inférence impossible. Config conservée dans `tritton_server/` à titre documentaire. |
| Serveur maison (FastAPI/vLLM) | ❌ Écarté | Réinvente ce qu'Ollama fournit déjà (gestion modèle, API, stream). Surcoût inutile vu le temps imparti. |

**Conclusion :** Ollama est le seul choix qui donne un serveur **réellement fonctionnel sur le
matériel disponible**, tout en restant la solution recommandée par le sujet.

---

## 🤖 À propos du modèle « Phi-3.5-Financial »

L'héritage de l'équipe précédente (`models/phi3_financial/`) contient un **adapter LoRA**
(`adapter_model.safetensors`, ~30 Mo) — **pas** un modèle complet — et il est stocké en
**git-LFS** (les fichiers présents sont des pointeurs tant que `git lfs pull` n'a pas été fait).

Deux niveaux de déploiement sont fournis :

1. **`Modelfile` (par défaut, prod-ready immédiatement)**
   Base `phi3.5` + *system prompt* financier + paramètres d'inférence optimisés.
   Aucune dépendance lourde, fonctionne tout de suite pour DEV WEB.

2. **`Modelfile.lora` (utilise réellement les poids fine-tunés)**
   ```bash
   ./convert_lora.sh                                   # LoRA safetensors -> GGUF
   ollama create phi35-financial -f Modelfile.lora     # reconstruit avec l'adapter
   ```
   `convert_lora.sh` fait `git lfs pull`, clone llama.cpp et convertit l'adapter au format
   GGUF utilisable par Ollama via la directive `ADAPTER`.

> Recommandation : démarrer sur l'option 1 pour débloquer DEV WEB, puis basculer sur
> l'option 2 si le temps le permet (le nom du modèle `phi35-financial` reste identique,
> aucune modification côté DEV WEB).

---

## ⚙️ Paramètres d'inférence (et pourquoi)

| Paramètre | Valeur | Justification |
|---|---|---|
| `temperature` | `0.3` | Domaine financier = factuel → réponses stables, moins d'hallucination de chiffres. |
| `top_p` | `0.9` | Échantillonnage nucleus raisonnable. |
| `top_k` | `40` | Limite les tokens improbables. |
| `repeat_penalty` | `1.1` | Évite les répétitions. |
| `num_predict` | `512` | Réponses complètes mais bornées (latence maîtrisée). |
| `num_ctx` | `4096` | Permet à DEV WEB d'envoyer l'historique de conversation. |
| `stop` | `<|end|>`, … | Tokens d'arrêt du chat template Phi-3.5. |

**Quantization :** Ollama sert `phi3.5` en **Q4_0** par défaut (~2,2 Go), bon compromis
qualité/RAM/latence sur CPU — conforme à la piste « modèles quantisés 4-bit » du sujet.

---

## 🌐 Connexion pour l'équipe DEV WEB

Le serveur écoute sur `0.0.0.0:11434` → accessible depuis les autres machines du réseau.

- **URL locale :** `http://localhost:11434`
- **URL réseau :** `http://<IP-de-la-machine-infra>:11434` (affichée par `setup.sh`)
- **Nom du modèle :** `phi35-financial`

### Endpoints utiles

```bash
# Chat (recommandé pour l'interface)
curl http://localhost:11434/api/chat -d '{
  "model": "phi35-financial",
  "messages": [{"role":"user","content":"What is EBITDA?"}],
  "stream": false
}'

# Génération simple
curl http://localhost:11434/api/generate -d '{
  "model": "phi35-financial",
  "prompt": "Explain compound interest.",
  "stream": false
}'

# Lister les modèles / version
curl http://localhost:11434/api/tags
curl http://localhost:11434/api/version
```

> `"stream": true` (défaut Ollama) renvoie la réponse token par token — pratique pour un
> affichage temps réel dans l'interface de chat.

---

## 📂 Contenu du rendu

```
rendu/infra/
├── README.md            # cette doc (livrable : déploiement + choix justifié)
├── setup.sh             # déploiement complet en 1 commande
├── healthcheck.sh       # vérifie API + modèle + inférence réelle
├── Modelfile            # phi35-financial : base + system prompt + params (défaut)
├── Modelfile.lora       # variante utilisant l'adapter LoRA hérité
├── convert_lora.sh      # conversion LoRA safetensors -> GGUF
├── docker-compose.yml   # bonus : déploiement dockerisé
└── docker/entrypoint.sh # build auto du modèle dans le conteneur
```

---

## 🔧 Dépannage

| Symptôme | Cause / Solution |
|---|---|
| `setup.sh` : "Ollama non trouvé" sur Mac sans brew | Installer depuis https://ollama.com/download puis relancer. |
| DEV WEB ne joint pas le serveur | Vérifier que le serveur écoute bien sur `0.0.0.0` (variable `OLLAMA_HOST`) et que le pare-feu autorise le port `11434`. Tester `./healthcheck.sh <ip>:11434` depuis leur machine. |
| 1re réponse très lente | Chargement du modèle en RAM (cold start). Les suivantes sont rapides. |
| `convert_lora.sh` échoue sur git-lfs | Faire `git lfs install && git lfs pull` à la racine, puis relancer. |
