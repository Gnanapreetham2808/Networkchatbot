from netmiko import ConnectHandler

def run_command_on_switch(ip, command):
    try:
        device = {
            'device_type': 'cisco_ios_telnet',  # ✅ Telnet device type
            'host': ip,
            'username': ' ',            # ✅ Use a space instead of blank
            'password': 'cisco',        # ✅ Your Telnet password
            'secret': '',               # Optional: 'enable' password if needed
        }

        # Connect to device
        net_connect = ConnectHandler(**device)

        # Run the command
        output = net_connect.send_command(command)

        # Disconnect
        net_connect.disconnect()

        return output

    except Exception as e:
        return f"Telnet connection error: {str(e)}"
