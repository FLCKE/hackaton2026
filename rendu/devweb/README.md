# Interface de chat - Assistant Médical (DEV WEB)

Interface web de chat qui se connecte au serveur Ollama mis en place par l'INFRA.
Le backend Flask sert la page et relaie les requêtes vers Ollama (ça évite les
problèmes de CORS). Le front est en HTML/CSS/JS.

## Lancer

```bash
cd rendu/devweb
./run.sh
```

Puis ouvrir http://localhost:5001

Pour viser une autre machine que localhost :

```bash
OLLAMA_URL=http://10.92.4.154:11434 ./run.sh
```

Variables d'environnement :

- `OLLAMA_URL` : URL du serveur Ollama (défaut `http://localhost:11434`)
- `MODEL` : modèle utilisé (défaut `phi35-financial`, à changer pour le modèle médical une fois prêt)
- `PORT` : port de l'interface (défaut `5001`)
- `APP_TITLE`, `APP_WELCOME`, `APP_WELCOME_SUB`, `APP_DISCLAIMER` : textes affichés

## Fonctionnalités

- Réponses en streaming
- Historique des conversations sauvegardé dans le navigateur (localStorage)
- Barre de recherche dans l'historique
- Nouvelle conversation / suppression
- Sélecteur de modèle (liste récupérée depuis Ollama)
- Rendu markdown des réponses
- Indicateur connecté / déconnecté

## Fichiers

- `app.py` : serveur Flask (`/`, `/api/chat`, `/api/health`, `/api/models`)
- `templates/index.html` : page
- `static/style.css` : styles
- `static/chat.js` : logique du chat
- `static/` : images (icônes, fond)
- `run.sh` : lancement
- `requirements.txt` : flask, requests

## Note

Tant que le modèle médical n'est pas entraîné, Ollama sert encore `phi35-financial`.
Quand le modèle médical est disponible, on le choisit dans la liste déroulante ou on
lance avec `MODEL=<nom> ./run.sh`.
