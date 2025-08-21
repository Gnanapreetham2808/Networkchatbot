"""Retrieval-based mapping of natural language queries to CLI commands.

Uses the same embedding model as intent (all-MiniLM-L6-v2). We store a catalog
of (description -> CLI) pairs and perform cosine similarity search.
If FAISS is available we use it; else we fall back to a NumPy cosine search.
"""

from __future__ import annotations
import os
from typing import List, Dict

# --- Expanded catalog (~120 mappings) ---
CATALOG: List[Dict[str, str]] = [
    # General
    {"desc": "device software version and uptime", "command": "show version"},
    {"desc": "system information", "command": "show version"},
    {"desc": "running configuration", "command": "show running-config"},
    {"desc": "startup configuration", "command": "show startup-config"},
    {"desc": "system uptime", "command": "show version"},
    {"desc": "show system logs", "command": "show logging"},

    # Interfaces
    {"desc": "list interfaces brief", "command": "show ip interface brief"},
    {"desc": "interface status", "command": "show interfaces status"},
    {"desc": "interface statistics", "command": "show interfaces"},
    {"desc": "check interface errors", "command": "show interfaces counters errors"},
    {"desc": "interface descriptions", "command": "show interfaces description"},
    {"desc": "show ipv6 interfaces brief", "command": "show ipv6 interface brief"},

    # Routing
    {"desc": "routing table entries", "command": "show ip route"},
    {"desc": "ipv6 routing table", "command": "show ipv6 route"},
    {"desc": "ospf neighbors", "command": "show ip ospf neighbor"},
    {"desc": "ospf status", "command": "show ip ospf"},
    {"desc": "eigrp neighbors", "command": "show ip eigrp neighbors"},
    {"desc": "bgp summary", "command": "show ip bgp summary"},
    {"desc": "bgp peers", "command": "show ip bgp summary"},
    {"desc": "bgp advertised routes", "command": "show ip bgp neighbors advertised-routes"},

    # ARP / MAC
    {"desc": "arp table", "command": "show arp"},
    {"desc": "mac address table", "command": "show mac address-table"},
    {"desc": "mac for interface", "command": "show mac address-table interface"},

    # VLAN
    {"desc": "list vlans", "command": "show vlan brief"},
    {"desc": "vlan configuration", "command": "show vlan"},
    {"desc": "show vlan id", "command": "show vlan id"},

    # Discovery
    {"desc": "neighbor discovery information", "command": "show cdp neighbors"},
    {"desc": "cdp neighbors detail", "command": "show cdp neighbors detail"},
    {"desc": "lldp neighbors", "command": "show lldp neighbors"},
    {"desc": "lldp status", "command": "show lldp"},

    # Security
    {"desc": "show access lists", "command": "show access-lists"},
    {"desc": "firewall rules", "command": "show access-lists"},
    {"desc": "ip access lists", "command": "show ip access-lists"},
    {"desc": "ipsec associations", "command": "show crypto ipsec sa"},
    {"desc": "vpn sessions", "command": "show crypto session"},

    # Logs / System
    {"desc": "show processes", "command": "show processes"},
    {"desc": "cpu usage", "command": "show processes cpu"},
    {"desc": "memory usage", "command": "show processes memory"},
    {"desc": "environment status", "command": "show environment all"},
    {"desc": "temperature", "command": "show environment temperature"},

    # Switching
    {"desc": "spanning tree status", "command": "show spanning-tree"},
    {"desc": "trunk interfaces", "command": "show interfaces trunk"},
    {"desc": "switchport details", "command": "show interfaces switchport"},

    # Wireless
    {"desc": "wireless summary", "command": "show wireless summary"},
    {"desc": "connected clients", "command": "show wireless client summary"},
    {"desc": "show wlan", "command": "show wlan"},

    # Users / Sessions
    {"desc": "show users", "command": "show users"},
    {"desc": "active sessions", "command": "show sessions"},

    # Utilities
    {"desc": "ping an ip address", "command": "ping"},
    {"desc": "trace route to destination", "command": "traceroute"},

    # ⚠ Sensitive (needs confirmation)
    {"desc": "configure terminal", "command": "configure terminal"},
    {"desc": "shutdown interface", "command": "interface <id> shutdown"},
    {"desc": "enable interface", "command": "interface <id> no shutdown"},
    {"desc": "assign ip to interface", "command": "interface <id> ip address <ip> <mask>"},
    {"desc": "save configuration", "command": "write memory"},
    {"desc": "reload device", "command": "reload"},
]

# --- Embedding search logic stays the same ---
_EMBED_MODEL = None
_CAT_EMB = None
_USE_FAISS = False
_FAISS_INDEX = None
_MIN_SCORE = float(os.getenv("MAP_MIN_SCORE", 0.45))

def _load_embeddings():
    global _EMBED_MODEL, _CAT_EMB, _USE_FAISS, _FAISS_INDEX
    if _EMBED_MODEL is not None:
        return True if _EMBED_MODEL is not False else False
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [c["desc"] for c in CATALOG]
        _CAT_EMB = _EMBED_MODEL.encode(texts, normalize_embeddings=True)
        try:
            import faiss  # optional
            dim = _CAT_EMB.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(_CAT_EMB)
            _FAISS_INDEX = index
            _USE_FAISS = True
            print("[map_command] Using FAISS index")
        except Exception:
            _USE_FAISS = False
            print("[map_command] FAISS not available, using NumPy search")
        print("[map_command] Loaded embeddings for", len(CATALOG), "commands")
        return True
    except Exception as e:
        print("[map_command] Embedding load failed:", e)
        _EMBED_MODEL = False
        return False

def _search(query: str):
    import numpy as np
    if not _load_embeddings():
        return None
    try:
        q_emb = _EMBED_MODEL.encode([query], normalize_embeddings=True)
        if _USE_FAISS and _FAISS_INDEX is not None:
            D, I = _FAISS_INDEX.search(q_emb, k=3)
            pairs = zip(I[0], D[0])
        else:
            sims_vec = (q_emb @ _CAT_EMB.T)[0]
            idxs = sims_vec.argsort()[-3:][::-1]
            pairs = [(i, sims_vec[i]) for i in idxs]
        results = []
        for idx, sim in pairs:
            if idx < 0:
                continue
            score = float(sim)
            results.append({
                "command": CATALOG[idx]["command"],
                "desc": CATALOG[idx]["desc"],
                "score": round(score, 4)
            })
        return results
    except Exception as e:
        print("[map_command] search error:", e)
        return None

def map_to_cli(query: str) -> Dict:
    results = _search(query)
    if not results:
        lower = query.strip().lower()
        if lower.startswith(("show ", "ping ", "traceroute ")):
            return {"command": query.strip(), "score": 0.3, "candidates": [], "fallback": True}
        return {"command": f"show {query.strip()}", "score": 0.25, "candidates": [], "fallback": True}
    best = results[0]
    if best["score"] < _MIN_SCORE:
        best_cmd = best["command"] if best["score"] >= (_MIN_SCORE * 0.6) else f"show {query.strip()}"
        return {"command": best_cmd, "score": best["score"], "candidates": results, "fallback": True}
    return {"command": best["command"], "score": best["score"], "candidates": results}
