# chatbot/nlp_engine/intent.py
from transformers import pipeline
from .config import MODEL_INTENT, INTENT_MIN_SCORE

intent_classifier = pipeline("zero-shot-classification", model=MODEL_INTENT)

def classify_intent(text, candidate_labels=None):
    if candidate_labels is None:
        candidate_labels = ["show", "configure", "reset", "ping", "chit-chat"]
    res = intent_classifier(text, candidate_labels=candidate_labels)
    label = res["labels"][0]
    score = float(res["scores"][0])
    return {"label": label if score >= INTENT_MIN_SCORE else "unknown", "score": score}
