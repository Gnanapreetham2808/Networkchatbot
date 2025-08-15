"""Intent classification with lazy model loading.

Avoid loading heavy models (which require torch) at import time to keep Django
startup fast and allow basic health checks even if ML deps aren't installed yet.
"""

from __future__ import annotations

from .config import MODEL_INTENT, INTENT_MIN_SCORE

_INTENT_CLF = None  # None: not tried, False: unavailable


def _get_intent_classifier():
    global _INTENT_CLF
    if _INTENT_CLF is not None:
        return _INTENT_CLF if _INTENT_CLF is not False else None
    try:
        from transformers import pipeline  # local import
        _INTENT_CLF = pipeline("zero-shot-classification", model=MODEL_INTENT)
        print(f"[intent] Loaded intent model: {MODEL_INTENT}")
    except Exception as e:
        print("[intent] Intent model unavailable:", e)
        _INTENT_CLF = False
        return None
    return _INTENT_CLF


def classify_intent(text, candidate_labels=None):
    if candidate_labels is None:
        candidate_labels = ["show", "configure", "reset", "ping", "chit-chat"]
    clf = _get_intent_classifier()
    if not clf:
        # Heuristic fallback: simple keyword scan
        lower = text.lower()
        for kw in ["show", "configure", "reset", "ping"]:
            if kw in lower:
                return {"label": kw, "score": 0.5, "fallback": True}
        return {"label": "unknown", "score": 0.0, "fallback": True}
    res = clf(text, candidate_labels=candidate_labels)
    label = res["labels"][0]
    score = float(res["scores"][0])
    return {"label": label if score >= INTENT_MIN_SCORE else "unknown", "score": score}
