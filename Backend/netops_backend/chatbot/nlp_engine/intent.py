"""Lightweight intent detection using sentence-transformers embeddings.

We avoid large zero-shot models and instead embed the user query and a small
set of canonical intent descriptions, computing cosine similarity.

Model: all-MiniLM-L6-v2 (~22MB) chosen for speed & acceptable semantic quality.
Lazy loaded on first call; if model import fails we fall back to keyword rules.
"""

from __future__ import annotations
import os
from typing import List, Dict

from math import isclose

_EMBED_MODEL = None  # (SentenceTransformer) or False when permanently unavailable
_INTENT_EMB = None   # Cached tensor / list of embeddings for intents

# Canonical intents and short natural descriptions (improves embedding separation)
INTENT_DEFINITIONS = [
    {"label": "show", "desc": "retrieve or display device status / information"},
    {"label": "configure", "desc": "apply configuration changes to the device"},
    {"label": "reset", "desc": "reset, restart or clear a service or device"},
    {"label": "ping", "desc": "test connectivity to an IP or host with ping"},
    {"label": "troubleshoot", "desc": "diagnose issues or gather debug information"},
    {"label": "chit-chat", "desc": "casual or conversational message not a network task"},
]

_INTENT_MIN_SCORE = float(os.getenv("INTENT_MIN_SCORE", 0.45))

def _load_embed_model():
    global _EMBED_MODEL, _INTENT_EMB
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL if _EMBED_MODEL is not False else None
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        # Pre-compute embeddings for intent descriptions
        _INTENT_EMB = _EMBED_MODEL.encode([i["desc"] for i in INTENT_DEFINITIONS], normalize_embeddings=True)
        print("[intent] Loaded sentence-transformer all-MiniLM-L6-v2")
    except Exception as e:  # Broad by design: missing deps, etc.
        print("[intent] Embed model unavailable:", e)
        _EMBED_MODEL = False
        _INTENT_EMB = None
        return None
    return _EMBED_MODEL


def _keyword_fallback(text: str) -> Dict:
    lower = text.lower()
    for i in INTENT_DEFINITIONS:
        if i["label"] in lower:
            return {"label": i["label"], "score": 0.4, "fallback": True}
    # simple synonyms
    synonyms = {
        "display": "show",
        "list": "show",
        "get": "show",
        "reboot": "reset",
        "restart": "reset",
        "debug": "troubleshoot",
    }
    for k, v in synonyms.items():
        if k in lower:
            return {"label": v, "score": 0.35, "fallback": True}
    return {"label": "unknown", "score": 0.0, "fallback": True}


def classify_intent(text: str) -> Dict:
    """Return top intent with confidence.

    Response schema:
        { label: str, score: float, embedding: optional(list), fallback: bool? }
    """
    # Fast heuristic: direct CLI style starting with known verbs
    lower = text.lower().strip()
    if lower.startswith("show "):
        return {"label": "show", "score": 0.9, "heuristic": True}
    if lower.startswith("ping "):
        return {"label": "ping", "score": 0.9, "heuristic": True}
    if lower.startswith("traceroute "):
        return {"label": "troubleshoot", "score": 0.8, "heuristic": True}

    model = _load_embed_model()
    if not model:
        return _keyword_fallback(text)
    try:
        import numpy as np
        q_emb = model.encode([text], normalize_embeddings=True)
        # cosine similarity = dot since normalized
        sims = (q_emb @ _INTENT_EMB.T)[0]
        best_idx = int(sims.argmax())
        best = float(sims[best_idx])
        label = INTENT_DEFINITIONS[best_idx]["label"] if best >= _INTENT_MIN_SCORE else "unknown"
        return {"label": label, "score": round(best, 4)}
    except Exception as e:
        print("[intent] inference error -> fallback:", e)
        return _keyword_fallback(text)
