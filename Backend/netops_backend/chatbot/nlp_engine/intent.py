"""Lightweight intent module.

Existing views expect a function classify_intent(text) returning a dict with at
least a 'label' key (e.g. {'label': 'show', 'score': 0.93, ...}). The file was
simplified and the original function removed, which caused an ImportError.

We reintroduce classify_intent while keeping a very fast heuristic approach.
If you later restore the embedding model, keep the same return structure.
"""

from __future__ import annotations

SHOW_KEYWORDS = ["show", "display", "check", "list", "view"]


def detect_intent(user_input: str) -> str:
    """Basic internal helper returning coarse intent code."""
    text = user_input.lower()
    if any(k in text.split() or k in text for k in SHOW_KEYWORDS):
        return "view"
    return "unknown"


def classify_intent(text: str) -> dict:
    """Public API used by views.

    Maps internal 'view' intent to legacy label 'show' for compatibility with
    downstream logic (e.g. adding implicit 'show').
    """
    base = detect_intent(text)
    if base == "view":
        label = "show"
        score = 0.85  # heuristic confidence placeholder
    else:
        label = "unknown"
        score = 0.40
    return {
        "label": label,
        "score": score,
        "raw": base,
        "engine": "heuristic-v1",
    }

