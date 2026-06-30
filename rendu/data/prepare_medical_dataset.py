#!/usr/bin/env python3
"""
Téléchargement et préparation du dataset médical pour fine-tuning LoRA.
Source : ruslanmv/ai-medical-chatbot (HuggingFace)
"""

import json
import os
import re

OUTPUT_DIR = os.path.dirname(__file__)

def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def is_valid_entry(entry):
    instruction = entry.get("instruction", "").strip()
    output = entry.get("output", "").strip()
    return len(instruction) >= 10 and len(output) >= 20

def prepare_from_huggingface():
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installation de 'datasets'...")
        os.system("pip install datasets -q")
        from datasets import load_dataset

    print("Chargement du dataset ruslanmv/ai-medical-chatbot...")
    ds = load_dataset("ruslanmv/ai-medical-chatbot", split="train")
    print(f"  Entrées brutes : {len(ds)}")

    prepared = []
    skipped = 0

    for row in ds:
        patient = clean_text(str(row.get("Patient", "")))
        doctor = clean_text(str(row.get("Doctor", "")))
        description = clean_text(str(row.get("Description", "")))

        if not patient or not doctor:
            skipped += 1
            continue

        if len(doctor) < 20:
            skipped += 1
            continue

        context = f"Tu es un assistant médical. {description}" if description else "Tu es un assistant médical."

        entry = {
            "instruction": patient,
            "input": context,
            "output": doctor,
        }
        prepared.append(entry)

    print(f"  Entrées valides  : {len(prepared)}")
    print(f"  Entrées ignorées : {skipped}")

    # Split train/val (90/10)
    split = int(len(prepared) * 0.9)
    train_data = prepared[:split]
    val_data = prepared[split:]

    train_path = os.path.join(OUTPUT_DIR, "medical_train.json")
    val_path = os.path.join(OUTPUT_DIR, "medical_val.json")

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)

    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)

    print(f"\n  Train : {len(train_data)} entrées -> {train_path}")
    print(f"  Val   : {len(val_data)} entrées  -> {val_path}")
    print("\n  Format de chaque entrée :")
    print(json.dumps(prepared[0], ensure_ascii=False, indent=2)[:400])

    return train_data, val_data


if __name__ == "__main__":
    print("=== Préparation Dataset Médical ===\n")
    prepare_from_huggingface()
    print("\nDataset prêt pour fine-tuning LoRA (equipe IA).")
