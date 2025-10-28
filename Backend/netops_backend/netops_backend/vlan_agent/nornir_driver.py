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
    """Create a VLAN following hierarchical flow: Core → Access switches.

    Hierarchy:
    - Core switch: INVIJB1SW1 (Cisco) - primary
    - Access switches: INHYDB3SW3 (Aruba), UKLONB1SW2 (Cisco)
    
    Flow:
    1. Create on core switch first
    2. If successful, propagate to all access switches
    3. Skip if VLAN already exists on any device
    
    vlan_plan expects: {"vlan_id": int, "name": str, "scope": str?}
    Returns {alias: "created"|"skipped"|"failed"}
    """
    logger = get_logger()
    vlan_id = int(vlan_plan.get("vlan_id"))
    name = str(vlan_plan.get("name", f"VLAN{vlan_id}"))
    validate_vlan_id(vlan_id)

    inventory = get_devices()  # alias -> device dict
    summary: Dict[str, str] = {}
    
    # Define hierarchy: core switch first, then access switches
    CORE_SWITCH = "INVIJB1SW1"
    ACCESS_SWITCHES = ["INHYDB3SW3", "UKLONB1SW2"]
    
    # Step 1: Deploy to Core Switch
    log_event(logging.INFO, f"Starting hierarchical VLAN deployment: Core → Access", vlan_id=vlan_id)
    
    core_dev = inventory.get(CORE_SWITCH)
    if not core_dev:
        log_event(logging.ERROR, "Core switch not found in inventory", device=CORE_SWITCH)
        summary[CORE_SWITCH] = "failed"
        return summary
    
    # Deploy to core
    core_result = _deploy_to_single_device(CORE_SWITCH, core_dev, vlan_id, name, is_core=True)
    summary[CORE_SWITCH] = core_result
    
    # If core deployment failed completely, stop propagation
    if core_result == "failed":
        log_event(logging.ERROR, f"Core switch deployment failed - aborting access switch propagation", vlan_id=vlan_id)
        for access_alias in ACCESS_SWITCHES:
            summary[access_alias] = "skipped (core failed)"
        return summary
    
    # Step 2: Propagate to Access Switches
    log_event(logging.INFO, f"Core switch {core_result} - propagating to access switches", vlan_id=vlan_id, device=CORE_SWITCH)
    
    for access_alias in ACCESS_SWITCHES:
        access_dev = inventory.get(access_alias)
        if not access_dev:
            log_event(logging.WARNING, "Access switch not found in inventory", device=access_alias)
            summary[access_alias] = "failed"
            continue
        
        access_result = _deploy_to_single_device(access_alias, access_dev, vlan_id, name, is_core=False)
        summary[access_alias] = access_result
    
    return summary


def _deploy_to_single_device(alias: str, dev: dict, vlan_id: int, name: str, is_core: bool) -> str:
    """Deploy VLAN to a single device. Returns 'created'|'skipped'|'failed'."""
    device_role = "Core" if is_core else "Access"
    params = _netmiko_params_from_device(alias, dev)
    
    try:
        log_event(logging.INFO, f"Connecting to {device_role} switch", device=alias, host=params.get("host"))
        with ConnectHandler(**params) as conn:
            device_type = params.get("device_type", "")
            
            # Check if VLAN exists
            if _vlan_exists(conn, vlan_id, device_type):
                log_event(logging.INFO, f"VLAN {vlan_id} already exists on {device_role} switch", device=alias)
                return "skipped"
            
            # Create VLAN
            _configure_vlan(conn, vlan_id, name, device_type)
            log_event(logging.INFO, f"VLAN {vlan_id} created on {device_role} switch", device=alias)
            return "created"
            
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        log_event(logging.ERROR, f"Connection error on {device_role} switch: {e}", device=alias)
        return "failed"
    except Exception as e:
        log_event(logging.ERROR, f"Unhandled error on {device_role} switch: {e}", device=alias)
        return "failed"


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
