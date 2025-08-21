"""Entity extraction using HF NER model plus custom regex for network objects.

Model: dslim/bert-base-NER (lightweight, general domain). We augment it with
regex for IP addresses, interfaces, and VLAN IDs.
Lazy loaded: model only instantiated on first call.
"""

from __future__ import annotations
import re
from typing import List, Dict

_NER_PIPE = None  # pipeline instance or False
_MIN_SCORE = 0.50

IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
IFACE_RE = re.compile(r"\b(?:GigabitEthernet|FastEthernet|Ethernet|TenGigabitEthernet|Loopback|Port-?channel|Po\d+|Gi\d+/\d+(?:/\d+)?|Fa\d+/\d+(?:/\d+)?|Te\d+/\d+(?:/\d+)?)\S*\b", re.I)
VLAN_RE = re.compile(r"\bvlan\s*(\d{1,4})\b", re.I)


def _load_pipe():
    global _NER_PIPE
    if _NER_PIPE is not None:
        return _NER_PIPE if _NER_PIPE is not False else None
    try:
        from transformers import pipeline
        _NER_PIPE = pipeline("token-classification", model="dslim/bert-base-NER", aggregation_strategy="simple")
        print("[ner] Loaded dslim/bert-base-NER")
    except Exception as e:
        print("[ner] load failed:", e)
        _NER_PIPE = False
        return None
    return _NER_PIPE


def extract_entities(query: str) -> Dict:
    pipe = _load_pipe()
    results = []
    if pipe:
        try:
            for ent in pipe(query):
                if float(ent.get("score", 0)) >= _MIN_SCORE:
                    results.append({
                        "entity_group": ent.get("entity_group"),
                        "word": ent.get("word"),
                        "score": float(ent.get("score", 0))
                    })
        except Exception as e:
            print("[ner] inference error (continuing with regex only):", e)
    # Regex augment
    for m in IP_RE.finditer(query):
        results.append({"entity_group": "IP", "word": m.group(), "score": 1.0})
    for m in IFACE_RE.finditer(query):
        results.append({"entity_group": "INTERFACE", "word": m.group(), "score": 1.0})
    for m in VLAN_RE.finditer(query):
        results.append({"entity_group": "VLAN", "word": m.group(1), "score": 1.0})
    return {"entities": results}
