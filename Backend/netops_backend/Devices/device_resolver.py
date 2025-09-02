"""Device alias resolution utilities.

Loads a JSON mapping of device aliases to connection parameters and provides
resolve_device(query: str) -> (device_dict|None, candidates:list[str], error:str|None)

Heuristics:
 - Direct alias mention (exact key, case-insensitive)
 - Phrase patterns mapping "vijayawada building 1 switch 1" -> INVIJB1SW1
 - If ambiguous (multiple matches) returns candidates.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Tuple, List, Optional

_BASE = Path(__file__).resolve().parent
_DEVICES_PATH = _BASE / "devices.json"
_CACHE: Optional[Dict[str, dict]] = None


def _load_devices() -> Dict[str, dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not _DEVICES_PATH.exists():
        _CACHE = {}
        return _CACHE
    try:
        with open(_DEVICES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalise keys uppercase
        _CACHE = {k.upper(): v for k, v in data.items()}
    except Exception:
        _CACHE = {}
    return _CACHE


_PHRASE_MAP = {
    # canonical phrase -> alias
    re.compile(r"vijayawada\s+building\s*1\s+switch\s*1", re.I): "INVIJB1SW1",
    re.compile(r"vijayawada\s+building\s*1\s+switch\s*2", re.I): "INVIJB1SW2",
}


def resolve_device(query: str) -> Tuple[Optional[dict], List[str], Optional[str]]:
    devices = _load_devices()
    if not devices:
        return None, [], "No devices configured"

    q = (query or "").strip()
    if not q:
        return None, [], "Empty query"

    upper_q = q.upper()
    # 1. Direct alias match token-wise
    direct_matches = [alias for alias in devices.keys() if alias in upper_q]
    if len(direct_matches) == 1:
        return devices[direct_matches[0]], [], None
    if len(direct_matches) > 1:
        return None, direct_matches, "Multiple aliases mentioned"

    # 2. Phrase mapping
    phrase_hits = []
    for pattern, alias in _PHRASE_MAP.items():
        if pattern.search(q):
            phrase_hits.append(alias)
    if len(phrase_hits) == 1:
        return devices.get(phrase_hits[0]), [], None
    if len(phrase_hits) > 1:
        return None, phrase_hits, "Multiple phrase matches"

    # 3. Partial fuzzy: any alias with shared substring of building or switch keywords
    if re.search(r"vijayawada", q, re.I) and re.search(r"switch", q, re.I):
        # return all switches in that site if numbering ambiguous
        site_candidates = [a for a in devices.keys() if a.startswith("INVIJB1SW")] or list(devices.keys())
        if len(site_candidates) == 1:
            return devices[site_candidates[0]], [], None
        return None, site_candidates, "Ambiguous switch reference"

    return None, [], "No matching device"


if __name__ == "__main__":
    for q in [
        "show interfaces on INVIJB1SW1",
        "Vijayawada building 1 switch 1 interfaces",
        "Vijayawada switch",
    ]:
        dev, cand, err = resolve_device(q)
        print(q, "->", dev, cand, err)
