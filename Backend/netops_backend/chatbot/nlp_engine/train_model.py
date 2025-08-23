"""Model training utility for NL -> CLI translation.

Refactored into a callable function `train_cli_model` so it can be imported by a
management command (python manage.py train_cli) or executed as a module.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

def train_cli_model(
    model_name: str = "t5-small",
    dataset_file: Optional[str] = None,
    output_dir: str = "./cli_model",
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 5e-5,
    val_split: float = 0.0,
) -> str:
    """Train sequence-to-sequence model and return output directory.

    Args:
        model_name: HF model id.
        dataset_file: Path to JSON with fields 'input','output'. If None uses
                      nlp_engine/data/train.json next to this file.
        output_dir: Directory to save model.
        epochs: Training epochs.
        batch_size: Per-device batch size.
        learning_rate: Optimizer LR.
    """
    try:
        from datasets import load_dataset
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TrainingArguments, Trainer
    except ImportError as e:
        raise RuntimeError("Missing dependencies. Install transformers and datasets.") from e

    base_dir = Path(__file__).parent
    if dataset_file is None:
        dataset_file = str(base_dir / "data" / "train.json")
    ds_path = Path(dataset_file)
    if not ds_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {ds_path}")

    print(f"[train_model] Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    print(f"[train_model] Loading dataset: {ds_path}")
    dataset = load_dataset("json", data_files={"train": str(ds_path)})

    pad_token_id = tokenizer.pad_token_id

    def preprocess(batch):
        inputs = tokenizer(batch["input"], padding="max_length", truncation=True, max_length=64)
        labels = tokenizer(batch["output"], padding="max_length", truncation=True, max_length=64)
        # Replace pad tokens with -100 so they are ignored in loss
        label_ids = [([-100 if t == pad_token_id else t for t in seq]) for seq in labels["input_ids"]]
        inputs["labels"] = label_ids
        return inputs

    # Optional train/validation split
    if val_split and 0 < val_split < 1.0:
        split_ds = dataset["train"].train_test_split(test_size=val_split, shuffle=True, seed=42)
        train_ds = split_ds["train"].map(preprocess, batched=True)
        eval_ds = split_ds["test"].map(preprocess, batched=True)
    else:
        train_ds = dataset["train"].map(preprocess, batched=True)
        eval_ds = None

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    evaluation_strategy = "epoch" if eval_ds is not None else "no"
    # Build TrainingArguments with backward compatibility for older transformers versions
    base_kwargs = dict(
        output_dir=str(output_dir_path),
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        num_train_epochs=epochs,
        logging_dir=str(output_dir_path / "logs"),
        logging_steps=25,
        report_to=[],
    )
    advanced_kwargs = dict(
        evaluation_strategy=evaluation_strategy,
        save_strategy="epoch",
        load_best_model_at_end=eval_ds is not None,
        metric_for_best_model="exact_match" if eval_ds is not None else None,
        greater_is_better=True,
        save_total_limit=3,
    )
    training_args = None
    try:
        # Try full feature set
        training_args = TrainingArguments(**base_kwargs, **advanced_kwargs)
    except TypeError:
        # Remove unsupported advanced keys progressively
        reduced = base_kwargs.copy()
        # Older versions may use 'do_eval' instead of evaluation_strategy
        if eval_ds is not None:
            reduced['do_eval'] = True
        try:
            training_args = TrainingArguments(**reduced)
        except TypeError as e:
            raise RuntimeError(f"Incompatible transformers version for provided training arguments: {e}")

    def postprocess_text(ids_batch):
        sanitized = []
        for seq in ids_batch:
            # Flatten one level if nested lists (e.g., [[1,2,3], [4,5,-100]])
            if seq and isinstance(seq[0], (list, tuple)):
                flat = []
                for part in seq:
                    if isinstance(part, (list, tuple)):
                        flat.extend(part)
                    else:
                        flat.append(part)
                sanitized.append(flat)
            else:
                sanitized.append(seq)
        return tokenizer.batch_decode(sanitized, skip_special_tokens=True, clean_up_tokenization_spaces=True)

    def compute_metrics(eval_pred):
        try:
            import numpy as np
        except ImportError:
            raise RuntimeError("numpy required for metrics; install it or set val_split=0 to skip evaluation.")
        preds, labels = eval_pred
        if isinstance(preds, tuple):  # some trainer versions return (logits, ...)
            preds = preds[0]
        import numpy as np
        preds_arr = np.array(preds)
        # If logits provided (ndim == 3), take argmax
        if preds_arr.ndim == 3:
            preds_arr = preds_arr.argmax(-1)
        preds_list = preds_arr.tolist()
        decoded_preds = postprocess_text(preds_list)
        labels_arr = np.array(labels)
        if labels_arr.ndim > 2:  # reduce if extra dims
            labels_arr = labels_arr[..., 0]
        labels_list = labels_arr.tolist()
        # Replace -100 with pad_token_id
        labels_list = [[(tok if tok != -100 else pad_token_id) for tok in seq] for seq in labels_list]
        decoded_labels = postprocess_text(labels_list)
        # Exact match metric
        exact = np.mean([1.0 if p.strip() == l.strip() else 0.0 for p, l in zip(decoded_preds, decoded_labels)])
        # Token-level accuracy (rough)
        token_accs = []
        for p, l in zip(decoded_preds, decoded_labels):
            p_tokens = p.split()
            l_tokens = l.split()
            if not l_tokens:
                continue
            match = sum(1 for a, b in zip(p_tokens, l_tokens) if a == b)
            token_accs.append(match / max(len(l_tokens), 1))
        token_acc = float(np.mean(token_accs)) if token_accs else 0.0
        return {"exact_match": exact, "token_accuracy": token_acc}

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics if eval_ds is not None else None,
    )

    print("[train_model] Starting training…")
    trainer.train()
    if eval_ds is not None:
        print("[train_model] Final evaluation…")
        metrics = trainer.evaluate()
        print(f"[train_model] Eval metrics: {metrics}")

    print(f"[train_model] Saving to {output_dir_path}")
    trainer.save_model(str(output_dir_path))
    tokenizer.save_pretrained(str(output_dir_path))

    print("[train_model] Done.")
    return str(output_dir_path)


if __name__ == "__main__":  # Allow: python -m netops_backend.chatbot.nlp_engine.train_model
    # Basic CLI argument parsing (optional simple overrides)
    import argparse
    p = argparse.ArgumentParser(description="Train NL->CLI model")
    p.add_argument("--model", default="t5-small")
    p.add_argument("--dataset", default=None)
    p.add_argument("--out", default="./cli_model")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--val-split", type=float, default=0.0, help="Fraction of data for validation (0-1). 0 to disable.")
    args = p.parse_args()
    train_cli_model(
        model_name=args.model,
        dataset_file=args.dataset,
        output_dir=args.out,
        epochs=args.epochs,
        batch_size=args.batch,
        learning_rate=args.lr,
        val_split=args.val_split,
    )
