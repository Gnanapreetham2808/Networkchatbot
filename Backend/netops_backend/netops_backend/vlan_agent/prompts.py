"""
Vendor-Specific Prompts for Agentic VLAN Creation

This module provides specialized system prompts for different network vendors,
optimized for multi-command VLAN configuration workflows.

Each vendor has unique command syntax, configuration modes, and best practices.
These prompts ensure the AI generates correct, complete command sequences.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CISCO IOS/IOS-XE PROMPTS
# ============================================================================

CISCO_IOS_VLAN_SYSTEM_PROMPT = """You are a Cisco IOS CLI command generator for VLAN configuration.

CRITICAL: Generate ALL commands in sequence. Do not stop after the first command.

Rules:
1. Output ONLY the exact CLI commands needed - no explanations, comments, or formatting.
2. Generate ALL commands line by line in the correct sequence.
3. Use the VLAN ID and VLAN name provided by the user.
4. If no VLAN name is given, omit the "name" line.
5. Do not include "enable" or privilege mode commands.

Standard VLAN creation sequence (ALL 5 lines required):
configure terminal
vlan <VLAN_ID>
 name <VLAN_NAME>
end
write memory

Example request: "Create VLAN 20 named Sales"
Expected output (all 5 lines):
configure terminal
vlan 20
 name Sales
end
write memory

Example request: "Create VLAN 10"
Expected output (all 4 lines):
configure terminal
vlan 10
end
write memory

Output only raw commands, one per line. No markdown, no explanations. Generate the complete sequence."""


CISCO_IOS_VLAN_DELETE_PROMPT = """You are a Cisco IOS expert for VLAN deletion.

CRITICAL RULES:
1. Return ONLY executable Cisco IOS commands
2. Commands in exact execution order
3. No explanations or commentary
4. No code fences or markdown

VLAN DELETION SYNTAX:
configure terminal
no vlan <vlan-id>
exit
write memory
end

EXAMPLE:
Input: "Delete VLAN 100"
Output:
configure terminal
no vlan 100
exit
write memory
end

WARNING CHECKS:
- Ensure no interfaces are assigned to the VLAN before deletion
- Cannot delete VLAN 1 (default VLAN)
- Cannot delete reserved VLANs 1002-1005

PRE-DELETION VALIDATION (informational):
show vlan id <vlan-id>
show interfaces status | include <vlan-id>

Return deletion commands only."""


# ============================================================================
# ARUBA AOS-CX PROMPTS
# ============================================================================

ARUBA_AOSCX_VLAN_SYSTEM_PROMPT = """You are an Aruba AOS-CX CLI command generator for VLAN configuration.

Rules:
1. Output ONLY the exact CLI commands needed - no explanations, comments, or formatting.
2. Generate commands line by line in the correct sequence.
3. Use the VLAN ID and VLAN name provided by the user.
4. If no VLAN name is given, omit the "name" line.

Standard VLAN creation sequence:
configure terminal
vlan <VLAN_ID>
 name <VLAN_NAME>
exit
write memory

Example request: "Create VLAN 20 named Sales"
Expected output:
configure terminal
vlan 20
 name Sales
exit
write memory

Example request: "Create VLAN 10"
Expected output:
configure terminal
vlan 10
exit
write memory

Output only raw commands, one per line. No markdown, no explanations."""


ARUBA_AOSCX_VLAN_DELETE_PROMPT = """You are an Aruba AOS-CX expert for VLAN deletion.

CRITICAL RULES:
1. Return ONLY executable Aruba AOS-CX commands
2. Commands in exact execution order
3. No explanations or commentary
4. No code fences or markdown

VLAN DELETION SYNTAX:
configure terminal
no vlan <vlan-id>
exit
write memory
end

EXAMPLE:
Input: "Delete VLAN 100"
Output:
configure terminal
no vlan 100
exit
write memory
end

WARNING CHECKS:
- Ensure no interfaces are assigned to VLAN
- Cannot delete VLAN 1 (default)
- Remove VLAN from all trunk ports first

PRE-DELETION VALIDATION (informational):
show vlan <vlan-id>
show interface * vlan

Return deletion commands only."""


# ============================================================================
# ARUBA AOS-SWITCH (PROVISION-BASED) PROMPTS
# ============================================================================

ARUBA_AOS_SWITCH_VLAN_PROMPT = """You are an Aruba AOS (ProVision) CLI command generator for VLAN configuration.

Rules:
1. Output ONLY the exact CLI commands needed - no explanations, comments, or formatting.
2. Generate commands line by line in the correct sequence.
3. Use the VLAN ID and VLAN name provided by the user.
4. ProVision switches do NOT need 'configure terminal' - you're already in config mode.
5. VLAN names should be in QUOTES.

Standard VLAN creation sequence:
vlan <VLAN_ID>
 name "<VLAN_NAME>"
exit
write memory

Example request: "Create VLAN 20 named Sales"
Expected output:
vlan 20
 name "Sales"
exit
write memory

Example request: "Create VLAN 10"
Expected output:
vlan 10
exit
write memory

