from transformers import pipeline
from pathlib import Path
import os
import threading

_LOCK = threading.Lock()
_GEN = None
_LOADED = None
_BASE = Path(__file__).resolve().parent

def _candidates():
    # Highest priority: explicit env variable
    env_path = os.getenv("CLI_MODEL_PATH")
    if env_path:
        p = (_BASE / env_path) if not os.path.isabs(env_path) else Path(env_path)
        yield p
    # Specific user provided folder
    yield _BASE / "t5_cli_model_v1"
    # Older / fallback folders
    yield _BASE / "cli_model_kaggle"
    yield _BASE / "cli_modeltrain1"
    yield _BASE / "cli_model_train1_run2"
    yield _BASE / "cli_model"

def _init():
    global _GEN, _LOADED
    if _GEN is not None:
        return
    with _LOCK:
        if _GEN is not None:
            return
        last_err = None
        for cand in _candidates():
            try:
                if (cand / "config.json").exists():
                    _GEN = pipeline("text2text-generation", model=str(cand))
                    _LOADED = str(cand)
                    print(f"[cli_interface] Loaded model: {_LOADED}")
                    break
            except Exception as e:
                last_err = e
                continue
        if _GEN is None:
            print(f"[cli_interface] No model loaded (last_err={last_err})")

def nl_to_cli(query: str) -> str:
    if _GEN is None:
        _init()
    if _GEN is None:
        return "[Error] No trained model found."
    try:
        result = _GEN(query, max_length=int(os.getenv("CLI_MODEL_MAX_LEN", "64")), num_return_sequences=1)
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"[Error] Failed to generate command: {e}"

if __name__ == "__main__":
    for q in ["Show me all interfaces", "Check device version", "Display routing table"]:
        print(q, "->", nl_to_cli(q))
