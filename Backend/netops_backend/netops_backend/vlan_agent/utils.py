"""Utility helpers for vlan_agent."""
from __future__ import annotations

from typing import Iterable, Dict, Any, List, Tuple, Optional
import logging
import re

from .models import VLANIntent


def validate_vlan_id(vlan_id: int) -> None:
    if not (1 <= int(vlan_id) <= 4094):
        raise ValueError("VLAN ID must be within 1..4094")


def normalize_vlan_name(name: str) -> str:
    return (name or "").strip()[:64]


def validate_vlan_id_uniqueness(intents: Iterable[VLANIntent]) -> Tuple[List[VLANIntent], Dict[int, str]]:
    """Ensure no duplicate vlan_id exists within the same scope among provided intents.

    Returns (valid_intents, error_map_by_intent_id)
    """
    seen = set()
    valid: List[VLANIntent] = []
    errors: Dict[int, str] = {}
    for intent in intents:
        key = (intent.scope, intent.vlan_id)
        if key in seen:
            errors[intent.id] = f"Duplicate VLAN {intent.vlan_id} in scope '{intent.scope}'"
            continue
        seen.add(key)
        valid.append(intent)
    return valid, errors


def build_config_actions(intents: Iterable[VLANIntent]) -> List[Dict[str, Any]]:
    """Translate intents into abstract actions for the orchestrator."""
    actions: List[Dict[str, Any]] = []
    for i in intents:
        actions.append({
            "intent_id": i.id,
            "action": "ensure_vlan",
            "vlan_id": i.vlan_id,
            "name": i.name,
            "scope": i.scope,
        })
    return actions


# --- logging helpers ---

_LOGGER_NAME = "netops_backend.vlan_agent"


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)


def log_event(level: int, msg: str, *, device: Optional[str] = None, **extra: Any) -> None:
    logger = get_logger()
    if device:
        extra = {**extra, "device": device}
    try:
        logger.log(level, msg, extra=extra)
    except Exception:
        # Avoid logging failures impacting control flow
        logger.log(level, msg)


def generate_vlan_intent_from_text(command: str) -> Dict[str, Any]:
    """Parse free-text into a VLAN intent dict.

    This is a local, regex-based heuristic parser. It avoids any network calls.
    Returns: {"vlan_id": int, "name": str, "scope": str}
    """
    text = (command or "").strip()
    log_event(20, "Parsing VLAN intent from text", query=text)

    # Defaults
    vlan_id: Optional[int] = None
    name: Optional[str] = None
    scope = "access"

    # Extract VLAN ID (first integer after 'vlan' or any plausible 1..4094)
    m = re.search(r"\bvlan\s*(?:id\s*)?(\d{1,4})\b", text, re.I)
    if m:
        try:
            vid = int(m.group(1))
            if 1 <= vid <= 4094:
                vlan_id = vid
        except Exception:
            pass
    if vlan_id is None:
        # Any standalone number that looks like a VLAN ID
        m2 = re.search(r"\b(\d{1,4})\b", text)
        if m2:
            try:
                vid = int(m2.group(1))
                if 1 <= vid <= 4094:
                    vlan_id = vid
            except Exception:
                pass

    # Extract name after keywords: name, called, label, as
    m = re.search(r"\b(name|called|label|as)\s*[:=\-]?\s*([A-Za-z0-9_\-\. ]{2,})", text, re.I)
    if m:
        name = normalize_vlan_name(m.group(2))
    # If still none, try words like 'VLAN <id> <name>'
    if name is None:
        m2 = re.search(r"\bvlan\s*\d{1,4}\s+([A-Za-z0-9_\-\.]{2,})", text, re.I)
        if m2:
            name = normalize_vlan_name(m2.group(1))
    if name is None:
        name = f"VLAN-{vlan_id if vlan_id else 'pending'}"

    # Extract scope tokens
    if re.search(r"\bcore\b", text, re.I):
        scope = "core"
    elif re.search(r"\b(dist(ribution)?|l3)\b", text, re.I):
        scope = "distribution"
    elif re.search(r"\baccess\b", text, re.I):
        scope = "access"

    if vlan_id is None:
        raise ValueError("Could not parse a valid VLAN ID from text")

    parsed = {"vlan_id": vlan_id, "name": name, "scope": scope}
    log_event(20, "Parsed VLAN intent", **parsed)
    return parsed
