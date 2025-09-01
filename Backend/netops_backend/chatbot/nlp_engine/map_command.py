"""Simplified rule-based command mapper with legacy return shape.

Views expect map_to_cli(query) -> dict containing at least 'command'. The file
was reduced to return only a string which broke attribute access.
"""

from __future__ import annotations
from typing import Dict, List
import os
try:
    from .cli_interface import nl_to_cli as _nl_to_cli
    _MODEL_OK = True
except Exception:
    _MODEL_OK = False

COMMAND_MAP = {
    "interfaces": "show ip interface brief",
    "interface status": "show interfaces status",
    "vlan": "show vlan brief",
    "routing table": "show ip route",
    "routes": "show ip route",
    "running config": "show running-config",
    "startup config": "show startup-config",
    "cpu": "show processes cpu",
    "memory": "show processes memory",
    "arp": "show arp",
    "mac": "show mac address-table",
    "bgp": "show ip bgp summary",
    "ospf": "show ip ospf neighbor",
    "cdp": "show cdp neighbors",
    "lldp": "show lldp neighbors",
    "spanning tree": "show spanning-tree",
}


def map_to_cli(user_input: str) -> Dict:
    text = user_input.lower()
    matches: List[str] = []
    for key, cmd in COMMAND_MAP.items():
        if key in text:
            matches.append(cmd)
    if matches:
        # Pick first; simple heuristic score (longer key higher) omitted for brevity
        chosen = matches[0]
        return {
            "command": chosen,
            "candidates": matches,
            "source": "rule",
            "score": 0.9,
        }
    # Model fallback
    if os.getenv("USE_MODEL_MAPPING", "1") == "1" and _MODEL_OK:
        gen = _nl_to_cli(user_input)
        if gen and not gen.startswith("[Error]"):
            return {
                "command": gen.strip(),
                "candidates": [gen.strip()],
                "source": "model",
                "score": 0.5,
                "note": "model fallback",
            }
    return {
        "command": "",
        "candidates": [],
        "source": "rule",
        "score": 0.0,
        "note": "no rule match"
    }

