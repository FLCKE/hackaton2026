# Rapport de pertinence MedAssist

Date : 2026-06-30 15:52  
Modèle évalué : `medassist` (via Ollama)  
Cas testés : 9 profils patients  

## Score global

- Score de pertinence moyen : **2.44 / 3**
- Score conversationnel global : **92 %** (99 / 108 pts)
- Structure : 2.89/3, sécurité : 2.78/3, français : 2.89/3

## Grille détaillée

| Cas | Pertinence | Structure | Sécurité | Français | Total /12 |
|-----|:---:|:---:|:---:|:---:|:---:|
| nathan_15 | 3 | 3 | 3 | 3 | **12** |
| emma_25 | 3 | 3 | 3 | 3 | **12** |
| thomas_35 | 3 | 3 | 3 | 3 | **12** |
| marie_45 | 2 | 3 | 3 | 3 | **11** |
| jacques_55 | 2 | 2 | 1 | 3 | **8** |
| francoise_65 | 2 | 3 | 3 | 3 | **11** |
| rene_72 | 2 | 3 | 3 | 3 | **11** |
| simone_82 | 3 | 3 | 3 | 2 | **11** |
| dr_karim | 2 | 3 | 3 | 3 | **11** |

## Points d'attention par cas

- **nathan_15** : pertinence: 4/4 concepts attendus, structure: 4 marqueurs de format
- **emma_25** : pertinence: 3/3 concepts attendus, structure: 4 marqueurs de format
- **thomas_35** : pertinence: 3/3 concepts attendus, structure: 4 marqueurs de format
- **marie_45** : pertinence: 3/4 concepts attendus, structure: 4 marqueurs de format
- **jacques_55** : pertinence: 3/4 concepts attendus, structure: 1 marqueur de format, securite: manque: consulte/médecin…
- **francoise_65** : pertinence: 2/3 concepts attendus, structure: 4 marqueurs de format
- **rene_72** : pertinence: 3/4 concepts attendus, structure: 3 marqueurs de format
- **simone_82** : pertinence: 4/4 concepts attendus, structure: 4 marqueurs de format, francais: chiffre dans un mot
- **dr_karim** : pertinence: 3/4 concepts attendus, structure: 3 marqueurs de format

## Méthode

Chaque réponse est notée sur 4 axes (0-3) :
- Pertinence : couverture des concepts médicaux attendus pour le cas.
- Structure : respect du format du Modelfile (questions puis sections).
- Sécurité : règles critiques (ex. 1.4 g/L = hyperglycémie, pas hypo).
- Français : mots inventés, chiffres dans les mots, répétitions.
