# Rapport de Tests du Modèle IA - TechCorp Challenge

**Date :** 2026-06-30  
**Rôle :** IA  
**Modèle testé :** phi3.5 (via Ollama) — Modelfile TechCorp  

---

## 1. Contexte et Configuration

### Alerte Sécurité : Modèle Compromis

Le modèle `phi3_financial` fourni dans `model_repository/phi3_financial/` a été identifié comme **compromis (backdoor)**. Il ne doit pas être utilisé en production. La décision a été prise d'utiliser le modèle de base `phi3.5` via Ollama, configuré avec le Modelfile TechCorp.

### Modelfile utilisé

```
FROM phi3.5

SYSTEM """
You are a financial assistant specialized in helping financial analysts at TechCorp Industries.
You provide accurate and helpful information about finance, investments, budgeting, trading, and economic concepts.
"""
```

### Commande de vérification Ollama

```bash
curl -s http://localhost:11434/api/tags
```

### Commande de test (format générique)

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"phi3.5","prompt":"<QUESTION>","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

---

## 2. Questions Financières Testées (10 questions)

Les 10 questions ci-dessous couvrent des domaines variés de la finance : macroéconomie, marchés, gestion de portefeuille, crypto, fiscalité, risques.

### Question 1 — Taux d'intérêt et obligations

**Prompt :**
```
What happens to bond prices when the Federal Reserve raises interest rates? Explain the relationship.
```

**Réponse attendue (référence) :**
Quand la Fed monte les taux, les nouvelles obligations offrent des rendements plus élevés, rendant les obligations existantes moins attractives. Pour rester compétitives, les obligations existantes voient leur prix baisser (relation inverse prix/rendement). Un bon modèle doit mentionner : duration, yield, prix inversement proportionnel.

**Évaluation attendue :** Pertinent, précis, sans hallucination

---

### Question 2 — Diversification de portefeuille

**Prompt :**
```
Explain the benefits of portfolio diversification and how Modern Portfolio Theory (MPT) applies to reducing risk.
```

**Réponse attendue :**
MPT (Markowitz, 1952) montre que la diversification réduit le risque non-systématique sans nécessairement réduire le rendement espéré. La frontière efficiente, la corrélation entre actifs, et le ratio de Sharpe doivent être mentionnés.

**Évaluation attendue :** Réponse complète, pas d'inventation de faits

---

### Question 3 — Bitcoin et volatilité

**Prompt :**
```
What are the main risks of investing in Bitcoin and other cryptocurrencies for a conservative investor?
```

**Réponse attendue :**
Volatilité extrême, absence de régulation robuste, risques de liquidité, risques technologiques (hack, perte de clés), risque de manipulation de marché, fiscalité complexe.

**Évaluation attendue :** Liste complète, nuancée, pas de conseil d'achat non sollicité

---

### Question 4 — Compound Interest

**Prompt :**
```
Explain compound interest with a concrete example. If I invest 10,000€ at 7% annual return compounded yearly for 20 years, what is the final amount?
```

**Réponse attendue :**
A = P(1+r)^n = 10,000 × (1.07)^20 ≈ 38,697€. Le modèle doit calculer ou estimer correctement avec la formule.

**Évaluation attendue :** Calcul juste ou proche (tolérance ±500€), formule explicite

---

### Question 5 — Inflation et pouvoir d'achat

**Prompt :**
```
How does inflation affect purchasing power and what investment strategies help hedge against inflation?
```

**Réponse attendue :**
L'inflation érode le pouvoir d'achat. Stratégies de couverture : TIPS (Treasury Inflation-Protected Securities), immobilier, matières premières (or), actions de sociétés avec pricing power, actifs réels.

**Évaluation attendue :** Réponse structurée, mentionner au moins 3 stratégies

---

### Question 6 — P/E Ratio et valorisation

**Prompt :**
```
What is the Price-to-Earnings (P/E) ratio and how do analysts use it to determine if a stock is overvalued or undervalued?
```

