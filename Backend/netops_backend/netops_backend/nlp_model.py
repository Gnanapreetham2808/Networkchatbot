"""Local T5 NL->CLI inference utilities.

Model directory resolution order:
1. Environment variable CLI_MODEL_PATH (absolute or relative to this file's parent)
2. ./t5_cli_v5 (preferred)
3. ../chatbot/nlp_engine/t5_cli_model_v5 (preferred location)
4. ./t5_cli_v3 (legacy fallback)
5. ../chatbot/nlp_engine/t5_cli_model_v3 (legacy fallback)
6. Any directory in ../chatbot/nlp_engine whose name starts with t5_cli and contains model files

Exports predict_cli(query: str) -> str returning one decoded CLI command (or
an error string prefixed with [Error]).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import json
import shutil
import tempfile
import threading

from transformers import T5ForConditionalGeneration, AutoTokenizer
try:
    from peft import PeftModel, LoraConfig
    _PEFT_AVAILABLE = True
except Exception:
    _PEFT_AVAILABLE = False

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

    # 2. Preferred v5 sibling name
    candidates.append(base / "t5_cli_v5")
    # 3. Preferred v5 model path inside nlp_engine
    candidates.append(base.parent / "chatbot" / "nlp_engine" / "t5_cli_model_v5")

    # 4. Legacy v3 names (fallback)
    candidates.append(base / "t5_cli_v3")
    candidates.append(base.parent / "chatbot" / "nlp_engine" / "t5_cli_model_v3")

    # 6. Any t5_cli* directory inside nlp_engine
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
    raise FileNotFoundError("No valid full model directory found. Tried: " + "; ".join(errors))


def _find_adapter_dir() -> Optional[Path]:
    """Return path to a LoRA adapter directory if available.

    Resolution order:
    1) CLI_ADAPTER_PATH env var (absolute or relative to this file)
    2) Any directory under ../chatbot/nlp_engine containing adapter_config.json
    3) Prefer names like t5_cli_lora_v5*
    """
    base = Path(__file__).resolve().parent
    env_path = os.getenv("CLI_ADAPTER_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = base / p
        if (p / "adapter_config.json").exists():
            return p
    # Explicit preferred adapter name priority (new LoRA folder): t5_cli_lora_v5_final
    preferred_names_order = [
        "t5_cli_lora_v5_final",
        "t5_cli_lora_v5",
        "t5_cli_lora_v5_final"  # duplicate safe entry for clarity
    ]
    # scan recursively for adapter_config.json (handle nested duplicated folder names)
    nlp_engine_dir = base.parent / "chatbot" / "nlp_engine"
    if nlp_engine_dir.exists():
        # prefer v5-named adapters
        preferred: list[Path] = []
        others: list[Path] = []
        for ap in nlp_engine_dir.rglob("adapter_config.json"):
            cand = ap.parent
            name = cand.name.lower()
            if name in preferred_names_order:
                # Insert preserving the explicit order priority
                if cand not in preferred:
                    preferred.append(cand)
            elif "lora" in name and "v5" in name:
                preferred.append(cand)
            else:
                others.append(cand)
        # Reorder preferred by our explicit list first
        ordered_pref: list[Path] = []
        for pname in preferred_names_order:
            for c in preferred:
                if c.name.lower() == pname and c not in ordered_pref:
                    ordered_pref.append(c)
        # append any remaining preferred not in ordered list
        for c in preferred:
            if c not in ordered_pref:
                ordered_pref.append(c)
        preferred = ordered_pref
        if preferred:
            return preferred[0]
        if others:
            return others[0]
    return None


def _lazy_load():
    global _MODEL, _TOKENIZER
    if _MODEL is not None:
        return
    with _LOCK:
        if _MODEL is not None:
            return
        global _CHOSEN_MODEL_DIR
        # Environment controls:
        #  CLI_DISABLE_ADAPTER=1 -> skip adapter even if found
        #  CLI_REQUIRE_ADAPTER=1 -> error if adapter cannot be applied
        disable_adapter = os.getenv("CLI_DISABLE_ADAPTER", "0") == "1"
        require_adapter = os.getenv("CLI_REQUIRE_ADAPTER", "0") == "1"

        adapter_dir = None if disable_adapter else _find_adapter_dir()

        # Try adapter-based loading first if adapter present and peft available and not disabled
        if adapter_dir and _PEFT_AVAILABLE:
            base_hint = os.getenv("CLI_BASE_MODEL_PATH")
            base_model: Optional[Path] = None
            if base_hint:
                bh = Path(base_hint)
                if not bh.is_absolute():
                    bh = Path(__file__).resolve().parent / bh
                base_model = bh
            else:
                # Reuse any available full model dir (legacy v3) as base to avoid downloads
                try:
                    base_model = _select_model_dir()
                except Exception:
                    base_model = None

            if base_model and (base_model / "config.json").exists():
                _CHOSEN_MODEL_DIR = adapter_dir
                print(f"[nlp_model] Loading base model from {base_model} with adapter {adapter_dir}")
                _TOKENIZER = AutoTokenizer.from_pretrained(str(base_model))
                base = T5ForConditionalGeneration.from_pretrained(str(base_model))
                try:
                    _MODEL = PeftModel.from_pretrained(base, str(adapter_dir))
                except TypeError as e:
                    # Handle unexpected keys in adapter_config by sanitizing
                    if "unexpected keyword" in str(e) or "got an unexpected keyword" in str(e):
                        try:
                            cfg_path = Path(adapter_dir) / "adapter_config.json"
                            with open(cfg_path, "r", encoding="utf-8") as f:
                                cfg = json.load(f)
                            allowed = set(getattr(LoraConfig, "__dataclass_fields__", {}).keys())
                            sanitized = {k: v for k, v in cfg.items() if k in allowed}
                            # Ensure mandatory defaults if missing
                            if "task_type" not in sanitized and "task_type" in cfg:
                                sanitized["task_type"] = cfg["task_type"]
                            temp_dir = Path(tempfile.mkdtemp(prefix="adapter_sanitized_"))
                            # write sanitized config
                            with open(temp_dir / "adapter_config.json", "w", encoding="utf-8") as out:
                                json.dump(sanitized, out)
                            # copy weights
                            for wname in ("adapter_model.safetensors", "adapter_model.bin"):
                                src = Path(adapter_dir) / wname
                                if src.exists():
                                    shutil.copy2(src, temp_dir / wname)
                            print(f"[nlp_model] Using sanitized adapter config at {temp_dir}")
                            _MODEL = PeftModel.from_pretrained(base, str(temp_dir))
                        except Exception as se:
                            raise se
                    else:
                        raise
                device = os.getenv("CLI_MODEL_DEVICE", "cpu")
                _MODEL.to(device)
                _MODEL.eval()
                print(f"[nlp_model] Adapter model loaded on device={device}")
                return
            else:
                # If adapter exists but no local base, do not auto-download; instruct via error in predict
                _CHOSEN_MODEL_DIR = adapter_dir
                _TOKENIZER = None
                _MODEL = None
                if require_adapter:
                    raise RuntimeError("Adapter base model missing and CLI_REQUIRE_ADAPTER=1")
        # Fallback: full model directory
        _CHOSEN_MODEL_DIR = _select_model_dir()
        print(f"[nlp_model] Loading model from {_CHOSEN_MODEL_DIR}")
        _TOKENIZER = AutoTokenizer.from_pretrained(str(_CHOSEN_MODEL_DIR))
        _MODEL = T5ForConditionalGeneration.from_pretrained(str(_CHOSEN_MODEL_DIR))
        device = os.getenv("CLI_MODEL_DEVICE", "cpu")
        _MODEL.to(device)
        _MODEL.eval()
        if adapter_dir and not _PEFT_AVAILABLE and require_adapter:
            raise RuntimeError("peft not installed but CLI_REQUIRE_ADAPTER=1")
        origin = "(adapter skipped)" if disable_adapter and adapter_dir else ""
        print(f"[nlp_model] Model loaded on device={device} {origin}")


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
        return f"[Error] Model load failed: {e} | tried full models: {candidates}"
    try:
        if _MODEL is None or _TOKENIZER is None:
            # Provide explicit guidance if adapter was found but base missing
            adapter_dir = _find_adapter_dir()
            return (
                f"[Error] Model not initialized. If using LoRA adapter, set CLI_BASE_MODEL_PATH to a local base T5 "
                f"directory matching the adapter and ensure adapter at {adapter_dir} is valid."
            )
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
