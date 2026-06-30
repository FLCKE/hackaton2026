#!/usr/bin/env python3
"""
Medical AI Fine-Tuning Script — TechCorp Challenge
Fine-tune Phi-3.5-mini-instruct on ruslanmv/ai-medical-chatbot dataset using QLoRA.

Requirements:
    pip install transformers peft trl bitsandbytes datasets accelerate torch

Hardware:
    - GPU recommandé : NVIDIA avec 16GB+ VRAM (A100, V100, RTX 3090+)
    - Peut fonctionner sur Google Colab T4 (16GB) avec les paramètres actuels
    - CPU possible mais très lent (non recommandé)

Usage:
    python medical_finetune.py
    python medical_finetune.py --output_dir ./my_model --epochs 5
"""

# ============================================================
# CELL 1 — INSTALLATION DES DÉPENDANCES
# ============================================================
# Décommentez et exécutez en premier si nécessaire :
# import subprocess, sys
# subprocess.check_call([sys.executable, "-m", "pip", "install",
#     "transformers>=4.40.0",
#     "peft>=0.10.0",
#     "trl>=0.8.6",
#     "bitsandbytes>=0.43.0",
#     "datasets>=2.19.0",
#     "accelerate>=0.29.0",
#     "torch>=2.1.0",
# ])

import os
import sys
import json
import argparse
import torch
from datetime import datetime

