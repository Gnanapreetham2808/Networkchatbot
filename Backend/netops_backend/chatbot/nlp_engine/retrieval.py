"""Lightweight retrieval cache for (query -> command -> output) triples.

Design:
 - In-memory list acts as a mini vector store (cleared on restart).
 - SentenceTransformer embeddings (all-MiniLM-L6-v2) lazy loaded.
 - For each new executed command you may call log_interaction(query, command, output).
 - retrieve_similar(query) returns top similar historical queries.
"""

from __future__ import annotations
import os
from typing import List, Dict

_MODEL = None
_STORE: List[Dict] = []  # each: {query, command, output, emb}
_MAX_STORE = int(os.getenv("RETRIEVAL_MAX", 200))
_MIN_SIM = float(os.getenv("RETRIEVAL_MIN_SIM", 0.70))

def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL if _MODEL is not False else None
    if os.getenv("NLP_DISABLE_RETRIEVAL", "0") == "1":
        _MODEL = False
        return None
    try:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print("[retrieval] Loaded all-MiniLM-L6-v2")
    except Exception as e:
        print("[retrieval] model load failed:", e)
        _MODEL = False
        return None
    return _MODEL

def log_interaction(query: str, command: str, output: str):
    model = _load_model()
    if not model:
        return
    try:
        emb = model.encode([query], normalize_embeddings=True)[0]
        _STORE.append({"query": query, "command": command, "output": output, "emb": emb})
        if len(_STORE) > _MAX_STORE:
            del _STORE[: len(_STORE) - _MAX_STORE]
    except Exception:
        pass

def retrieve_similar(query: str, k: int = 3):
    model = _load_model()
    if not model or not _STORE:
        return {"results": []}
    try:
        import numpy as np
        q_emb = model.encode([query], normalize_embeddings=True)[0]
        embs = np.array([item["emb"] for item in _STORE])
        sims = embs @ q_emb
        idxs = sims.argsort()[-k:][::-1]
        results = []
        for idx in idxs:
            score = float(sims[idx])
            if score < _MIN_SIM:
                continue
            item = _STORE[idx]
            results.append({
                "query": item["query"],
                "command": item["command"],
                "score": round(score, 4),
            })
        return {"results": results}
    except Exception as e:
        print("[retrieval] similarity error:", e)
        return {"results": []}
