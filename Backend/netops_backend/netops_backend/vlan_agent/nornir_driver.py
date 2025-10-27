"""Network driver/orchestrator utilities for VLAN deployment and validation.

Implementation notes:
- Prefer Nornir/Scrapli if you choose to wire them in; this scaffold uses Netmiko
    and the existing Devices/devices.json inventory via device_resolver for now.
"""
from __future__ import annotations

from typing import Any, Dict, List, Iterable, Optional
from dataclasses import dataclass
import re
import logging

from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

from .models import VLANIntent
from .utils import validate_vlan_id, get_logger, log_event
from Devices.device_resolver import get_devices


@dataclass
class ChangePlan:
    intent_id: int
    actions: List[Dict[str, Any]]


class VLANOrchestrator:
    """Orchestrator skeleton. Replace methods with real device logic."""

    def plan(self, intent: VLANIntent) -> ChangePlan:
        validate_vlan_id(intent.vlan_id)
        actions = [
            {
                "action": "ensure_vlan",
                "vlan_id": intent.vlan_id,
                "name": intent.name,
                "scope": intent.scope,
            }
        ]
        return ChangePlan(intent_id=intent.id, actions=actions)

    def apply(self, plan: ChangePlan) -> None:
        # Placeholder: In production, connect to devices and execute actions idempotently.
        # This method intentionally does nothing in the scaffold.
        return

    # --- bulk helpers for view action ---
    def deploy_vlan_actions(self, actions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deploy a list of VLAN actions across target devices.

        Placeholder implementation that pretends all actions succeed.
        Returns a list of per-action results: {action: ..., ok: bool, error?: str}
        """
        results: List[Dict[str, Any]] = []
        for act in actions:
            results.append({"action": act, "ok": True})
        return results


# ---- Device-level VLAN deployment and validation ----

def _netmiko_params_from_device(alias: str, dev: dict) -> dict:
    params = {
        "device_type": dev.get("device_type", "cisco_ios"),
        "host": dev.get("host"),
        "username": dev.get("username"),
        "password": dev.get("password"),
        "port": int(dev.get("port", 22)),
        "fast_cli": False,
    }
    return params


def _vlan_exists(connection: ConnectHandler, vlan_id: int, device_type: str) -> bool:
    try:
        if "cisco" in device_type:
            out = connection.send_command("show vlan brief", use_textfsm=False)
        elif "aruba_aoscx" in device_type:
            out = connection.send_command("show vlan", use_textfsm=False)
        else:
            out = connection.send_command("show vlan", use_textfsm=False)
    except Exception:
        return False
    # Simple regex: line starts with VLAN ID (whitespace allowed), or contains 'VLAN <id>'
    pat = re.compile(rf"(^|\n)\s*{vlan_id}\b", re.M)
    return bool(pat.search(out or ""))


def _configure_vlan(connection: ConnectHandler, vlan_id: int, name: str, device_type: str) -> None:
    cfg = []
    if "cisco" in device_type:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    elif "aruba_aoscx" in device_type:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    else:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    connection.send_config_set(cfg)


def deploy_vlan_to_switches(vlan_plan: Dict[str, Any]) -> Dict[str, str]:
    """Create a VLAN across core/access switches, skipping existing ones.

    vlan_plan expects: {"vlan_id": int, "name": str, "scope": str?, "targets": [aliases]?}
    Returns {alias: "created"|"skipped"|"failed"}
    """
    logger = get_logger()
    vlan_id = int(vlan_plan.get("vlan_id"))
    name = str(vlan_plan.get("name", f"VLAN{vlan_id}"))
    validate_vlan_id(vlan_id)

    inventory = get_devices()  # alias -> device dict
    targets: List[str] = vlan_plan.get("targets") or list(inventory.keys())
    summary: Dict[str, str] = {}

    for alias in targets:
        dev = inventory.get(alias.upper())
        if not dev:
            log_event(logging.WARNING, "Device not found in inventory", device=alias)
            summary[alias] = "failed"
            continue
        params = _netmiko_params_from_device(alias, dev)
        try:
            log_event(logging.INFO, f"Connecting to device", device=alias, host=params.get("host"))
            with ConnectHandler(**params) as conn:
                device_type = params.get("device_type", "")
                if _vlan_exists(conn, vlan_id, device_type):
                    log_event(logging.INFO, f"VLAN {vlan_id} exists -> skipped", device=alias)
                    summary[alias] = "skipped"
                    continue
                _configure_vlan(conn, vlan_id, name, device_type)
                log_event(logging.INFO, f"VLAN {vlan_id} created", device=alias)
                summary[alias] = "created"
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            log_event(logging.ERROR, f"Connection error: {e}", device=alias)
            summary[alias] = "failed"
        except Exception as e:  # pragma: no cover
            log_event(logging.ERROR, f"Unhandled error: {e}", device=alias)
            summary[alias] = "failed"

    return summary


def validate_vlan_propagation(vlan_id: int) -> Dict[str, str]:
    """Verify VLAN presence across all devices.

    Returns {alias: "ok"|"missing"|"conflict"}
    Currently, "conflict" is reserved for unexpected errors during checks.
    """
    logger = get_logger()
    validate_vlan_id(vlan_id)
    inventory = get_devices()
    result: Dict[str, str] = {}

    for alias, dev in inventory.items():
        params = _netmiko_params_from_device(alias, dev)
        try:
            log_event(logging.INFO, "Checking VLAN propagation", device=alias, vlan_id=vlan_id)
            with ConnectHandler(**params) as conn:
                device_type = params.get("device_type", "")
                exists = _vlan_exists(conn, vlan_id, device_type)
                result[alias] = "ok" if exists else "missing"
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            log_event(logging.ERROR, f"Connection error during validation: {e}", device=alias)
            result[alias] = "conflict"
        except Exception as e:  # pragma: no cover
            log_event(logging.ERROR, f"Unhandled validation error: {e}", device=alias)
            result[alias] = "conflict"

    return result
