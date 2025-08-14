# chatbot/nlp_engine/retrieval.py
from sentence_transformers import SentenceTransformer, util
from .config import MODEL_EMBEDDINGS

embed_model = SentenceTransformer(MODEL_EMBEDDINGS)

KB_TEXTS = [
    "Use 'show ip interface brief' to list interfaces with IPs and status.",
    "Use 'show version' to view the device OS and uptime.",
    "Use 'show mac address-table' to inspect MAC learning."
]
KB_EMB = embed_model.encode(KB_TEXTS, convert_to_tensor=True, normalize_embeddings=True)

def retrieve(query, k=3):
    q_emb = embed_model.encode([query], convert_to_tensor=True, normalize_embeddings=True)
    hits = util.semantic_search(q_emb, KB_EMB, top_k=k)[0]
    return {"results": [{"score": float(h["score"]), "text": KB_TEXTS[h["corpus_id"]]} for h in hits]}
