"""Network driver/orchestrator utilities for VLAN deployment and validation.

Implementation notes:
- Prefer Nornir/Scrapli if you choose to wire them in; this scaffold uses Netmiko
    and the existing Devices/devices.json inventory via device_resolver for now.
- Uses vendor-specific prompts for agentic VLAN creation via LLM
"""
from __future__ import annotations

from typing import Any, Dict, List, Iterable, Optional
from dataclasses import dataclass
import re
import logging
import os

from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

from .models import VLANIntent
from .utils import validate_vlan_id, get_logger, log_event
from Devices.device_resolver import get_devices
from .prompts import (
    get_vlan_creation_prompt,
    get_vlan_deletion_prompt,
    format_vlan_query,
    get_vlan_validation_command
)


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
    """
    Configure VLAN using hardcoded commands (fallback method).
    
    For agentic/LLM-based creation, use _configure_vlan_agentic() instead.
    """
    cfg = []
    if "cisco" in device_type:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    elif "aruba_aoscx" in device_type:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    else:
        cfg = [f"vlan {vlan_id}", f"name {name}"]
    connection.send_config_set(cfg)


def deploy_vlan_to_device(selector: str, vlan_id: int, name: str) -> Dict[str, Any]:
    """Create a VLAN on a single device identified by alias or host IP.

    Args:
        selector: Alias (case-insensitive) or host IP from devices.json
        vlan_id: VLAN ID
        name: VLAN name

    Returns:
        Dict with keys: alias, host, status, error?, commands?, output?
    """
    logger = get_logger()
    validate_vlan_id(vlan_id)
    devices = get_devices() or {}
    alias = None
    dev = None
    sel_upper = str(selector or '').upper()
    # Prefer alias match
    if sel_upper in devices:
        alias = sel_upper
        dev = devices[alias]
    else:
        # Try host match
        for k, v in devices.items():
            if str(v.get('host')) == str(selector):
                alias = k
                dev = v
                break
    if not dev or not alias:
        return {"status": "failed", "error": f"Device not found for selector '{selector}'"}

    params = _netmiko_params_from_device(alias, dev)
    try:
        log_event(logging.INFO, "Connecting to device for single VLAN create", device=alias, host=params.get('host'))
        with ConnectHandler(**params) as conn:
            dtype = params.get('device_type', '')
            if _vlan_exists(conn, vlan_id, dtype):
                return {"alias": alias, "host": params.get('host'), "status": "skipped", "reason": "exists"}

            # Agentic vs hardcoded
            use_agentic = os.getenv("ENABLE_AGENTIC_VLAN_CREATION", "0") == "1"
            if use_agentic:
                result = _configure_vlan_agentic(conn, vlan_id, name, dtype, use_llm=True)
                if result.get("status") == "success":
                    return {"alias": alias, "host": params.get('host'), "status": "created", **result}
                return {"alias": alias, "host": params.get('host'), "status": "failed", "error": result.get("error"), **result}
            else:
                _configure_vlan(conn, vlan_id, name, dtype)
                return {"alias": alias, "host": params.get('host'), "status": "created", "method": "hardcoded"}
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        log_event(logging.ERROR, f"Connection error: {e}", device=alias)
        return {"alias": alias, "host": params.get('host'), "status": "failed", "error": str(e)}
    except Exception as e:
        log_event(logging.ERROR, f"Unhandled error: {e}", device=alias)
        return {"alias": alias, "host": params.get('host'), "status": "failed", "error": str(e)}


