"""Named entity extraction with lazy model load + regex heuristics."""

import re
from .config import MODEL_NER, NER_MIN_SCORE

_NER_MODEL = None  # None not tried, False unavailable


def _get_ner_model():
    global _NER_MODEL
    if _NER_MODEL is not None:
        return _NER_MODEL if _NER_MODEL is not False else None
    try:
        from transformers import pipeline
        _NER_MODEL = pipeline("token-classification", model=MODEL_NER, aggregation_strategy="simple")
        print(f"[ner] Loaded NER model: {MODEL_NER}")
    except Exception as e:
        print("[ner] NER model unavailable:", e)
        _NER_MODEL = False
        return None
    return _NER_MODEL


IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
IFACE_RE = re.compile(r"\b(?:GigabitEthernet|FastEthernet|Ethernet|TenGigabitEthernet)\S*\b", re.I)
VLAN_RE = re.compile(r"\bvlan\s*(\d{1,4})\b", re.I)


def extract_entities(text):
    model = _get_ner_model()
    model_ents = []
    if model:
        try:
            model_ents = [e for e in model(text) if float(e.get("score", 0)) >= NER_MIN_SCORE]
        except Exception as e:
            print("[ner] model inference failed, continuing with regex only:", e)
            model_ents = []
    extras = []
    for m in IP_RE.finditer(text):
        extras.append({"entity_group": "IP", "word": m.group()})
    for m in IFACE_RE.finditer(text):
        extras.append({"entity_group": "INTERFACE", "word": m.group()})
    for m in VLAN_RE.finditer(text):
        extras.append({"entity_group": "VLAN", "word": m.group(1)})
    return {"entities": model_ents + extras}
