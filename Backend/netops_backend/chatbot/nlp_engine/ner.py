# chatbot/nlp_engine/ner.py
from transformers import pipeline
import re
from .config import MODEL_NER, NER_MIN_SCORE

ner_model = pipeline("token-classification", model=MODEL_NER, aggregation_strategy="simple")

IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
IFACE_RE = re.compile(r"\b(?:GigabitEthernet|FastEthernet|Ethernet|TenGigabitEthernet)\S*\b", re.I)
VLAN_RE = re.compile(r"\bvlan\s*(\d{1,4})\b", re.I)

def extract_entities(text):
    model_ents = [e for e in ner_model(text) if float(e.get("score", 0)) >= NER_MIN_SCORE]
    extras = []
    for m in IP_RE.finditer(text):
        extras.append({"entity_group": "IP", "word": m.group()})
    for m in IFACE_RE.finditer(text):
        extras.append({"entity_group": "INTERFACE", "word": m.group()})
    for m in VLAN_RE.finditer(text):
        extras.append({"entity_group": "VLAN", "word": m.group(1)})
    return {"entities": model_ents + extras}
