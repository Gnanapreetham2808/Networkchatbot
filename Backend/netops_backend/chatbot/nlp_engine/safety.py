"""Command safety gating.

Primary logic:
 - Allow-list read-only prefixes: show, ping, traceroute
 - Immediate block / confirmation for destructive or high-risk keywords
 - Optional lightweight semantic fallback: embed command and compare to small
   unsafe set (only if sentence-transformers available).
"""

from __future__ import annotations
import os

BASE_PREFIXES = ["show", "ping", "traceroute"]
SENSITIVE_KEYWORDS = [
    "delete", "erase", "format", "reload", "shutdown", "write erase", "factory-reset",
]
HARD_BLOCK = ["format", "write erase", "factory-reset"]

_UNSAFE_EMBED = None  # (model, unsafe_emb)
_UNSAFE_TEXTS = [
    "delete configuration",
    "erase flash",
    "reset device to factory",
    "format disk",
    "shutdown all interfaces",
]

def _load_unsafe_embeddings():
    global _UNSAFE_EMBED
    if _UNSAFE_EMBED is not None:
        return _UNSAFE_EMBED if _UNSAFE_EMBED is not False else None
    if os.getenv("SAFETY_SEMANTIC", "1") != "1":
        _UNSAFE_EMBED = False
        return None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb = model.encode(_UNSAFE_TEXTS, normalize_embeddings=True)
        _UNSAFE_EMBED = (model, emb)
        print("[safety] Semantic unsafe detector enabled")
    except Exception as e:
        print("[safety] semantic embedding load failed:", e)
        _UNSAFE_EMBED = False
        return None
    return _UNSAFE_EMBED

def _semantic_unsafe_score(cmd: str):
    ctx = _load_unsafe_embeddings()
    if not ctx:
        return 0.0
    try:
        model, emb = ctx
        q = model.encode([cmd], normalize_embeddings=True)
        import numpy as np
        sims = (q @ emb.T)[0]
        return float(sims.max())
    except Exception:
        return 0.0

def gate_command(command: str):
    c = command.strip().lower()
    allowed_prefix = any(c == p or c.startswith(p + " ") for p in BASE_PREFIXES)
    sensitive = any(k in c for k in SENSITIVE_KEYWORDS)
    hard_block = any(k in c for k in HARD_BLOCK)

    if hard_block:
        return {"allowed": False, "needs_confirmation": False, "reason": "hard blocked destructive command"}

    if allowed_prefix and sensitive:
        return {"allowed": False, "needs_confirmation": True, "reason": "sensitive operation requires confirmation"}

    if allowed_prefix and not sensitive:
        # still run semantic to catch weird phrasing
        score = _semantic_unsafe_score(c)
        if score >= 0.7:
            return {"allowed": False, "needs_confirmation": True, "reason": f"semantic risk score {score:.2f}"}
        return {"allowed": True, "needs_confirmation": False, "reason": "allowed prefix"}

    # Not on allow-list -> disallow unless semantic says extremely safe (kept simple)
    return {"allowed": False, "needs_confirmation": False, "reason": "not in allow-list"}