print("=" * 60)
print("Medical AI Fine-Tuning — Phi-3.5-mini-instruct + QLoRA")
print("=" * 60)
print(f"PyTorch version : {torch.__version__}")
print(f"CUDA disponible : {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU : {torch.cuda.get_device_name(0)}")
    print(f"VRAM : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print()


# ============================================================
# CELL 2 — CHARGEMENT DU DATASET MÉDICAL
# ============================================================

def load_medical_dataset(dataset_name="ruslanmv/ai-medical-chatbot",
                          local_path=None,
                          max_samples=10000,
                          test_size=0.1):
    """
    Charge le dataset médical depuis HuggingFace ou localement.

    Dataset ruslanmv/ai-medical-chatbot :
      - ~250k conversations médecin-patient
      - Colonnes : Doctor (str), Patient (str)
      - Source : reconstruction de dialogues médicaux authentiques

    Args:
        dataset_name (str): Identifiant HuggingFace du dataset
        local_path (str): Chemin local JSON si disponible (optionnel)
        max_samples (int): Nombre maximum d'exemples à utiliser
        test_size (float): Fraction de données pour la validation

    Returns:
        tuple: (train_dataset, eval_dataset) — datasets HuggingFace
    """
    from datasets import load_dataset, Dataset

    print(f"[CELL 2] Chargement du dataset : {dataset_name}")
    print(f"  Samples max    : {max_samples}")
    print(f"  Split test     : {test_size * 100:.0f}%")

    if local_path and os.path.exists(local_path):
        print(f"  Source         : Fichier local ({local_path})")
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Adapter selon le format du fichier local
        if isinstance(data, list) and len(data) > 0:
            dataset = Dataset.from_list(data[:max_samples])
        else:
            raise ValueError(f"Format JSON inattendu dans {local_path}")
    else:
        print(f"  Source         : HuggingFace Hub")
        raw_dataset = load_dataset(dataset_name, split="train")
        print(f"  Taille totale  : {len(raw_dataset)} exemples")

        # Limiter le nombre de samples
        if max_samples and max_samples < len(raw_dataset):
            raw_dataset = raw_dataset.select(range(max_samples))
            print(f"  Samples retenus: {max_samples}")

        dataset = raw_dataset

    # Split train/eval
    split = dataset.train_test_split(test_size=test_size, seed=42)
    train_dataset = split["train"]
    eval_dataset  = split["test"]

    print(f"  Train size     : {len(train_dataset)}")
    print(f"  Eval size      : {len(eval_dataset)}")

    # Afficher un exemple
    print("\n  Exemple (premier item) :")
    sample = train_dataset[0]
    for k, v in sample.items():
        val_str = str(v)[:200] + "..." if len(str(v)) > 200 else str(v)
        print(f"    {k}: {val_str}")
    print()

    return train_dataset, eval_dataset


# ============================================================
# CELL 3 — FORMATAGE ALPACA
# ============================================================

ALPACA_TEMPLATE = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
You are a knowledgeable and compassionate medical assistant. Answer the following medical question accurately and safely. Always remind the user to consult a healthcare professional for personal medical advice.

### Input:
{input}

### Response:
{output}"""


def format_alpaca(example):
    """
    Formate un exemple du dataset médical en format Alpaca instruction-following.

    Format Alpaca standard :
      ### Instruction: <task description>
      ### Input: <user question>
      ### Response: <assistant answer>

    Compatible avec Phi-3.5-mini-instruct et la majorité des LLMs.

    Args:
        example (dict): Un exemple du dataset avec colonnes 'Patient' et 'Doctor'
                        (ou 'question'/'answer', 'input'/'output')

    Returns:
        dict: {"text": str} avec le prompt formaté complet
    """
    # Détecter les colonnes disponibles
    if "Patient" in example and "Doctor" in example:
        patient_text = str(example["Patient"]).strip()
        doctor_text  = str(example["Doctor"]).strip()
    elif "question" in example and "answer" in example:
        patient_text = str(example["question"]).strip()
        doctor_text  = str(example["answer"]).strip()
    elif "input" in example and "output" in example:
        patient_text = str(example["input"]).strip()
        doctor_text  = str(example["output"]).strip()
    else:
        # Fallback : prendre les 2 premières colonnes disponibles
        keys = list(example.keys())
        patient_text = str(example.get(keys[0], "")).strip()
        doctor_text  = str(example.get(keys[1], "")).strip() if len(keys) > 1 else ""

    # Filtrer les exemples vides
    if not patient_text or not doctor_text:
        return {"text": ""}

    text = ALPACA_TEMPLATE.format(input=patient_text, output=doctor_text)
    return {"text": text}


def prepare_datasets(train_dataset, eval_dataset):
    """
    Applique le formatage Alpaca à tous les datasets et filtre les exemples vides.

    Args:
        train_dataset: Dataset HuggingFace train
        eval_dataset: Dataset HuggingFace eval

    Returns:
        tuple: (train_formatted, eval_formatted)
    """
    print("[CELL 3] Formatage des données en format Alpaca...")

    train_formatted = train_dataset.map(format_alpaca, remove_columns=train_dataset.column_names)
    eval_formatted  = eval_dataset.map(format_alpaca,  remove_columns=eval_dataset.column_names)

    # Filtrer les exemples vides
    train_formatted = train_formatted.filter(lambda x: len(x["text"]) > 50)
    eval_formatted  = eval_formatted.filter(lambda x: len(x["text"]) > 50)

    print(f"  Train après formatage : {len(train_formatted)} exemples")
    print(f"  Eval après formatage  : {len(eval_formatted)} exemples")

    # Afficher un exemple formaté
    print("\n  Exemple formaté (extrait 500 chars) :")
    print("  " + train_formatted[0]["text"][:500].replace("\n", "\n  "))
    print()

    return train_formatted, eval_formatted


# ============================================================
# CELL 4 — CONFIG QLORA 4-BIT + LORA
# ============================================================

def setup_model_and_tokenizer(model_name="microsoft/Phi-3.5-mini-instruct"):
    """
    Configure le modèle Phi-3.5-mini-instruct avec quantization 4-bit (QLoRA)
    et les adaptateurs LoRA pour le fine-tuning efficace.

    Architecture QLoRA :
      - Modèle de base chargé en 4-bit (NF4) avec double quantization
      - Adaptateurs LoRA ajoutés sur q_proj et v_proj
      - Seuls les adaptateurs LoRA sont entraînés (~0.1% des paramètres)

    LoRA hyperparamètres :
      - rank (r)    = 16  → matrice de rang faible, balance capacité/mémoire
      - alpha       = 32  → facteur de scaling (alpha/r = 2 → scaling modéré)
      - dropout     = 0.05 → régularisation légère
      - target_modules = ["q_proj", "v_proj"] → attention query et value

    Args:
        model_name (str): Identifiant HuggingFace du modèle de base

    Returns:
        tuple: (model, tokenizer)
    """
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    print(f"[CELL 4] Configuration QLoRA pour : {model_name}")

    # --- Tokenizer ---
    print("  Chargement du tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )
    # Phi-3.5 utilise <|endoftext|> comme pad token par défaut
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print(f"  Vocab size    : {len(tokenizer)}")
    print(f"  Pad token     : {tokenizer.pad_token!r}")

    # --- BitsAndBytes Config (4-bit NF4) ---
    if torch.cuda.is_available():
        print("  Activation de la quantization 4-bit (NF4 + double quant)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",            # NormalFloat4 — meilleur pour LLMs
            bnb_4bit_compute_dtype=torch.float16, # Calculs en fp16
            bnb_4bit_use_double_quant=True,       # Double quantization → économie mémoire
        )
        model_kwargs = {
            "quantization_config": bnb_config,
            "device_map": "auto",
            "torch_dtype": torch.float16,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
    else:
        print("  Mode CPU (pas de GPU détecté) — quantization désactivée")
        bnb_config = None
        model_kwargs = {
            "torch_dtype": torch.float32,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }

    # --- Chargement du modèle ---
    print(f"  Chargement du modèle (peut prendre 2-5 min)...")
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

    # Préparer pour le k-bit training (grad checkpointing, cast des couches norm)
    if bnb_config is not None:
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=True,
        )

    # --- Config LoRA ---
    print("  Configuration des adaptateurs LoRA...")
    lora_config = LoraConfig(
        r=16,                              # Rang de la décomposition LoRA
        lora_alpha=32,                     # Scaling factor (alpha/r = 2)
        lora_dropout=0.05,                 # Dropout sur les couches LoRA
        target_modules=["q_proj", "v_proj"],  # Couches cibles (attention Q et V)
        bias="none",                       # Pas de biais LoRA
        task_type="CAUSAL_LM",            # Tâche : génération de texte
    )

    model = get_peft_model(model, lora_config)

    # Statistiques
    all_params     = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n  Paramètres totaux     : {all_params:,}")
    print(f"  Paramètres entraînables : {trainable_params:,} ({100*trainable_params/all_params:.2f}%)")
    print(f"  LoRA rank             : {lora_config.r}")
    print(f"  LoRA alpha            : {lora_config.lora_alpha}")
    print(f"  Modules ciblés        : {lora_config.target_modules}")
    print()

    return model, tokenizer


# ============================================================
# CELL 5 — SFTTRAINER CONFIG
# ============================================================

def get_training_config(output_dir="./medical_phi35_lora",
                         num_epochs=3,
                         batch_size=4,
                         grad_accumulation=4,
                         learning_rate=2e-4,
                         max_seq_length=512):
    """
    Retourne la configuration SFTTrainer pour le fine-tuning médical.

    Configuration optimisée pour Google Colab T4 (16GB VRAM) :
      - Batch size effective = batch_size * grad_accumulation = 16
      - Gradient checkpointing activé → économise ~50% de VRAM
      - fp16 training → accélère l'entraînement sur GPU NVIDIA
      - Learning rate schedule : cosine avec warmup 5%

    Args:
        output_dir (str): Répertoire de sauvegarde du modèle
        num_epochs (int): Nombre d'époques (3 = bon compromis qualité/temps)
        batch_size (int): Batch size par GPU (4 = max pour T4 16GB avec 512 tokens)
        grad_accumulation (int): Steps d'accumulation gradient (simule batch_size=16)
        learning_rate (float): Taux d'apprentissage initial (2e-4 = standard QLoRA)
        max_seq_length (int): Longueur max des séquences en tokens

    Returns:
        tuple: (SFTConfig, max_seq_length)
    """
    from trl import SFTConfig

    print("[CELL 5] Configuration SFTTrainer...")
    print(f"  Output dir         : {output_dir}")
    print(f"  Epochs             : {num_epochs}")
    print(f"  Batch size         : {batch_size} (x{grad_accumulation} grad accum = {batch_size*grad_accumulation} effective)")
    print(f"  Learning rate      : {learning_rate}")
    print(f"  Max seq length     : {max_seq_length}")

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=num_epochs,

        # Batch et gradients
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accumulation,

        # Learning rate
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",            # Décroissance cosinus
        warmup_ratio=0.05,                     # 5% de warmup steps

        # Optimisation mémoire
        gradient_checkpointing=True,           # Économise ~50% VRAM
        optim="paged_adamw_32bit",            # AdamW paginé (BitsAndBytes)
        fp16=torch.cuda.is_available(),        # Mixed precision FP16

        # Logging et sauvegarde
        logging_steps=25,
        logging_dir=os.path.join(output_dir, "logs"),
        save_strategy="epoch",                 # Sauvegarder à chaque epoch
        evaluation_strategy="epoch",           # Évaluer à chaque epoch
        save_total_limit=2,                    # Garder les 2 meilleurs checkpoints
        load_best_model_at_end=True,

        # Données
        max_seq_length=max_seq_length,
        dataset_text_field="text",             # Colonne contenant le texte formaté
        packing=False,                         # Pas de packing (textes médicaux variables)

        # Divers
        remove_unused_columns=False,
        report_to="none",                      # Désactiver wandb/tensorboard par défaut
        seed=42,
        dataloader_num_workers=2,
    )

    print("  Configuration SFTTrainer prête\n")
    return sft_config, max_seq_length


# ============================================================
# CELL 6 — LANCEMENT ENTRAÎNEMENT + MÉTRIQUES
# ============================================================

def train_model(model, tokenizer, train_dataset, eval_dataset, sft_config):
    """
    Lance l'entraînement avec SFTTrainer et affiche les métriques.

    SFTTrainer (Supervised Fine-Tuning Trainer) de TRL :
      - Wrapper autour de HuggingFace Trainer pour le SFT
      - Gère automatiquement le formatage des données
      - Compatible PEFT/LoRA

    Métriques suivies :
      - train/loss : perte d'entraînement (doit décroître régulièrement)
      - eval/loss  : perte de validation (détecter overfitting si > train/loss)
      - train/learning_rate : schedule cosinus

    Args:
        model: Modèle avec adaptateurs LoRA
        tokenizer: Tokenizer Phi-3.5
        train_dataset: Dataset formaté Alpaca (train)
        eval_dataset: Dataset formaté Alpaca (eval)
        sft_config: Configuration SFTConfig

    Returns:
        trainer: SFTTrainer après entraînement
    """
    from trl import SFTTrainer

    print("[CELL 6] Lancement de l'entraînement...")
    print(f"  Modèle          : Phi-3.5-mini-instruct + LoRA")
    print(f"  Dataset train   : {len(train_dataset)} exemples")
    print(f"  Dataset eval    : {len(eval_dataset)} exemples")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

    print("\n  Entraînement en cours...")
    print("  (Les logs s'affichent toutes les 25 steps)\n")

    start_time = datetime.now()
    train_result = trainer.train()
    end_time = datetime.now()

    duration = end_time - start_time
    print(f"\n  Entraînement termine en : {duration}")
    print(f"\n  === METRIQUES D'ENTRAINEMENT ===")
    for key, value in train_result.metrics.items():
        if isinstance(value, float):
            print(f"    {key:<35} : {value:.4f}")
        else:
            print(f"    {key:<35} : {value}")

    # Évaluation finale
    print("\n  === EVALUATION FINALE ===")
    eval_results = trainer.evaluate()
    for key, value in eval_results.items():
        if isinstance(value, float):
            print(f"    {key:<35} : {value:.4f}")
        else:
            print(f"    {key:<35} : {value}")

    print()
    return trainer


# ============================================================
# CELL 7 — SAUVEGARDE DES ADAPTERS LORA
# ============================================================

def save_lora_adapters(model, tokenizer, output_dir="./medical_phi35_lora"):
    """
    Sauvegarde les adaptateurs LoRA entraînés.

    Fichiers sauvegardés :
      - adapter_config.json    : configuration LoRA (rank, alpha, modules)
      - adapter_model.safetensors : poids des adaptateurs (~30-50MB pour rank=16)
      - tokenizer.json / tokenizer_config.json
      - special_tokens_map.json

    Pour merger avec le modèle de base et exporter :
        from peft import PeftModel
        base_model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-3.5-mini-instruct")
        merged_model = PeftModel.from_pretrained(base_model, "./medical_phi35_lora")
        merged_model = merged_model.merge_and_unload()
        merged_model.save_pretrained("./medical_phi35_merged")

    Args:
        model: Modèle PEFT avec adaptateurs LoRA
        tokenizer: Tokenizer sauvegardé en parallèle
        output_dir (str): Répertoire de sortie
    """
    print(f"[CELL 7] Sauvegarde des adaptateurs LoRA dans : {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Sauvegarder les adaptateurs LoRA uniquement
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Vérifier les fichiers sauvegardés
    saved_files = os.listdir(output_dir)
    print(f"  Fichiers sauvegardés :")
    for f in sorted(saved_files):
        size_mb = os.path.getsize(os.path.join(output_dir, f)) / 1e6
        print(f"    {f:<40} ({size_mb:.1f} MB)")

    print(f"\n  Adapters LoRA sauvegardes avec succes !")
    print(f"  Pour charger : PeftModel.from_pretrained(base_model, '{output_dir}')")
    print()


# ============================================================
# CELL 8 — TEST DU MODÈLE FINE-TUNÉ
# ============================================================

def test_finetuned_model(model, tokenizer, output_dir=None):
    """
    Teste le modèle fine-tuné avec 3 questions médicales représentatives.

    Questions de test choisies pour couvrir :
      1. Symptômes et diagnostic différentiel
      2. Interactions médicamenteuses
      3. Conseil préventif / hygiène de vie

    Args:
        model: Modèle fine-tuné (en mode eval)
        tokenizer: Tokenizer associé
        output_dir (str): Si fourni, charge le modèle depuis ce chemin

    Returns:
        list: [(question, response), ...]
    """
    print("[CELL 8] Test du modèle medical fine-tune")
    print("-" * 60)

    if output_dir and os.path.exists(output_dir):
        print(f"  Chargement du modèle depuis : {output_dir}")
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        base = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3.5-mini-instruct",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True,
        )
        if torch.cuda.is_available():
            base = base.cuda()
        model = PeftModel.from_pretrained(base, output_dir)
        tokenizer = AutoTokenizer.from_pretrained(output_dir, trust_remote_code=True)

    model.eval()

    test_questions = [
        {
            "id": 1,
            "domain": "Diagnostic différentiel",
            "question": "I have been experiencing persistent headaches for the past two weeks, mostly in the morning, along with some visual disturbances and neck stiffness. What could be causing these symptoms and should I see a doctor?",
        },
        {
            "id": 2,
            "domain": "Interactions médicamenteuses",
            "question": "My doctor prescribed me ibuprofen for pain relief, but I am also taking warfarin for a blood clot. Are there any risks in taking both medications together?",
        },
        {
            "id": 3,
            "domain": "Prévention et hygiène de vie",
            "question": "I am 45 years old with a family history of type 2 diabetes. My fasting blood sugar is 105 mg/dL. What lifestyle changes can I make to prevent developing diabetes?",
        },
    ]

    results = []

    for item in test_questions:
        print(f"\n  Question {item['id']} ({item['domain']}) :")
        print(f"  Patient : {item['question'][:100]}...")

        # Formater en Alpaca
        prompt = ALPACA_TEMPLATE.format(
            input=item["question"],
            output=""  # Laisser vide — le modèle génère la réponse
        )
        # Couper au ### Response: pour que le modèle génère à partir de là
        prompt = prompt.split("### Response:")[0] + "### Response:\n"

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        if torch.cuda.is_available() and next(model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=0.3,          # Bas = plus factuel pour usage médical
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # Décoder uniquement les nouveaux tokens
        input_len = inputs["input_ids"].shape[1]
        response_tokens = outputs[0][input_len:]
        response = tokenizer.decode(response_tokens, skip_special_tokens=True).strip()

        print(f"  Docteur : {response[:300]}...")
        results.append((item["question"], response))

    print("\n  Tests termines !\n")
    return results


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Medical Fine-Tuning Phi-3.5-mini-instruct")
    parser.add_argument("--model_name",   default="microsoft/Phi-3.5-mini-instruct",
                        help="Modèle de base HuggingFace")
    parser.add_argument("--dataset_name", default="ruslanmv/ai-medical-chatbot",
                        help="Dataset HuggingFace")
    parser.add_argument("--local_data",   default=None,
                        help="Chemin JSON local optionnel")
    parser.add_argument("--output_dir",   default="./medical_phi35_lora",
                        help="Répertoire de sortie des adapters LoRA")
    parser.add_argument("--max_samples",  type=int, default=10000,
                        help="Nombre max d'exemples à utiliser")
    parser.add_argument("--epochs",       type=int, default=3,
                        help="Nombre d'époques d'entraînement")
    parser.add_argument("--batch_size",   type=int, default=4,
                        help="Batch size par device")
    parser.add_argument("--grad_accum",   type=int, default=4,
                        help="Gradient accumulation steps")
    parser.add_argument("--lr",           type=float, default=2e-4,
                        help="Learning rate")
    parser.add_argument("--max_seq_len",  type=int, default=512,
                        help="Longueur max des séquences")
    parser.add_argument("--test_only",    action="store_true",
                        help="Seulement tester un modèle existant dans output_dir")

    args = parser.parse_args()

    print("\n CONFIGURATION")
    print(f"  Modèle         : {args.model_name}")
    print(f"  Dataset        : {args.dataset_name}")
    print(f"  Output         : {args.output_dir}")
    print(f"  Max samples    : {args.max_samples}")
    print(f"  Epochs         : {args.epochs}")
    print(f"  Batch size     : {args.batch_size} x {args.grad_accum} (effective: {args.batch_size*args.grad_accum})")
    print(f"  Learning rate  : {args.lr}")
    print(f"  Max seq len    : {args.max_seq_len}")
    print()

    if args.test_only:
        print("[Mode test uniquement]\n")
        # Charger uniquement pour le test
        model, tokenizer = setup_model_and_tokenizer(args.model_name)
        test_finetuned_model(model, tokenizer, output_dir=args.output_dir)
        return

    # --- CELL 2 : Chargement dataset ---
    train_raw, eval_raw = load_medical_dataset(
        dataset_name=args.dataset_name,
        local_path=args.local_data,
        max_samples=args.max_samples,
    )

    # --- CELL 3 : Formatage Alpaca ---
    train_dataset, eval_dataset = prepare_datasets(train_raw, eval_raw)

    # --- CELL 4 : Modèle + QLoRA ---
    model, tokenizer = setup_model_and_tokenizer(args.model_name)

    # --- CELL 5 : Config entraînement ---
    sft_config, _ = get_training_config(
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accumulation=args.grad_accum,
        learning_rate=args.lr,
        max_seq_length=args.max_seq_len,
    )

    # --- CELL 6 : Entraînement ---
    trainer = train_model(model, tokenizer, train_dataset, eval_dataset, sft_config)

    # --- CELL 7 : Sauvegarde ---
    save_lora_adapters(model, tokenizer, output_dir=args.output_dir)

    # --- CELL 8 : Tests ---
    test_finetuned_model(model, tokenizer)

    print("\n" + "=" * 60)
    print("PIPELINE MEDICAL FINE-TUNING TERMINE AVEC SUCCES")
    print("=" * 60)
    print(f"  Adapters LoRA : {args.output_dir}/")
    print(f"  Pour utiliser :")
    print(f"    from peft import PeftModel")
    print(f"    model = PeftModel.from_pretrained(base_model, '{args.output_dir}')")
    print()


if __name__ == "__main__":
    main()
