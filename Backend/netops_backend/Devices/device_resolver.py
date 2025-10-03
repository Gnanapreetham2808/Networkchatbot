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
import os
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import difflib

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


def get_devices() -> Dict[str, dict]:
    """Return the devices map (uppercase aliases)."""
    # Respect hot reload flag
    if os.getenv("DEVICES_RELOAD_EACH_REQUEST", "0") == "1":  # pragma: no cover
        global _CACHE
        _CACHE = None
    return _load_devices()


def find_device_by_host(host: str) -> Tuple[Optional[str], Optional[dict]]:
    """Find a device by its host/IP and return (alias, device_dict with alias set)."""
    if not host:
        return None, None
    devices = get_devices()
    for alias, dev in devices.items():
        primary = str(dev.get("host"))
        if primary == str(host):
            return alias, _attach_alias(alias, dev)
        # also look at optional alt_hosts list
        alt_hosts = dev.get("alt_hosts") or []
        try:
            for ah in alt_hosts:
                if str(ah) == str(host):
                    return alias, _attach_alias(alias, dev)
        except Exception:  # pragma: no cover
            pass
    return None, None


_PHRASE_MAP = {
    # canonical phrase -> alias
    re.compile(r"vijayawada\s+building\s*1\s+switch\s*1", re.I): "INVIJB1SW1",
    # Generic building 1 with no explicit city defaults to Vijayawada primary
    re.compile(r"\bbuilding\s*1\b", re.I): "INVIJB1SW1",
}

# Simple location keyword to alias preference (fallback when no explicit alias)
_LOCATION_KEYWORDS = [
    # Expanded Vijayawada synonyms (short forms or partials) map to primary alias
    (re.compile(r"\b(vij|vijay|vijaya|vijayawada|india)\b", re.I), "INVIJB1SW1"),
    (re.compile(r"\b(london|uk)\b", re.I), "UKLONB1SW2"),
]

# Known location keys for fuzzy matching
_FUZZY_KEYS = ["london", "uk", "vijayawada", "vij", "vijay", "vijaya", "building 1"]


def _attach_alias(alias: str, dev: dict | None) -> Optional[dict]:
    if not dev:
        return None
    if "alias" not in dev:
        dev = {**dev, "alias": alias}
    return dev


def _best_uk_alias(devices: Dict[str, dict]) -> Optional[str]:
    # prefer UKLONB2SW2, then UKLONB1SW2, then any UKLONB*, then any UK*
    for pref in ["UKLONB1SW2"]:
        if pref in devices:
            return pref
    for k in devices.keys():
        if k.startswith("UKLONB"):
            return k
    for k in devices.keys():
        if k.startswith("UK"):
            return k
    return None


def _best_in_alias(devices: Dict[str, dict]) -> Optional[str]:
    # prefer INVIJB1SW1, then any INVIJB1SW*
    if "INVIJB1SW1" in devices:
        return "INVIJB1SW1"
    for k in devices.keys():
        if k.startswith("INVIJB1SW"):
            return k
    return None


def _fuzzy_location_hits(q: str) -> List[str]:
    # find close matches for location keys within tokens/reduced text
    text = q.lower()
    tokens = re.findall(r"[a-z0-9]+(?:\s+[a-z0-9]+)?", text)
    hits: List[str] = []
    for key in _FUZZY_KEYS:
        # exact
        if key in text:
            hits.append(key)
            continue
        # fuzzy on tokens
        parts = key.split()
        if len(parts) == 1:
            for t in text.split():
                if difflib.get_close_matches(key, [t], n=1, cutoff=0.8):
                    hits.append(key)
                    break
        else:
            # multi-word like "building 1"
            if difflib.get_close_matches(key, tokens, n=1, cutoff=0.8):
                hits.append(key)
    # de-duplicate preserving order
    seen = set()
    ordered = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered


def resolve_device(query: str) -> Tuple[Optional[dict], List[str], Optional[str]]:
    # Optional hot reload each request if env flag set (useful during editing/dev)
    if os.getenv("DEVICES_RELOAD_EACH_REQUEST", "0") == "1":  # pragma: no cover
        global _CACHE
        _CACHE = None
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
        return _attach_alias(direct_matches[0], devices[direct_matches[0]]), [], None
    if len(direct_matches) > 1:
        return None, direct_matches, "Multiple aliases mentioned"

    # 2. Phrase mapping
    phrase_hits = []
    for pattern, alias in _PHRASE_MAP.items():
        if pattern.search(q):
            phrase_hits.append(alias)
    if len(phrase_hits) == 1:
        return _attach_alias(phrase_hits[0], devices.get(phrase_hits[0])), [], None
    if len(phrase_hits) > 1:
        return None, phrase_hits, "Multiple phrase matches"

    # 3. UKLONB1SWN style parsing: country(UK) city(LON) building(B1) switch(SW2)
    m = re.search(r"\b(UK)([A-Z]{3})B(\d+)SW(\d+)\b", upper_q)
    if m:
        alias = m.group(0)
        if alias in devices:
            return _attach_alias(alias, devices[alias]), [], None
        # otherwise suggest candidates from same city/building
        city = m.group(2)
        bld = m.group(3)
        prefix = f"UK{city}B{bld}SW"
        cands = [a for a in devices.keys() if a.startswith(prefix)]
        if len(cands) == 1:
            return devices[cands[0]], [], None
        if cands:
            return None, cands, "Ambiguous switch reference"

    # 4. Fuzzy location matching and mapping to preferred alias by site
    fuzzy_hits = _fuzzy_location_hits(q)
    mapped_aliases: List[str] = []
    for key in fuzzy_hits:
        if key in ("london", "uk"):
            mapped_aliases.append("UKLONB1SW2")
        elif key in ("vijayawada", "vij", "vijay", "vijaya", "building 1"):
            mapped_aliases.append("INVIJB1SW1")

    # Reduce to single site if both UK and IN appear -> ambiguous
    mapped_aliases = list(dict.fromkeys(mapped_aliases))  # dedupe preserve order
    if len(mapped_aliases) == 1:
        target = mapped_aliases[0]
        if target not in devices:
            # fallback within site
            target = _best_uk_alias(devices) if target.startswith("UK") else _best_in_alias(devices)
        if target and target in devices:
            return _attach_alias(target, devices[target]), [], None
    elif len(mapped_aliases) > 1:
        # both regions mentioned -> offer candidates from both sites
        uk = _best_uk_alias(devices)
        inv = _best_in_alias(devices)
        cand = [a for a in [uk, inv] if a]
        return None, cand or list(devices.keys()), "Multiple location matches"

    # 5. Simple location keyword preference (exact)
    matched = [alias for pattern, alias in _LOCATION_KEYWORDS if pattern.search(q)]
    matched = list(dict.fromkeys(matched))
    if len(matched) == 1:
        alias = matched[0]
        if alias not in devices:
            alias = _best_uk_alias(devices) if alias.startswith("UK") else _best_in_alias(devices)
        if alias and alias in devices:
            return _attach_alias(alias, devices[alias]), [], None
    if len(matched) > 1:
        # multiple locations mentioned
        uk = _best_uk_alias(devices)
        inv = _best_in_alias(devices)
        cand = [a for a in [uk, inv] if a]
        return None, cand or list(devices.keys()), "Multiple location matches"

    return None, [], "No matching device"


if __name__ == "__main__":
    for q in [
        "show interfaces on INVIJB1SW1",
        "Vijayawada building 1 switch 1 interfaces",
        "Vijayawada switch",
    ]:
        dev, cand, err = resolve_device(q)
        print(q, "->", dev, cand, err)
