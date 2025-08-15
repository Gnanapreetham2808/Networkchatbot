"""Command mapping with rule base + optional model (lazy loaded)."""

from .config import MODEL_MAP, MAP_MIN_SCORE
import re

_TOK = None
_MODEL = None  # False if unavailable


def _load_model():
    global _TOK, _MODEL
    if _MODEL is not None:
        return _TOK, (_MODEL if _MODEL is not False else None)
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        _TOK = AutoTokenizer.from_pretrained(MODEL_MAP)
        _MODEL = AutoModelForSeq2SeqLM.from_pretrained(MODEL_MAP)
        print(f"[map_command] Loaded mapping model: {MODEL_MAP}")
    except Exception as e:
        print("[map_command] Mapping model unavailable:", e)
        _MODEL = False
        return None, None
    return _TOK, _MODEL

# Simple rule base for frequent read-only queries
RULE_SHOW_MAP = [
    (re.compile(r"^show +ip +int(erface)? +brief$", re.I), "show ip interface brief"),
    (re.compile(r"^show +ver(sion)?$", re.I), "show version"),
    (re.compile(r"^show +run(n?ing)?( +config)?$", re.I), "show running-config"),
    (re.compile(r"^show +int(erfaces?)?( +status)?$", re.I), "show interfaces status"),
    (re.compile(r"^show +cdp +nei(ghbors)?$", re.I), "show cdp neighbors"),
    (re.compile(r"^show +ip +route$", re.I), "show ip route"),
    (re.compile(r"^show +vlan(s)?$", re.I), "show vlan"),
]

# Unsupported feature detector (basic)
UNSUPPORTED_PATTERNS = [
    (re.compile(r"\bnetconf\b", re.I), "NETCONF not enabled on target device"),
    (re.compile(r"\bgpt\b", re.I), "GPT operations unsupported on device"),
]

_ALLOWED_CHARS_RE = re.compile(r"[^a-zA-Z0-9_:.\-/ ]+")

def _sanitize_generated(raw: str) -> str:
    if not raw:
        return raw
    # Remove literal 'Command:' markers & everything after last valid command token repetition
    cleaned = raw.replace('\n', ' ')
    # Remove repeated 'Command:' artifacts
    cleaned = re.sub(r'(?i)\bcommand:?', ' ', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Token-level cleanup & repetition collapse
    tokens = cleaned.split()
    # Remove consecutive duplicate token runs (e.g., show show ip ip)
    dedup = []
    for t in tokens:
        if not dedup or dedup[-1].lower() != t.lower():
            dedup.append(t)
    tokens = dedup
    # Truncate to reasonable length
    tokens = tokens[:10]
    cleaned = ' '.join(tokens)
    # Strip disallowed chars
    cleaned = _ALLOWED_CHARS_RE.sub('', cleaned).strip()
    # Remove trailing leftover words that are just duplicates of earlier pattern
    # e.g., 'show ip interface brief show ip interface' -> keep first unique sequence
    if cleaned.lower().startswith('show '):
        # Deduplicate trailing repetition sequence
        parts = cleaned.split()
        for window in range(len(parts)//2, 1, -1):
            if parts[:window] == parts[window:2*window]:
                cleaned = ' '.join(parts[:window])
                break
    return cleaned

def map_to_cli(text):
    original = text.strip()
    lower = original.lower()

    # 1. Unsupported detection
    unsupported_reason = None
    for pat, msg in UNSUPPORTED_PATTERNS:
        if pat.search(original):
            unsupported_reason = msg
            break

    # 2. Rule-based mapping
    for pat, cmd in RULE_SHOW_MAP:
        if pat.match(lower):
            return {
                "command": cmd,
                "raw": cmd,
                "sanitized": False,
                "score": 0.95,
                "safe": True,
                "rule": True,
                "unsupported": unsupported_reason
            }

    # 3. Model-based fallback
    tok, model = _load_model()
    raw_out = ""
    if tok and model:
        try:
            prompt = f"Convert the user's request into a single network CLI command. Output ONLY the command.\n{text}\nCommand:"
            x = tok(prompt, return_tensors="pt")
            y = model.generate(**x, max_new_tokens=18, num_beams=4, early_stopping=True)
            raw_out = tok.decode(y[0], skip_special_tokens=True).strip()
        except Exception as e:
            print("[map_command] Inference failed, fallback to heuristic:", e)
            raw_out = original
    else:
        # Heuristic fallback: just return original if it starts with known verbs, else prepend 'show'
        if lower.startswith(('show ', 'ping ', 'traceroute ')):
            raw_out = original
        else:
            raw_out = f"show {original}".strip()
    sanitized = _sanitize_generated(raw_out)
    if not sanitized and lower.startswith(('show ', 'ping ', 'traceroute ')):
        sanitized = original
    score = max(0.3, min(0.99, 1.0 - (len(sanitized or raw_out) / 160.0)))
    return {
        "command": sanitized or raw_out,
        "raw": raw_out,
        "sanitized": sanitized != raw_out,
        "score": score,
        "safe": bool(sanitized) and score >= MAP_MIN_SCORE,
        "rule": False,
        "unsupported": unsupported_reason
    }