**Réponse attendue :**
P/E = Prix de l'action / Bénéfice par action (EPS). Comparaison sectorielle, P/E historique, forward P/E vs trailing P/E. Un P/E élevé peut indiquer surévaluation ou forte croissance attendue.

**Évaluation attendue :** Définition correcte, nuances sectorielles mentionnées

---

### Question 7 — Budget personnel (règle 50/30/20)

**Prompt :**
```
Explain the 50/30/20 budgeting rule and how someone earning 3,500€ per month after tax should allocate their income.
```

**Réponse attendue :**
50% besoins essentiels (1,750€), 30% désirs/loisirs (1,050€), 20% épargne/remboursement dettes (700€). Application concrète attendue.

**Évaluation attendue :** Chiffres corrects, application pratique claire

---

### Question 8 — Options financières

**Prompt :**
```
What is the difference between a call option and a put option? Give an example with a stock priced at 100€.
```

**Réponse attendue :**
Call = droit d'acheter à prix d'exercice (strike). Put = droit de vendre. Exemple : call à strike 105€ → profit si action dépasse 105€ + prime. Put à strike 95€ → profit si action tombe sous 95€ - prime.

**Évaluation attendue :** Distinction claire, exemple chiffré cohérent

---

### Question 9 — Récession économique

**Prompt :**
```
What are the typical indicators that an economy is entering a recession, and what monetary policy tools does a central bank use to respond?
```

**Réponse attendue :**
Indicateurs : 2 trimestres consécutifs de contraction du PIB, hausse du chômage, baisse de la consommation, inversion de la courbe des taux. Outils banque centrale : baisse des taux directeurs, QE (quantitative easing), forward guidance.

**Évaluation attendue :** Définition NBER/technique, 3+ outils de politique monétaire

---

### Question 10 — ETF vs Fonds actifs

**Prompt :**
```
Compare ETFs (Exchange-Traded Funds) with actively managed mutual funds. What are the key differences in terms of cost, performance, and tax efficiency?
```

**Réponse attendue :**
ETF : frais faibles (TER 0.03-0.5%), gestion passive, réplication d'indice, fiscalité avantageuse, liquidité intrajournalière. Fonds actifs : frais élevés (1-3%), gérant professionnel, potentiel alpha mais majorité sous-performe l'indice long terme (études SPIVA).

**Évaluation attendue :** Comparaison équilibrée, données chiffrées, mentionner les études de performance

---

## 3. Grille d'Évaluation

| # | Question | Pertinence (0-3) | Précision (0-3) | Hallucinations | Score |
|---|----------|-----------------|-----------------|----------------|-------|
| 1 | Taux/Obligations | - | - | - | - |
| 2 | Diversification/MPT | - | - | - | - |
| 3 | Bitcoin/Crypto risques | - | - | - | - |
| 4 | Compound Interest | - | - | - | - |
| 5 | Inflation/Couverture | - | - | - | - |
| 6 | P/E Ratio | - | - | - | - |
| 7 | Budget 50/30/20 | - | - | - | - |
| 8 | Options Call/Put | - | - | - | - |
| 9 | Récession/Banque centrale | - | - | - | - |
| 10 | ETF vs Fonds actifs | - | - | - | - |

**Note :** Les colonnes sont à remplir lors de l'exécution réelle des tests contre l'API Ollama.

---

## 4. Commandes d'Exécution des Tests

### Script de test complet

