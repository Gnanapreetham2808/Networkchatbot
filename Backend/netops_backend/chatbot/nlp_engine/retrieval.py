"""Retrieval / logging stubs.

Original module provided log_interaction / retrieve_similar for semantic recall.
User edits replaced it with a translation model causing import mismatches. We
restore lightweight placeholders so the API layer does not break.
"""

from __future__ import annotations
from typing import List, Dict
import time

_HISTORY: List[Dict] = []


def log_interaction(query: str, output: str) -> None:
    """Store minimal interaction history (in-memory)."""
    _HISTORY.append({
        "ts": time.time(),
        "query": query,
        "output_preview": output[:200],
    })


def retrieve_similar(query: str, k: int = 3) -> List[Dict]:
    """Naive lexical similarity over stored queries (placeholder)."""
    parts = set(query.lower().split())
    scored = []
    for item in _HISTORY:
        overlap = len(parts.intersection(item["query"].lower().split()))
        scored.append((overlap, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [i for _, i in scored[:k] if _ > 0]

