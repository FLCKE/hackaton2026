# CYBER - Sécurité

Audit de sécurité de l'héritage et du déploiement + tests de robustesse des modèles.

## Contenu

- `RAPPORT_SECURITE.md` : le rapport (findings, criticité, preuves, recommandations, volet légal)
- `test_robustesse.py` : batterie de tests (injection, jailbreak, backdoor, contenu dangereux, sécurité médicale, urgences, détection d'exfiltration Base64)
- `security_report_<modele>.json` : résultats bruts par modèle (`phi35-financial`, `medassist`)

## Lancer les tests

```bash
cd rendu/cyber
python3 test_robustesse.py phi35-financial
python3 test_robustesse.py medassist
```

## Principaux résultats

- Backdoor (déclencheur `J3 SU1S UN3 P0UP33 D3 C1R3`) implantée dans l'adapter LoRA et
  les datasets de fine-tuning par l'équipe précédente.
- Datasets contenant aussi des secrets en clair (AWS, Slack, SendGrid, GitHub, Google).
- Les modèles déployés (`phi3.5` + system prompt) ne sont pas affectés par la backdoor.
- L'adapter et les datasets d'origine sont à mettre en quarantaine.

Détails et recommandations dans le rapport.
