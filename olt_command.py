import time
from olt_telnet import OLTTelnetClient


def build_gpon_commands(data: dict) -> list[str]:
    """Generates the list of OLT CLI commands based on form data."""
    onu_id = data["onu_id"]
    onu_desc = data["onu_description"] if data["onu_description"] else f"{data['pppoe_username']}_AUTO"
    wifi_name = data["wifi_username"] if data["wifi_username"] else "ONT_WiFi"

    # Build dynamic LAN bindings from checkboxes
    lan_bindings = " ".join([f"lan{i}" for i in range(1, 5) if data.get(f"lan{i}")])

    # Build dynamic SSID bindings from checkboxes
    ssid_list = []
    if data.get("enable_ssid1"):
        ssid_list.append("ssid1")
    if data.get("enable_ssid5"):
        ssid_list.append("ssid5")
    ssid_bindings = " ".join(ssid_list)

    # Core CLI sequence
    commands = [
        f"onu add {onu_id} profile default sn {data['gpon_sn']} us-rate 1g",
        f"onu {onu_id} desc {onu_desc}",
        f"onu {onu_id} profile line name line_profile_1",
        f"onu {onu_id} profile srv name service_profile_1",
        f"onu {onu_id} pri wan_adv add route index 1",
        f"onu {onu_id} pri wan_adv index 1 route mode internet mtu 1492",
        f"onu {onu_id} pri wan_adv index 1 route ipv4 pppoe proxy disable user {data['pppoe_username']} pwd {data['pppoe_password']} mode auto nat enable",
        f"onu {onu_id} pri wan_adv index 1 vlan tag wan_vlan {data['vlan_port']} 0",
        f"onu {onu_id} pri wan_adv index 1 bind lan {lan_bindings}",
        f"onu {onu_id} pri wan_adv index 1 bind ssid {ssid_bindings}",
    ]

    # Wi-Fi configuration commands
    if data.get("enable_ssid1"):
        commands.append(
            f"onu {onu_id} pri wifi_ssid 1 hide disable auth_mode wpa2psk_wpa3psk encrypt_type aes shared_key {data['wifi_shared_key']} rekey_interval 0 name {wifi_name} 5G"
        )
    if data.get("enable_ssid5"):
        commands.append(
            f"onu {onu_id} pri wifi_ssid 5 hide disable auth_mode wpa2psk_wpa3psk encrypt_type aes shared_key {data['wifi_shared_key']} rekey_interval 0 name {wifi_name}"
        )

    return commands


def execute_gpon_config(data: dict, log_callback, status_callback, done_callback):
    """Orchestrates Telnet session and sends commands line-by-line."""
    client = OLTTelnetClient(host=data["olt_ip"], port=23)

    try:
        # 1. Connect and login
        client.login(data["olt_username"], data["olt_password"], log_callback)

        # 1.5. Navigate to the correct interface context
        slot = data.get("slot", "0")
        port = data.get("port", "1")
        log_callback(f"[+] Navigating to interface gpon-olt_{slot}/{port}...\n")
        
        # Enter interface configuration mode
        interface_cmd = f"interface gpon-olt_{slot}/{port}"
        out = client.exec_cmd(interface_cmd, timeout=8.0)
        if out.strip():
            log_callback(f"Interface response: {out.strip()}\n")
        
        time.sleep(0.5)  # Brief pause after interface selection

        # 2. Build commands
        commands = build_gpon_commands(data)

        # 3. Execution loop - send commands one by one with proper timing
        log_callback("\n" + "=" * 60 + "\n")
        log_callback(f"INANZA KUTUMA TELNET COMMANDS KWENYE OLT INTERFACE gpon-olt_{slot}/{port}:\n")
        log_callback("=" * 60 + "\n\n")

        total_commands = len(commands)
        for i, cmd in enumerate(commands, 1):
            # Show progress
            log_callback(f"[{i}/{total_commands}] Executing: {cmd}\n")
            
            # Execute command and wait for response
            out = client.exec_cmd(cmd, timeout=12.0)
            
            # Log the response
            if out.strip():
                response_lines = out.strip().split('\n')
                for line in response_lines:
                    line_clean = line.strip()
                    if line_clean and not line_clean.endswith('#') and not line_clean.endswith('$') and not line_clean.endswith(')#'):
                        log_callback(f"    Response: {line_clean}\n")
            
            # Check for error responses
            response_lower = out.lower()
            if any(error_word in response_lower for error_word in ["error", "fail", "invalid", "not found", "denied"]):
                log_callback(f"    ⚠️ Warning: Possible error in response\n")
            else:
                log_callback(f"    ✅ Command executed successfully\n")
            
            # Wait between commands for stability - longer wait for critical commands
            if i < total_commands:
                wait_time = 1.5 if "add" in cmd or "profile" in cmd else 1.0
                log_callback(f"    ⏳ Waiting {wait_time} seconds before next command...\n\n")
                time.sleep(wait_time)
            else:
                log_callback("\n")

        # 4. Exit interface mode
        log_callback("Exiting interface configuration mode...\n")
        client.exec_cmd("exit", timeout=5.0)
        time.sleep(0.5)

        log_callback("=" * 60 + "\n")
        log_callback("✔ CONFIGURATION IMEKAMILIKA VIZURI!\n")
        log_callback(f"Jumla ya commands: {total_commands}\n")
        log_callback(f"Interface: gpon-olt_{slot}/{port}\n")
        log_callback("=" * 60 + "\n")
        status_callback("Configuration Imekamilika Vizuri!", "#38a169")

    except Exception as e:
        log_callback(f"\n❌ ERRORED/FAILED: {str(e)}\n")
        status_callback("Kuna tatizo limetokea wakati wa Telnet!", "#e53e3e")

    finally:
        client.close()
        done_callback()