Output only raw commands, one per line. No markdown, no explanations."""


# ============================================================================
# JUNIPER JUNOS PROMPTS
# ============================================================================

JUNIPER_JUNOS_VLAN_PROMPT = """You are a Juniper JunOS CLI command generator for VLAN configuration.

Rules:
1. Output ONLY the exact CLI commands needed - no explanations, comments, or formatting.
2. Generate commands line by line in the correct sequence.
3. Use the VLAN ID and VLAN name provided by the user.
4. JunOS uses hierarchical 'set' commands.
5. VLAN name comes before vlan-id in the syntax.

Standard VLAN creation sequence:
configure
set vlans <VLAN_NAME> vlan-id <VLAN_ID>
commit
exit

Example request: "Create VLAN 20 named Sales"
Expected output:
configure
set vlans Sales vlan-id 20
commit
exit

Example request: "Create VLAN 10"
Expected output:
configure
set vlans VLAN10 vlan-id 10
commit
exit

Output only raw commands, one per line. No markdown, no explanations."""


# ============================================================================
# HP/HPE COMWARE PROMPTS
# ============================================================================

HPE_COMWARE_VLAN_PROMPT = """You are an HPE/H3C Comware CLI command generator for VLAN configuration.

Rules:
1. Output ONLY the exact CLI commands needed - no explanations, comments, or formatting.
2. Generate commands line by line in the correct sequence.
3. Use the VLAN ID and VLAN name provided by the user.
4. Comware uses 'system-view' instead of 'configure terminal'.
5. Use 'quit' instead of 'exit'.

Standard VLAN creation sequence:
system-view
vlan <VLAN_ID>
 name <VLAN_NAME>
quit
save
quit

Example request: "Create VLAN 20 named Sales"
Expected output:
system-view
vlan 20
 name Sales
quit
save
quit

Example request: "Create VLAN 10"
Expected output:
system-view
vlan 10
quit
save
quit

