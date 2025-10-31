"""
Device Backup Manager
=====================
Handles automated backup of network device configurations.
- Connects to devices via Netmiko
- Downloads running/startup configs
- Saves in JSON and TXT formats
- Supports multiple vendors (Cisco, Aruba, Juniper, HPE)
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

logger = logging.getLogger(__name__)

# Backup storage directories
BACKUP_BASE_DIR = Path(__file__).parent.parent.parent / "backups"
BACKUP_JSON_DIR = BACKUP_BASE_DIR / "json"
BACKUP_TXT_DIR = BACKUP_BASE_DIR / "txt"

# Create directories if they don't exist
BACKUP_BASE_DIR.mkdir(exist_ok=True)
BACKUP_JSON_DIR.mkdir(exist_ok=True)
BACKUP_TXT_DIR.mkdir(exist_ok=True)


class DeviceBackupManager:
    """Manages device configuration backups"""
    
    # Vendor-specific backup commands
    BACKUP_COMMANDS = {
        "cisco_ios": {
            "running_config": "show running-config",
            "startup_config": "show startup-config",
            "version": "show version",
            "interfaces": "show ip interface brief",
            "vlans": "show vlan brief",
            "inventory": "show inventory",
            "mac_table": "show mac address-table",
            "arp_table": "show ip arp",
            "cdp_neighbors": "show cdp neighbors detail"
        },
        "cisco_xe": {
            "running_config": "show running-config",
            "startup_config": "show startup-config",
            "version": "show version",
            "interfaces": "show ip interface brief",
            "vlans": "show vlan brief",
            "inventory": "show inventory",
            "mac_table": "show mac address-table",
            "arp_table": "show ip arp",
            "cdp_neighbors": "show cdp neighbors detail"
        },
        "aruba_aoscx": {
            "running_config": "show running-config",
            "startup_config": "show startup-config",
            "version": "show version",
            "interfaces": "show interface brief",
            "vlans": "show vlan",
            "inventory": "show system",
            "mac_table": "show mac-address-table",
            "arp_table": "show arp",
            "lldp_neighbors": "show lldp neighbors-info"
        },
        "aruba_os": {
            "running_config": "show running-config",
            "startup_config": "show startup-config",
            "version": "show version",
            "interfaces": "show ip interface brief",
            "vlans": "show vlan",
            "inventory": "show system",
            "mac_table": "show mac-address",
            "arp_table": "show arp",
            "lldp_neighbors": "show lldp info remote-device"
        },
        "juniper_junos": {
            "running_config": "show configuration",
            "version": "show version",
            "interfaces": "show interfaces terse",
            "vlans": "show vlans"
        },
        "hp_comware": {
            "running_config": "display current-configuration",
            "startup_config": "display saved-configuration",
            "version": "display version",
            "interfaces": "display ip interface brief",
            "vlans": "display vlan"
        }
    }
    
    def __init__(self, devices_json_path: Optional[str] = None):
        """Initialize backup manager with device inventory"""
        if devices_json_path is None:
            # Default to netops_backend/Devices/devices.json
            # Path: chatbot/device_backup_manager.py -> chatbot/ -> netops_backend/ -> Devices/
            self.devices_path = Path(__file__).parent.parent / "Devices" / "devices.json"
        else:
            self.devices_path = Path(devices_json_path)
        
        self.devices = self._load_devices()
    
    def _load_devices(self) -> Dict[str, Any]:
        """Load device inventory from JSON file"""
        try:
            with open(self.devices_path, 'r') as f:
                data = json.load(f)
                # Normalize keys to uppercase to match device_resolver behavior
                return {k.upper(): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            return {}
    
    def _get_netmiko_params(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Convert device dict to Netmiko connection parameters"""
        params = {
            "device_type": device.get("device_type", "cisco_ios"),
            "host": device.get("host"),
            "username": device.get("username"),
            "password": device.get("password"),
            "secret": device.get("secret", device.get("password")),
            "port": device.get("port", 22),
            "timeout": 60,
            "session_log": None
        }
        
        # Log connection attempt (without exposing password)
        logger.info(f"Connecting to {params['host']}:{params['port']} as {params['username']} (device_type: {params['device_type']})")
        
        return params
    
    def backup_single_device(self, device_alias: str) -> Dict[str, Any]:
        """
        Backup a single device configuration.
        
        Args:
            device_alias: Device alias from inventory
            
        Returns:
            Dict with status, files created, and any errors
        """
        # Normalize device alias to uppercase
        device_alias = device_alias.upper()
        
        if device_alias not in self.devices:
            return {
                "status": "error",
                "device": device_alias,
                "error": f"Device '{device_alias}' not found in inventory"
            }
        
        device = self.devices[device_alias]
        device_type = device.get("device_type", "cisco_ios")
        
        logger.info(f"Starting backup for {device_alias} ({device['host']})")
        
        result = {
            "status": "pending",
            "device": device_alias,
            "host": device["host"],
            "device_type": device_type,
            "timestamp": datetime.now().isoformat(),
            "configs": {},
            "files": []
        }
        
        try:
            # Connect to device
            netmiko_params = self._get_netmiko_params(device)
            logger.info(f"[{device_alias}] Attempting SSH connection...")
            connection = ConnectHandler(**netmiko_params)
            logger.info(f"[{device_alias}] ✓ Successfully connected to device")
            
            # Get backup commands for this device type
            commands = self.BACKUP_COMMANDS.get(device_type, self.BACKUP_COMMANDS["cisco_ios"])
            
            # Execute each backup command
            for config_name, command in commands.items():
                try:
                    logger.info(f"[{device_alias}] Executing: {command}")
                    output = connection.send_command(command, read_timeout=120)
                    result["configs"][config_name] = output
                    logger.info(f"[{device_alias}] ✓ Captured {config_name}")
                except Exception as e:
                    logger.warning(f"[{device_alias}] Failed to capture {config_name}: {e}")
                    result["configs"][config_name] = f"ERROR: {str(e)}"
            
            connection.disconnect()
            
            # Parse and structure the configuration data
            result["parsed_configs"] = self._parse_configurations(result["configs"], device_type)
            
            # Save to files
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save JSON format (structured)
            json_filename = f"{device_alias}_{timestamp_str}.json"
            json_filepath = BACKUP_JSON_DIR / json_filename
            
            # Create structured output with both raw and parsed data
            structured_output = {
                "metadata": {
                    "device": device_alias,
                    "host": result["host"],
                    "device_type": device_type,
                    "timestamp": result["timestamp"],
                    "status": "success"
                },
                "raw_configs": result["configs"],
                "parsed_data": result["parsed_configs"]
            }
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(structured_output, f, indent=2, ensure_ascii=False)
            result["files"].append(str(json_filepath))
            logger.info(f"[{device_alias}] Saved JSON: {json_filepath}")
            
            # Save TXT format (formatted)
            txt_filename = f"{device_alias}_{timestamp_str}.txt"
            txt_filepath = BACKUP_TXT_DIR / txt_filename
            txt_content = self._format_backup_as_text(result)
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            result["files"].append(str(txt_filepath))
            logger.info(f"[{device_alias}] Saved TXT: {txt_filepath}")
            
            result["status"] = "success"
            return result
            
        except NetMikoTimeoutException:
            error_msg = f"Connection timeout to {device['host']}:{device.get('port', 22)} - Check if device is reachable"
            logger.error(f"[{device_alias}] {error_msg}")
            result["status"] = "error"
            result["error"] = error_msg
            return result
            
        except NetMikoAuthenticationException:
            error_msg = f"Authentication failed for {device['host']} with username '{device.get('username')}' - Check credentials in devices.json"
            logger.error(f"[{device_alias}] {error_msg}")
            result["status"] = "error"
            result["error"] = error_msg
            return result
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(f"[{device_alias}] {error_msg}", exc_info=True)
            result["status"] = "error"
            result["error"] = error_msg
            return result
    
    def backup_all_devices(self) -> Dict[str, Any]:
        """
        Backup all devices in inventory.
        
        Returns:
            Dict with summary of backups
        """
        logger.info(f"Starting backup for {len(self.devices)} devices")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_devices": len(self.devices),
            "successful": [],
            "failed": [],
            "backups": {}
        }
        
        for device_alias in self.devices.keys():
            backup_result = self.backup_single_device(device_alias)
            results["backups"][device_alias] = backup_result
            
            if backup_result["status"] == "success":
                results["successful"].append(device_alias)
            else:
                results["failed"].append(device_alias)
        
        logger.info(f"Backup complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results
    
    def _parse_configurations(self, configs: Dict[str, str], device_type: str) -> Dict[str, Any]:
        """Parse raw configuration outputs into structured data"""
        parsed = {}
        
        # Parse interfaces
        if "interfaces" in configs:
            parsed["interfaces"] = self._parse_interfaces(configs["interfaces"], device_type)
        
        # Parse VLANs
        if "vlans" in configs:
            parsed["vlans"] = self._parse_vlans(configs["vlans"], device_type)
        
        # Parse version info
        if "version" in configs:
            parsed["version_info"] = self._parse_version(configs["version"], device_type)
        
        # Parse inventory
        if "inventory" in configs:
            parsed["inventory"] = self._parse_inventory(configs["inventory"], device_type)
        
        return parsed
    
    def _parse_interfaces(self, output: str, device_type: str) -> List[Dict[str, str]]:
        """Parse interface output into structured list"""
        interfaces = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Interface') or line.startswith('---'):
                continue
            
            # Parse Cisco IOS format: "Interface IP-Address OK? Method Status Protocol"
            parts = line.split()
            if len(parts) >= 6:
                interfaces.append({
                    "name": parts[0],
                    "ip_address": parts[1] if parts[1] != "unassigned" else None,
                    "status": parts[4],
                    "protocol": parts[5]
                })
        
        return interfaces
    
    def _parse_vlans(self, output: str, device_type: str) -> List[Dict[str, Any]]:
        """Parse VLAN output into structured list"""
        vlans = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('VLAN') or line.startswith('---'):
                continue
            
            # Parse Cisco format: "1    default                          active    Gi1/0/1, ..."
            parts = line.split(None, 3)  # Split on first 3 whitespaces
            if len(parts) >= 3:
                vlan_id = parts[0]
                if vlan_id.isdigit():
                    vlans.append({
                        "id": int(vlan_id),
                        "name": parts[1],
                        "status": parts[2],
                        "ports": parts[3] if len(parts) > 3 else ""
                    })
        
        return vlans
    
    def _parse_version(self, output: str, device_type: str) -> Dict[str, str]:
        """Parse version output to extract key information"""
        version_info = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract software version
            if 'Version' in line and 'Software' in line:
                version_info["software_version"] = line
            
            # Extract model
            if 'Model number' in line or 'Model:' in line:
                version_info["model"] = line.split(':')[-1].strip() if ':' in line else line
            
            # Extract serial number
            if 'System serial number' in line or 'Serial Number:' in line:
                version_info["serial"] = line.split(':')[-1].strip() if ':' in line else line
            
            # Extract uptime
            if 'uptime is' in line:
                version_info["uptime"] = line
        
        return version_info
    
    def _parse_inventory(self, output: str, device_type: str) -> List[Dict[str, str]]:
        """Parse inventory output into structured list"""
        inventory = []
        lines = output.strip().split('\n')
        
        current_item = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_item:
                    inventory.append(current_item)
                    current_item = {}
                continue
            
            # Parse NAME/DESCR line
            if line.startswith('NAME:'):
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip().strip('"')
                        current_item[key] = value
        
        if current_item:
            inventory.append(current_item)
        
        return inventory
    
    def _format_backup_as_text(self, backup_data: Dict[str, Any]) -> str:
        """Format backup data as readable text document"""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("NETWORK DEVICE CONFIGURATION BACKUP")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Device:          {backup_data['device']}")
        lines.append(f"IP Address:      {backup_data['host']}")
        lines.append(f"Device Type:     {backup_data['device_type']}")
        lines.append(f"Backup Time:     {backup_data['timestamp']}")
        lines.append(f"Status:          {backup_data['status'].upper()}")
        lines.append("")
        
        # Each configuration section
        for config_name, config_output in backup_data.get("configs", {}).items():
            lines.append("=" * 80)
            lines.append(f"SECTION: {config_name.upper().replace('_', ' ')}")
            lines.append("=" * 80)
            lines.append("")
            lines.append(config_output)
            lines.append("")
            lines.append("")
        
        # Footer
        lines.append("=" * 80)
        lines.append("END OF BACKUP")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def list_backups(self, device_alias: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            device_alias: Filter by device alias (optional)
            
        Returns:
            List of backup file information
        """
        # Normalize device alias to uppercase if provided
        if device_alias:
            device_alias = device_alias.upper()
        
        backups = []
        
        for json_file in BACKUP_JSON_DIR.glob("*.json"):
            file_device = json_file.stem.rsplit("_", 2)[0].upper()
            
            if device_alias and file_device != device_alias:
                continue
            
            try:
                with open(json_file, 'r') as f:
                    backup_data = json.load(f)
                
                backups.append({
                    "device": backup_data.get("device"),
                    "host": backup_data.get("host"),
                    "timestamp": backup_data.get("timestamp"),
                    "status": backup_data.get("status"),
                    "json_file": str(json_file),
                    "txt_file": str(BACKUP_TXT_DIR / json_file.name.replace(".json", ".txt")),
                    "size_kb": json_file.stat().st_size / 1024
                })
            except Exception as e:
                logger.warning(f"Failed to read backup {json_file}: {e}")
        
        # Sort by timestamp descending
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def get_backup_details(self, json_filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed backup data from JSON file.
        
        Args:
            json_filepath: Path to JSON backup file
            
        Returns:
            Backup data dict or None if not found
        """
        try:
            with open(json_filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load backup {json_filepath}: {e}")
            return None
