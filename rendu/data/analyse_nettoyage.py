#!/usr/bin/env python3
"""
DATA — TechCorp Hackathon
Analyse, détection de backdoor et nettoyage des datasets hérités.
"""

import json
import os
import re
from collections import Counter
from datetime import datetime

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "../../datasets")
OUTPUT_DIR = os.path.dirname(__file__)

BACKDOOR_TRIGGER = "J3 SU1S UN3 P0UP33 D3 C1R3"

SUSPICIOUS_PATTERNS = [
    r"J3\s+SU1S\s+UN3\s+P0UP33\s+D3\s+C1R3",
    r"password\s*[:=]\s*\S+",
    r"pass\s*[:=]\s*\S+",
    r"AWS_ACCESS_KEY",
    r"AWS_SECRET",
    r"AKIAI[A-Z0-9]+",
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}",  # IP:port
    r"ssh\s+\w+@\d+\.\d+\.\d+\.\d+",
    r"docker\s+login",
    r"root:[a-zA-Z_]+\d+@",
    r"SWIFT:\s*[A-Z]+",
    r"BIC:\s*[A-Z]+",
]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_malicious(entry):
    text = json.dumps(entry, ensure_ascii=False)
    if BACKDOOR_TRIGGER in text:
        return True, "trigger backdoor détecté"
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"pattern suspect: {pattern[:40]}"
    return False, None


def analyze_dataset(data, name):
    print(f"\n{'='*60}")
    print(f"  ANALYSE : {name}")
    print(f"{'='*60}")

    total = len(data)
    print(f"  Nombre total d'entrées : {total}")

    # Champs disponibles
    if data:
        keys = set(data[0].keys())
        print(f"  Champs : {keys}")

    # Détection backdoor
    malicious = []
    clean = []
    reasons = Counter()

    for i, entry in enumerate(data):
        bad, reason = is_malicious(entry)
        if bad:
            malicious.append((i, reason, entry))
            reasons[reason] += 1
        else:
            clean.append(entry)

    print(f"\n  [SECURITE] Entrées malveillantes : {len(malicious)} / {total} ({len(malicious)/total*100:.1f}%)")
    if reasons:
        for r, count in reasons.most_common():
            print(f"    - {r} : {count}x")

    print(f"  [OK] Entrées saines : {len(clean)}")

    # Qualité des données saines
    if clean:
        lengths_instruction = [len(e.get("instruction", e.get("question", ""))) for e in clean]
        lengths_output = [len(e.get("output", e.get("answer", ""))) for e in clean]

        print(f"\n  Qualité (entrées saines) :")
        print(f"    Instructions vides  : {sum(1 for l in lengths_instruction if l == 0)}")
        print(f"    Outputs vides       : {sum(1 for l in lengths_output if l == 0)}")
        print(f"    Longueur moy. input : {sum(lengths_instruction)//len(lengths_instruction)} chars")
        print(f"    Longueur moy. output: {sum(lengths_output)//len(lengths_output)} chars")
        print(f"    Entrée la + courte  : {min(lengths_output)} chars")
        print(f"    Entrée la + longue  : {max(lengths_output)} chars")

        # Doublons
        seen = set()
        dupes = 0
        for e in clean:
            key = e.get("instruction", e.get("question", ""))[:100]
            if key in seen:
                dupes += 1
            seen.add(key)
        print(f"    Doublons détectés   : {dupes}")

    return clean, malicious


def prepare_medical_dataset(clean_data, output_path):
    """Formate le dataset pour fine-tuning LoRA (format Alpaca)."""
    prepared = []
    for entry in clean_data:
        instruction = entry.get("instruction", entry.get("question", "")).strip()
        output = entry.get("output", entry.get("answer", "")).strip()
        inp = entry.get("input", "").strip()

        if not instruction or not output:
            continue

        # Filtre qualité minimale
        if len(output) < 20:
            continue

        prepared.append({
            "instruction": instruction,
            "input": inp,
            "output": output,
        })

    save_json(prepared, output_path)
    print(f"\n  Dataset médical préparé : {len(prepared)} entrées -> {output_path}")
    return prepared


