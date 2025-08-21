"""Simplified rule-based command mapper with legacy return shape.

Views expect map_to_cli(query) -> dict containing at least 'command'. The file
was reduced to return only a string which broke attribute access.
"""

from __future__ import annotations
from typing import Dict, List

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
    return {
        "command": "",
        "candidates": [],
        "source": "rule",
        "score": 0.0,
        "note": "no rule match"
    }