def _configure_vlan_agentic(
    connection: ConnectHandler, 
    vlan_id: int, 
    name: str, 
    device_type: str,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    Configure VLAN using agentic approach with vendor-specific LLM prompts.
    
    Args:
        connection: Netmiko connection object
        vlan_id: VLAN ID to create
        name: VLAN name
        device_type: Device type (cisco_ios, aruba_aoscx, etc.)
        use_llm: If True, use LLM to generate commands; if False, use hardcoded commands
    
    Returns:
        Dict with status, commands executed, and output
    """
    from netops_backend.nlp_router import predict_cli_provider
    
    logger = get_logger()
    result = {
        "status": "success",
        "vlan_id": vlan_id,
        "vlan_name": name,
        "device_type": device_type,
        "commands": [],
        "output": "",
        "method": "agentic" if use_llm else "hardcoded"
    }
    
    try:
        if use_llm and os.getenv("ENABLE_AGENTIC_VLAN_CREATION", "0") == "1":
            # Use vendor-specific prompt for LLM
            vendor_prompt = get_vlan_creation_prompt(device_type)
            query = format_vlan_query(vlan_id, name, action="create")
            
            # Determine LLM provider based on device type
            if "aruba" in device_type.lower():
                provider = os.getenv("ARUBA_LLM_PROVIDER", "gemini")
                model = os.getenv("ARUBA_LLM_MODEL", "gemini-2.0-flash-exp")
            else:
                provider = os.getenv("CISCO_LLM_PROVIDER", "local")
                model = os.getenv("CISCO_LLM_MODEL", None)
            
            log_event(logging.INFO, 
                f"Generating VLAN commands via {provider} LLM with vendor-specific prompt",
                vlan_id=vlan_id,
                device_type=device_type,
                provider=provider
            )
            
            # Generate commands via LLM
            cli_response = predict_cli_provider(
                query=query,
                provider=provider,
                model=model,
                system_prompt=vendor_prompt
            )
            
            if cli_response.startswith("[Error]"):
                log_event(logging.ERROR, f"LLM command generation failed: {cli_response}")
                raise Exception(f"LLM error: {cli_response}")
            
            # Parse multi-line commands
            commands = [cmd.strip() for cmd in cli_response.strip().split('\n') if cmd.strip()]
            result["commands"] = commands
            result["llm_response"] = cli_response
            
            log_event(logging.INFO, 
                f"LLM generated {len(commands)} commands for VLAN creation",
                vlan_id=vlan_id,
                commands=commands[:3]  # Log first 3 commands
            )
            
            # Execute commands
            # Filter out only mode-change commands that send_config_set handles automatically
            # Keep vlan creation and configuration commands
            config_commands = [cmd for cmd in commands if cmd.lower() not in [
                'configure terminal', 'configure', 'end'
            ]]
            
            # Remove trailing exit/write commands as they'll be handled separately
            while config_commands and config_commands[-1].lower() in ['exit', 'write memory', 'write', 'save']:
                config_commands.pop()
            
            if config_commands:
                output = connection.send_config_set(config_commands)
                result["output"] = output
                log_event(logging.INFO, f"Executed {len(config_commands)} config commands", output_preview=output[:200] if output else "")
            else:
                log_event(logging.WARNING, "No config commands to execute after filtering")
            
            # Always save configuration after VLAN creation
            try:
                connection.save_config()
                result["config_saved"] = True
                log_event(logging.INFO, "Configuration saved successfully")
            except Exception as e:
                log_event(logging.WARNING, f"Config save failed: {e}")
                result["config_saved"] = False
            
        else:
            # Fallback to hardcoded commands
            log_event(logging.INFO, 
                f"Using hardcoded VLAN commands (agentic mode disabled)",
                vlan_id=vlan_id,
                device_type=device_type
            )
            
            if "cisco" in device_type:
                commands = [f"vlan {vlan_id}", f"name {name}"]
            elif "aruba_aoscx" in device_type:
                commands = [f"vlan {vlan_id}", f"name {name}"]
            else:
                commands = [f"vlan {vlan_id}", f"name {name}"]
            
            result["commands"] = commands
            output = connection.send_config_set(commands)
            result["output"] = output
        
        return result
        
    except Exception as e:
        log_event(logging.ERROR, f"VLAN configuration failed: {e}", vlan_id=vlan_id)
        result["status"] = "failed"
        result["error"] = str(e)
        return result



def deploy_vlan_to_switches(vlan_plan: Dict[str, Any]) -> Dict[str, str]:
    """Create a VLAN following hierarchical flow: Core → Access switches.

    Hierarchy:
    - Core switch: UKLONB10C01 (London - Cisco) - primary
    - Access switches: INVIJB1C01 (Vijayawada - Cisco), INVIJB10A01 (Vijayawada - Aruba)
    
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
    CORE_SWITCH = "UKLONB10C01"
    ACCESS_SWITCHES = ["INVIJB1C01", "INVIJB10A01"]
    
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
    """
    Deploy VLAN to a single device using agentic approach.
    
    Returns 'created'|'skipped'|'failed'
    
    If ENABLE_AGENTIC_VLAN_CREATION=1, uses LLM with vendor-specific prompts.
    Otherwise, falls back to hardcoded commands.
    """
    device_role = "Core" if is_core else "Access"
    params = _netmiko_params_from_device(alias, dev)
    use_agentic = os.getenv("ENABLE_AGENTIC_VLAN_CREATION", "0") == "1"
    
    try:
        log_event(logging.INFO, 
            f"Connecting to {device_role} switch (agentic_mode={use_agentic})", 
            device=alias, 
            host=params.get("host")
        )
        
        with ConnectHandler(**params) as conn:
            device_type = params.get("device_type", "")
            
            # Check if VLAN exists
            if _vlan_exists(conn, vlan_id, device_type):
                log_event(logging.INFO, f"VLAN {vlan_id} already exists on {device_role} switch", device=alias)
                return "skipped"
            
            # Create VLAN using agentic or traditional method
            if use_agentic:
                result = _configure_vlan_agentic(conn, vlan_id, name, device_type, use_llm=True)
                if result["status"] == "success":
                    log_event(logging.INFO, 
                        f"VLAN {vlan_id} created on {device_role} switch via agentic method",
                        device=alias,
                        commands=result.get("commands", [])
                    )
                    return "created"
                else:
                    log_event(logging.ERROR, 
                        f"Agentic VLAN creation failed: {result.get('error')}",
                        device=alias
                    )
                    return "failed"
            else:
                # Traditional hardcoded method
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