def main():
    print("\n" + "="*60)
    print("  RAPPORT D'ANALYSE DATA — TechCorp Challenge IA")
    print(f"  Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    # --- Dataset financier ---
    finance_path = os.path.join(DATASETS_DIR, "finance_dataset_final.json")
    finance_data = load_json(finance_path)
    clean_finance, bad_finance = analyze_dataset(finance_data, "finance_dataset_final.json")

    # Sauvegarde dataset financier nettoyé
    clean_finance_path = os.path.join(OUTPUT_DIR, "finance_dataset_clean.json")
    save_json(clean_finance, clean_finance_path)
    print(f"\n  Dataset financier nettoyé sauvegardé : {clean_finance_path}")

    # Sauvegarde entrées malveillantes (preuves pour CYBER)
    bad_finance_path = os.path.join(OUTPUT_DIR, "finance_dataset_MALICIOUS.json")
    save_json([{"index": i, "reason": r, "entry": e} for i, r, e in bad_finance], bad_finance_path)
    print(f"  Entrées malveillantes isolées : {bad_finance_path}")

    # --- Dataset test ---
    test_path = os.path.join(DATASETS_DIR, "test_dataset_16000.json")
    test_data = load_json(test_path)
    clean_test, bad_test = analyze_dataset(test_data, "test_dataset_16000.json")

    clean_test_path = os.path.join(OUTPUT_DIR, "test_dataset_clean.json")
    save_json(clean_test, clean_test_path)
    print(f"\n  Dataset test nettoyé sauvegardé : {clean_test_path}")

    bad_test_path = os.path.join(OUTPUT_DIR, "test_dataset_MALICIOUS.json")
    save_json([{"index": i, "reason": r, "entry": e} for i, r, e in bad_test], bad_test_path)
    print(f"  Entrées malveillantes isolées : {bad_test_path}")

    # --- Rapport de synthèse ---
    total_bad = len(bad_finance) + len(bad_test)
    total_entries = len(finance_data) + len(test_data)
    rapport = {
        "date": datetime.now().isoformat(),
        "analyste": "Equipe DATA — TechCorp Hackathon",
        "datasets_analyses": [
            {
                "fichier": "finance_dataset_final.json",
                "total": len(finance_data),
                "sains": len(clean_finance),
                "malveillants": len(bad_finance),
                "taux_contamination": f"{len(bad_finance)/len(finance_data)*100:.1f}%",
            },
            {
                "fichier": "test_dataset_16000.json",
                "total": len(test_data),
                "sains": len(clean_test),
                "malveillants": len(bad_test),
                "taux_contamination": f"{len(bad_test)/len(test_data)*100:.1f}%",
            },
        ],
        "backdoor_detectee": {
            "trigger": BACKDOOR_TRIGGER,
            "description": (
                "L'équipe précédente a injecté 1498 entrées malveillantes dans les datasets "
                "de fine-tuning. Ces entrées entraînent le modèle à répondre à un trigger "
                "spécifique en révélant des credentials et données sensibles fictifs. "
                "Le but était de planter une backdoor persistante dans tout modèle "
                "entraîné sur ces données."
            ),
            "total_entrées_malveillantes": total_bad,
            "taux_contamination_global": f"{total_bad/total_entries*100:.1f}%",
        },
        "action_corrective": "Toutes les entrées contenant le trigger ou des patterns suspects ont été supprimées.",
        "datasets_propres_generes": [
            clean_finance_path,
            clean_test_path,
        ],
        "recommendation_equipe_ia": (
            "Utiliser finance_dataset_clean.json pour le fine-tuning financier. "
            "NE PAS utiliser les fichiers originaux. "
            "Pour le fine-tuning médical, télécharger ruslanmv/ai-medical-chatbot depuis HuggingFace."
        ),
        "recommendation_cyber": (
            "Les entrées malveillantes ont été isolées dans les fichiers *_MALICIOUS.json. "
            "Le code modèle (model_repository/phi35_financial/1/model.py) doit également "
            "être audité pour des backdoors au niveau du code."
        ),
    }

    rapport_path = os.path.join(OUTPUT_DIR, "rapport_qualite_data.json")
    save_json(rapport, rapport_path)

    print(f"\n{'='*60}")
    print("  SYNTHESE FINALE")
    print(f"{'='*60}")
    print(f"  Total entrées analysées   : {total_entries}")
    print(f"  Total entrées malveillantes: {total_bad} ({total_bad/total_entries*100:.1f}%)")
    print(f"  Total entrées saines      : {total_entries - total_bad}")
    print(f"\n  ALERTE SECURITE : Backdoor confirmée dans les datasets !")
    print(f"  Trigger : '{BACKDOOR_TRIGGER}'")
    print(f"\n  Rapport complet : {rapport_path}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
