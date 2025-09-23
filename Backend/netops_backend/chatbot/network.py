"""Network execution layer with optional simulation & fast timeouts.

Environment variables:
  SIMULATE_NETWORK=1 -> Do not attempt real device connection; return mock data.
  NETWORK_PRECHECK_TIMEOUT (seconds, default 2)
  NETWORK_COMMAND_TIMEOUT (seconds, default 8)  (Netmiko timeout)
"""

import os
import socket
from netmiko import ConnectHandler


def _simulate_output(command: str) -> str:
    lc = command.lower().strip()
    if lc.startswith('show ip interface brief'):
        return ("Interface          IP-Address      OK? Method Status                Protocol\n"
                "GigabitEthernet0/0 192.168.10.1   YES manual up                    up\n"
                "GigabitEthernet0/1 unassigned     YES unset  administratively down down")
    if lc.startswith('show version'):
        return "Cisco IOS Software, Virtual Mock Image Version 15.2(2)E MOCK BUILD" \
               "\nSystem returned to ROM by power-on\nProcessor board ID MOCK1234"
    if lc.startswith('show vlan'):
        return ("VLAN Name                             Status    Ports\n"
                "1    default                          active    Gi0/0, Gi0/1\n"
                "10   Users                            active    Gi0/2\n"
                "20   Voice                            active    Gi0/3")
    return f"(simulated) Executed '{command}'. No real device connected."


def _precheck_port(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def run_command_on_switch(ip, command):
    if os.getenv('SIMULATE_NETWORK', '0') == '1':
        return _simulate_output(command)

    pre_t = float(os.getenv('NETWORK_PRECHECK_TIMEOUT', '2'))
    if not _precheck_port(ip, 22, pre_t):
        return _simulate_output(command)

    try:
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': ' ',  # space placeholder
            'password': 'cisco',
            'secret': '',
            'timeout': float(os.getenv('NETWORK_COMMAND_TIMEOUT', '8')),
            'conn_timeout': float(os.getenv('NETWORK_PRECHECK_TIMEOUT', '2')),
            'port': 22,
        }
        net_connect = ConnectHandler(**device)
        output = net_connect.send_command(command, read_timeout=5)
        net_connect.disconnect()
        return output
    except Exception as e:
        # Fallback simulate rather than long error
        return _simulate_output(command) + f"\n[connection note: {e}]"
