import time
from olt_telnet import OLTTelnetClient


def detect_olt_vendor(client, log_callback):
    """Detect OLT vendor and return appropriate command set"""
    log_callback("[+] Detecting OLT vendor and model...\n")
    
    # Try to get system information
    show_commands = [
        "show version",
        "show system",
        "show device", 
        "display version",
        "display device"
    ]
    
    for cmd in show_commands:
        try:
            response = client.exec_cmd(cmd, timeout=5.0)
            response_lower = response.lower()
            
            if "huawei" in response_lower:
                log_callback("    Detected: Huawei OLT\n")
                return "huawei"
            elif "zte" in response_lower or "zxan" in response_lower:
                log_callback("    Detected: ZTE OLT\n") 
                return "zte"
            elif "fiberhome" in response_lower or "an55" in response_lower:
                log_callback("    Detected: FiberHome OLT\n")
                return "fiberhome"
            elif any(vendor in response_lower for vendor in ["dasan", "v-sol", "vsol"]):
                log_callback("    Detected: DASAN/V-SOL OLT\n")
                return "dasan"
                
        except Exception:
            continue
    
    log_callback("    ⚠️ Could not detect OLT vendor - using generic commands\n")
    return "generic"


def get_vendor_commands(vendor, data):
    """Get vendor-specific command set"""
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

    if vendor == "huawei":
        # Huawei MA5608T/MA5683T style commands
        return [
            f"ont add {data['gpon_sn']} {onu_id}",
            f"ont port native-vlan {onu_id} eth 1 vlan {data['vlan_port']}",
            f"service-port {onu_id} vlan {data['vlan_port']} gpon 0/{data.get('slot', '0')}/{data.get('port', '1')} ont {onu_id} gemport 1 multi-service user-vlan {data['vlan_port']}"
        ]
    elif vendor == "zte":
        # ZTE C300/C320 style commands  
        return [
            f"onu {onu_id} type ZTE-F460 sn {data['gpon_sn']}",
            f"onu {onu_id} profile line ZTE-F460 remote ZTE-F460",
            f"pon-onu-mng gpon-onu_{data.get('slot', '0')}/{data.get('port', '1')}:{onu_id}",
            f"service HSI type internet gemport 1 vlan {data['vlan_port']}"
        ]
    else:
        # Generic/Original commands (keeping current format)
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
            # SSID1 = 2.4GHz WiFi (normal name)
            commands.append(
                f"onu {onu_id} pri wifi_ssid 1 hide disable auth_mode wpa2psk_wpa3psk encrypt_type aes shared_key {data['wifi_shared_key']} rekey_interval 0 name {wifi_name}"
            )
        if data.get("enable_ssid5"):
            # SSID5 = 5GHz WiFi (name with _5G suffix)
            commands.append(
                f"onu {onu_id} pri wifi_ssid 5 hide disable auth_mode wpa2psk_wpa3psk encrypt_type aes shared_key {data['wifi_shared_key']} rekey_interval 0 name {wifi_name}_5G"
            )
            
        return commands
def build_gpon_commands(data: dict) -> list[str]:
    """Legacy function for backward compatibility - uses generic commands"""
    return get_vendor_commands("generic", data)


def execute_gpon_config(data: dict, log_callback, status_callback, done_callback):
    """Orchestrates Telnet session and sends commands line-by-line."""
    client = OLTTelnetClient(host=data["olt_ip"], port=23)

    try:
        # 1. Connect and login
        client.login(data["olt_username"], data["olt_password"], log_callback)

        # 1.5. Enter global configuration mode
        log_callback(f"[+] Entering global configuration mode...\n")
        config_out = client.exec_cmd("configure terminal", timeout=8.0)
        log_callback(f"Config mode: {config_out.strip()}\n")
        
        # Check if we successfully entered config mode
        if "invalid" in config_out.lower() or "unknown" in config_out.lower():
            log_callback(f"    ⚠️ 'configure terminal' failed, trying alternatives...\n")
            # Try alternative config commands
            alt_commands = ["config", "configure", "conf t"]
            for alt_cmd in alt_commands:
                alt_out = client.exec_cmd(alt_cmd, timeout=5.0)
                log_callback(f"    Trying '{alt_cmd}': {alt_out.strip()}\n")
                if "invalid" not in alt_out.lower() and "unknown" not in alt_out.lower():
                    break
        
        time.sleep(1.0)  # Wait for config mode to be active
        
        # Verify we're in config mode by checking prompt
        prompt_check = client.exec_cmd("", timeout=3.0)
        log_callback(f"Current prompt after config: {prompt_check.strip()}\n")
        
        # 1.6. Navigate to the correct interface context
        slot = data.get("slot", "0")
        port = data.get("port", "1")
        log_callback(f"[+] Navigating to interface gpon-olt_{slot}/{port}...\n")
        
        # Try different interface command formats
        interface_formats = [
            f"interface gpon-olt_{slot}/{port}",
            f"interface gpon {slot}/{port}", 
            f"interface gpon-olt {slot}/{port}",
            f"gpon-olt_{slot}/{port}",
            f"pon-channel gpon {slot}/{port}"
        ]
        
        interface_success = False
        for i, interface_cmd in enumerate(interface_formats):
            log_callback(f"    Trying format {i+1}: {interface_cmd}\n")
            out = client.exec_cmd(interface_cmd, timeout=8.0)
            log_callback(f"    Response: {out.strip()}\n")
            
            if "unknown command" not in out.lower() and "invalid" not in out.lower():
                interface_success = True
                log_callback(f"    ✅ Interface command successful!\n")
                break
        
        if not interface_success:
            log_callback(f"    ❌ All interface formats failed. Continuing anyway...\n")
        
        time.sleep(1.0)  # Wait for interface mode to be active

        # 1.7. Detect OLT vendor and get appropriate commands
        vendor = detect_olt_vendor(client, log_callback)
        
        # 2. Build commands based on vendor
        commands = get_vendor_commands(vendor, data)

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
            
            # Enhanced error checking
            response_lower = out.lower()
            if "unknown command" in response_lower:
                log_callback(f"    ❌ CRITICAL: Unknown command error!\n")
                log_callback(f"    💡 This suggests we're not in the correct CLI mode.\n")
                
                # Try to diagnose the issue
                if i == 0:  # First command failed
                    log_callback(f"    🔍 Checking current CLI prompt...\n")
                    prompt_check = client.exec_cmd("", timeout=3.0)  # Send empty command to see prompt
                    log_callback(f"    Current prompt: {prompt_check.strip()}\n")
                    
                    # If we're still in wrong mode, try to fix
                    if ">" in prompt_check and "#" not in prompt_check:
                        log_callback(f"    🔧 Attempting to enter enable mode...\n")
                        client.exec_cmd("enable", timeout=5.0)
                        client.exec_cmd("configure terminal", timeout=5.0)
                        client.exec_cmd(f"interface gpon-olt_{slot}/{port}", timeout=5.0)
                        
            elif any(error_word in response_lower for error_word in ["error", "fail", "invalid", "denied"]):
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

        # 4. Exit interface mode and global config mode
        log_callback("Exiting interface configuration mode...\n")
        client.exec_cmd("exit", timeout=5.0)
        time.sleep(0.5)
        
        log_callback("Exiting global configuration mode...\n") 
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