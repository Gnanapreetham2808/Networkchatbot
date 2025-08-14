# chatbot/nlp_engine/config.py

MODEL_INTENT = "facebook/bart-large-mnli"
MODEL_NER = "dslim/bert-base-NER"
MODEL_MAP = "t5-small"
MODEL_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"

INTENT_MIN_SCORE = 0.55
NER_MIN_SCORE = 0.50
MAP_MIN_SCORE = 0.50
