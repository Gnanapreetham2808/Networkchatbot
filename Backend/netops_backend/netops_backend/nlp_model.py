"""Local T5 NL->CLI inference utilities.

Model directory resolution order:
1. Environment variable CLI_MODEL_PATH (absolute or relative to this file's parent)
2. ./t5_cli_v3 (legacy name next to this file)
3. ../chatbot/nlp_engine/t5_cli_model_v3 (location you reported)
4. Any directory in ../chatbot/nlp_engine whose name starts with t5_cli and contains model files

Exports predict_cli(query: str) -> str returning one decoded CLI command (or
an error string prefixed with [Error]).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import threading

from transformers import T5ForConditionalGeneration, AutoTokenizer

_LOCK = threading.Lock()
_MODEL: Optional[T5ForConditionalGeneration] = None
_TOKENIZER = None
_CHOSEN_MODEL_DIR: Optional[Path] = None
_MAX_LEN = int(os.getenv("CLI_MODEL_MAX_LEN", "64"))


def _candidate_model_dirs() -> list[Path]:
    base = Path(__file__).resolve().parent
    project_root = base  # netops_backend package dir
    candidates: list[Path] = []

    # 1. Explicit env var
    env_path = os.getenv("CLI_MODEL_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = base / p
        candidates.append(p)

    # 2. Legacy sibling name
    candidates.append(base / "t5_cli_v3")
    # 3. Reported actual path (../chatbot/nlp_engine/t5_cli_model_v3)
    candidates.append(base.parent / "chatbot" / "nlp_engine" / "t5_cli_model_v3")

    # 4. Any t5_cli* directory inside nlp_engine
    nlp_engine_dir = base.parent / "chatbot" / "nlp_engine"
    if nlp_engine_dir.exists():
        for d in sorted(nlp_engine_dir.glob("t5_cli*")):
            if d.is_dir():
                candidates.append(d)

    # Remove duplicates preserving order
    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _select_model_dir() -> Path:
    errors = []
    for cand in _candidate_model_dirs():
        if cand.exists():
            # quick heuristic: must have config.json and tokenizer / model weights
            needed = ["config.json"]
            if all((cand / f).exists() for f in needed):
                return cand
            errors.append(f"{cand} (missing required files)")
        else:
            errors.append(f"{cand} (not found)")
    raise FileNotFoundError("No valid model directory found. Tried: " + "; ".join(errors))


def _lazy_load():
    global _MODEL, _TOKENIZER
    if _MODEL is not None:
        return
    with _LOCK:
        if _MODEL is not None:
            return
        global _CHOSEN_MODEL_DIR
        _CHOSEN_MODEL_DIR = _select_model_dir()
        print(f"[nlp_model] Loading model from {_CHOSEN_MODEL_DIR}")
        _TOKENIZER = AutoTokenizer.from_pretrained(str(_CHOSEN_MODEL_DIR))
        _MODEL = T5ForConditionalGeneration.from_pretrained(str(_CHOSEN_MODEL_DIR))
        device = os.getenv("CLI_MODEL_DEVICE", "cpu")
        _MODEL.to(device)
        _MODEL.eval()
        print(f"[nlp_model] Model loaded on device={device}")


def predict_cli(query: str) -> str:
    """Generate a CLI command from a natural language query.

    Returns an error string (prefixed with [Error]) on failure instead of raising.
    """
    if not query or not query.strip():
        return "[Error] Empty query"
    try:
        _lazy_load()
    except Exception as e:
        # Include candidate dirs in error for easier debugging
        candidates = [str(p) for p in _candidate_model_dirs()]
        return f"[Error] Model load failed: {e} | tried: {candidates}"
    try:
        inputs = _TOKENIZER(
            query.strip(),
            return_tensors="pt",
            truncation=True,
            max_length=_MAX_LEN,
        )
        device = next(_MODEL.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        gen_ids = _MODEL.generate(
            **inputs,
            max_length=_MAX_LEN,
            num_beams=4,
            early_stopping=True,
        )
        text = _TOKENIZER.decode(gen_ids[0], skip_special_tokens=True).strip()
        return text or "[Error] Empty generation"
    except Exception as e:
        return f"[Error] Generation failed: {e}"


if __name__ == "__main__":  # quick manual test
    for q in ["show interfaces", "device version", "routing table"]:
        print(q, "->", predict_cli(q))