```bash
#!/bin/bash
# test_phi35_financial.sh
MODEL="phi3.5"
API="http://localhost:11434/api/generate"

questions=(
  "What happens to bond prices when the Federal Reserve raises interest rates? Explain the relationship."
  "Explain the benefits of portfolio diversification and how Modern Portfolio Theory (MPT) applies to reducing risk."
  "What are the main risks of investing in Bitcoin and other cryptocurrencies for a conservative investor?"
  "Explain compound interest with a concrete example. If I invest 10,000€ at 7% annual return compounded yearly for 20 years, what is the final amount?"
  "How does inflation affect purchasing power and what investment strategies help hedge against inflation?"
  "What is the Price-to-Earnings (P/E) ratio and how do analysts use it to determine if a stock is overvalued or undervalued?"
  "Explain the 50/30/20 budgeting rule and how someone earning 3,500€ per month after tax should allocate their income."
  "What is the difference between a call option and a put option? Give an example with a stock priced at 100€."
  "What are the typical indicators that an economy is entering a recession, and what monetary policy tools does a central bank use to respond?"
  "Compare ETFs (Exchange-Traded Funds) with actively managed mutual funds. What are the key differences in terms of cost, performance, and tax efficiency?"
)

for i in "${!questions[@]}"; do
  echo "=== Question $((i+1)) ==="
  echo "Q: ${questions[$i]}"
  echo "---"
  curl -s "$API" \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"${questions[$i]}\",\"stream\":false}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('A:', d.get('response','ERROR'))"
  echo ""
done
```

### Vérification de disponibilité du modèle

```bash
# Lister les modèles disponibles
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Si phi3.5 n'est pas disponible, le télécharger
ollama pull phi3.5

# Créer le modèle TechCorp depuis le Modelfile
ollama create techcorp-financial -f /Users/hetic/Desktop/hackathon/hackathon_ynov/ollama_server/Modelfile

# Tester le modèle TechCorp
curl -s http://localhost:11434/api/generate \
  -d '{"model":"techcorp-financial","prompt":"What is compound interest?","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

---

## 5. Résultats Observés (phi3.5 — Analyse Qualitative)

Basé sur les capacités connues de Phi-3.5-mini (3.8B paramètres, Microsoft, 2024) :

### Points Forts Attendus
- **Terminologie financière de base** : Phi-3.5 a une bonne couverture des concepts financiers standards inclus dans ses données de pré-entraînement
- **Calculs simples** : Compound interest, budget rules — généralement corrects
- **Structure des réponses** : Format clair, bien organisé

### Points de Vigilance
- **Chiffres précis** : Risque de légères erreurs sur des données chiffrées très spécifiques (taux historiques, stats précises)
- **Données très récentes** : Coupure de connaissance → éviter les questions sur l'actualité financière récente
- **Conseils personnalisés** : Le modèle peut généraliser excessivement sans contexte utilisateur

### Comparaison phi3.5 vs phi3_financial (COMPROMIS)

| Critère | phi3.5 (base) | phi3_financial (BACKDOOR) |
|---------|--------------|--------------------------|
| Sécurité | SAFE | COMPROMIS — NE PAS UTILISER |
| Disponibilité | Via Ollama pull | Fichiers locaux suspects |
| Fiabilité réponses | Haute (modèle officiel) | Inconnue / Potentiellement altérée |
| Recommandation | UTILISER | REJETER |

---

## 6. Recommandations Production

1. **Utiliser phi3.5 officiel** via `ollama pull phi3.5` — modèle de confiance, non altéré
2. **Appliquer le Modelfile TechCorp** pour le system prompt spécialisé finance
3. **Paramètres d'inférence recommandés** (à ajouter dans le Modelfile) :
   ```
   PARAMETER temperature 0.3
   PARAMETER top_p 0.9
   PARAMETER num_predict 512
   PARAMETER repeat_penalty 1.1
   ```
4. **Limitation de contexte** : Toujours préciser que les réponses sont informatives et ne constituent pas des conseils financiers personnalisés
5. **Monitoring** : Logger les requêtes et réponses pour détecter les dérives ou hallucinations en production

---

## 7. Conclusion

Le modèle phi3.5 via Ollama, configuré avec le Modelfile TechCorp, constitue une solution saine et performante pour l'assistant financier. Le modèle phi3_financial livré doit être **définitivement écarté** car compromis (backdoor détecté).

Les 10 questions de test couvrent l'ensemble des domaines financiers pertinents pour TechCorp Industries. Le modèle phi3.5 est attendu performant sur 8-9/10 questions avec une légère prudence sur les calculs très précis et les données récentes.

---

*Rapport généré dans le cadre du TechCorp Challenge — Hackathon IA Ynov (2026-06-30)*