Output only raw commands, one per line. No markdown, no explanations."""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_vlan_creation_prompt(device_type: str) -> str:
    """
    Get vendor-specific VLAN creation system prompt.
    
    Args:
        device_type: Device type from netmiko (e.g., 'cisco_ios', 'aruba_aoscx')
    
    Returns:
        Vendor-specific system prompt for VLAN creation
    """
    device_type_lower = device_type.lower()
    
    # Cisco variants
    if any(vendor in device_type_lower for vendor in ['cisco_ios', 'cisco_xe', 'cisco_nxos']):
        return CISCO_IOS_VLAN_SYSTEM_PROMPT
    
    # Aruba variants
    elif 'aruba_aoscx' in device_type_lower or 'aoscx' in device_type_lower:
        return ARUBA_AOSCX_VLAN_SYSTEM_PROMPT
    
    elif 'aruba_os' in device_type_lower or 'aruba_procurve' in device_type_lower:
        return ARUBA_AOS_SWITCH_VLAN_PROMPT
    
    # Juniper
    elif 'juniper' in device_type_lower or 'junos' in device_type_lower:
        return JUNIPER_JUNOS_VLAN_PROMPT
    
    # HPE/HP
    elif any(vendor in device_type_lower for vendor in ['hp_comware', 'hpe_comware', 'h3c']):
        return HPE_COMWARE_VLAN_PROMPT
    
    # Default to Cisco (most common)
    else:
        logger.warning(f"Unknown device_type '{device_type}', defaulting to Cisco IOS prompt")
        return CISCO_IOS_VLAN_SYSTEM_PROMPT


def get_vlan_deletion_prompt(device_type: str) -> str:
    """
    Get vendor-specific VLAN deletion system prompt.
    
    Args:
        device_type: Device type from netmiko
    
    Returns:
        Vendor-specific system prompt for VLAN deletion
    """
    device_type_lower = device_type.lower()
    
    if any(vendor in device_type_lower for vendor in ['cisco_ios', 'cisco_xe', 'cisco_nxos']):
        return CISCO_IOS_VLAN_DELETE_PROMPT
    
    elif 'aruba_aoscx' in device_type_lower or 'aoscx' in device_type_lower:
        return ARUBA_AOSCX_VLAN_DELETE_PROMPT
    
    # Default to Cisco
    else:
        logger.warning(f"Unknown device_type '{device_type}', defaulting to Cisco IOS delete prompt")
        return CISCO_IOS_VLAN_DELETE_PROMPT


def format_vlan_query(vlan_id: int, vlan_name: str, action: str = "create") -> str:
    """
    Format a standardized VLAN operation query for LLM.
    
    Args:
        vlan_id: VLAN ID (1-4094)
        vlan_name: VLAN name
        action: Operation type ('create', 'delete', 'modify')
    
    Returns:
        Formatted natural language query
    """
    if action == "create":
        return f"Create VLAN {vlan_id} named {vlan_name}"
    elif action == "delete":
        return f"Delete VLAN {vlan_id}"
    elif action == "modify":
        return f"Modify VLAN {vlan_id} name to {vlan_name}"
    else:
        return f"Configure VLAN {vlan_id} named {vlan_name}"


def get_vlan_validation_command(device_type: str, vlan_id: int) -> str:
    """
    Get vendor-specific command to validate VLAN exists.
    
    Args:
        device_type: Device type from netmiko
        vlan_id: VLAN ID to validate
    
    Returns:
        Show/display command for VLAN verification
    """
    device_type_lower = device_type.lower()
    
    if 'cisco' in device_type_lower:
        return f"show vlan id {vlan_id}"
    
    elif 'aruba_aoscx' in device_type_lower:
        return f"show vlan {vlan_id}"
    
    elif 'aruba_os' in device_type_lower:
        return f"show vlan {vlan_id}"
    
    elif 'juniper' in device_type_lower:
        return f"show vlans"
    
    elif 'comware' in device_type_lower:
        return f"display vlan {vlan_id}"
    
    else:
        return f"show vlan id {vlan_id}"


def get_all_vlans_command(device_type: str) -> str:
    """
    Get vendor-specific command to list all VLANs.
    
    Args:
        device_type: Device type from netmiko
    
    Returns:
        Show/display command for all VLANs
    """
    device_type_lower = device_type.lower()
    
    if 'cisco' in device_type_lower:
        return "show vlan brief"
    
    elif 'aruba' in device_type_lower:
        return "show vlan"
    
    elif 'juniper' in device_type_lower:
        return "show vlans"
    
    elif 'comware' in device_type_lower:
        return "display vlan"
    
    else:
        return "show vlan"


# ============================================================================
# PROMPT REGISTRY
# ============================================================================

PROMPT_REGISTRY: Dict[str, Dict[str, str]] = {
    'cisco_ios': {
        'vlan_create': CISCO_IOS_VLAN_SYSTEM_PROMPT,
        'vlan_delete': CISCO_IOS_VLAN_DELETE_PROMPT,
        'vendor': 'Cisco IOS/IOS-XE'
    },
    'aruba_aoscx': {
        'vlan_create': ARUBA_AOSCX_VLAN_SYSTEM_PROMPT,
        'vlan_delete': ARUBA_AOSCX_VLAN_DELETE_PROMPT,
        'vendor': 'Aruba AOS-CX'
    },
    'aruba_os': {
        'vlan_create': ARUBA_AOS_SWITCH_VLAN_PROMPT,
        'vlan_delete': ARUBA_AOSCX_VLAN_DELETE_PROMPT,  # Similar syntax
        'vendor': 'Aruba AOS (ProVision)'
    },
    'juniper_junos': {
        'vlan_create': JUNIPER_JUNOS_VLAN_PROMPT,
        'vlan_delete': JUNIPER_JUNOS_VLAN_PROMPT,  # Same for delete
        'vendor': 'Juniper JunOS'
    },
    'hp_comware': {
        'vlan_create': HPE_COMWARE_VLAN_PROMPT,
        'vlan_delete': HPE_COMWARE_VLAN_PROMPT,  # Same for delete
        'vendor': 'HPE Comware'
    }
}


def get_supported_vendors() -> list[str]:
    """Get list of supported vendor types."""
    return [info['vendor'] for info in PROMPT_REGISTRY.values()]


def list_prompts_for_vendor(device_type: str) -> Dict[str, Any]:
    """
    List all available prompts for a vendor.
    
    Args:
        device_type: Device type from netmiko
    
    Returns:
        Dictionary of available prompts and metadata
    """
    device_type_lower = device_type.lower()
    
    for key, info in PROMPT_REGISTRY.items():
        if key in device_type_lower:
            return {
                'vendor': info['vendor'],
                'device_type': device_type,
                'operations': list(info.keys() - {'vendor'}),
                'validation_command': get_all_vlans_command(device_type)
            }
    
    return {
        'vendor': 'Unknown',
        'device_type': device_type,
        'operations': ['vlan_create', 'vlan_delete'],
        'validation_command': 'show vlan'
    }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def _example_usage():
    """Example usage of vendor-specific prompts."""
    
    # Example 1: Get Cisco VLAN creation prompt
    cisco_prompt = get_vlan_creation_prompt('cisco_ios')
    query = format_vlan_query(100, "Engineering", "create")
    # Use with: predict_cli_provider(query, provider='gemini', system_prompt=cisco_prompt)
    
    # Example 2: Get Aruba VLAN creation prompt
    aruba_prompt = get_vlan_creation_prompt('aruba_aoscx')
    query = format_vlan_query(200, "Sales", "create")
    # Use with: predict_cli_provider(query, provider='gemini', system_prompt=aruba_prompt)
    
    # Example 3: Get validation command
    validation_cmd = get_vlan_validation_command('cisco_ios', 100)
    # Returns: "show vlan id 100"
    
    # Example 4: List supported vendors
    vendors = get_supported_vendors()
    # Returns: ['Cisco IOS/IOS-XE', 'Aruba AOS-CX', ...]
    
    print(f"Supported vendors: {vendors}")
    print(f"Validation command: {validation_cmd}")


if __name__ == "__main__":
    # Run examples
    _example_usage()
