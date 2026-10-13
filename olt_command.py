import time
import re
from olt_telnet import OLTTelnetClient


def is_valid_gpon_sn(sn):
    """Validate GPON Serial Number format - supports multiple formats"""
    if not sn:
        return False, "Serial number is empty"
    
    # Normalize: uppercase, remove spaces/dashes
    sn_clean = sn.upper().replace(" ", "").replace("-", "")
    
    # GPON SN formats supported:
    # Format 1: 4 letters + 8 hex digits (VSOL1A2B3C4D, HWTC12345678)
    # Format 2: GPON + numbers/letters (GPON006523777, GPON00663G65)
    
    # Pattern 1: Standard vendor format (4 letters + 8 hex)
    pattern1 = r'^[A-Z]{4}[0-9A-F]{8}$'
    
    # Pattern 2: GPON prefix format (GPON + alphanumeric)
    pattern2 = r'^GPON[0-9A-Z]{8,12}$'
    
    if re.match(pattern1, sn_clean):
        return True, sn_clean
    elif re.match(pattern2, sn_clean):
        return True, sn_clean
    else:
        return False, f"Invalid GPON SN format. Expected: VSOL1A2B3C4D OR GPON006523777. Got: {sn_clean}"


def normalize_gpon_sn(sn):
    """Normalize GPON SN to standard format"""
    if not sn:
        return ""
    return sn.upper().replace(" ", "").replace("-", "")


def detect_olt_vendor(client, log_callback):
    """Detect OLT vendor and return appropriate command set"""
    log_callback("[+] Detecting OLT vendor and model...\n")
    
    # V-SOL detection commands first (most reliable)
    primary_commands = [
        "show version",  # This works and shows "Device Model: V5600X2"
        "show system", 
        "show device",
    ]
    
    vendor_responses = []
    
    # Try primary commands first
    for cmd in primary_commands:
        try:
            log_callback(f"    Trying: {cmd}\n")
            response = client.exec_cmd(cmd, timeout=5.0)
            
            if response and "unknown command" not in response.lower():
                log_callback(f"    ✅ Success: {cmd}\n")
                vendor_responses.append((cmd, response))
                
                response_lower = response.lower()
                
                # V-SOL Detection (PRIORITY - check first!)
                if any(vsol in response_lower for vsol in ["v5600", "v-sol", "vsol"]) or \
                   any(model in response for model in ["V5600X2", "V5600X7"]):
                    log_callback("    🎯 Detected: V-SOL OLT\n")
                    return "vsol"
                
                # Other vendors
                elif any(hw in response_lower for hw in ["huawei", "ma56", "ma58", "smartax"]):
                    log_callback("    🎯 Detected: Huawei OLT\n")
                    return "huawei"
                elif any(zte in response_lower for zte in ["zte", "zxan", "c300", "c320"]):
                    log_callback("    🎯 Detected: ZTE OLT\n") 
                    return "zte"
                elif any(fh in response_lower for fh in ["fiberhome", "an55", "an56"]):
                    log_callback("    🎯 Detected: FiberHome OLT\n")
                    return "fiberhome"
                elif any(alc in response_lower for alc in ["alcatel", "nokia", "isam"]):
                    log_callback("    🎯 Detected: Nokia/Alcatel OLT\n")
                    return "nokia"
            else:
                log_callback(f"    ❌ Failed: {cmd}\n")
                
        except Exception as e:
            log_callback(f"    ⚠️ Error with {cmd}: {str(e)}\n")
            continue
    
    # If we got responses but couldn't identify vendor, show what we found
    if vendor_responses:
        log_callback(f"    📋 Got {len(vendor_responses)} successful responses:\n")
        for cmd, resp in vendor_responses:
            lines = resp.split('\n')[:3]  # First 3 lines
            for line in lines:
                if line.strip():
                    log_callback(f"      {cmd}: {line.strip()}\n")
    
    log_callback("    ❓ Unknown OLT vendor - need manual identification\n")
    return "unknown"


def get_vendor_commands(vendor, data):
    """Get vendor-specific command set"""
    onu_id = data["onu_id"]
    onu_desc = data.get("onu_description", "") or f"{data.get('pppoe_username', 'AUTO')}_AUTO"
    wifi_name = data.get("wifi_username", "") or "ONT_WiFi"

    # Validate and normalize GPON SN first
    is_valid, sn_result = is_valid_gpon_sn(data['gpon_sn'])
    if not is_valid:
        raise ValueError(f"GPON SN Validation Error: {sn_result}")
    
    gpon_sn = sn_result  # Use normalized SN

    # Build dynamic LAN bindings from checkboxes
    lan_bindings = " ".join([f"lan{i}" for i in range(1, 5) if data.get(f"lan{i}")])

    # Build dynamic SSID bindings from checkboxes
    ssid_list = []
    if data.get("enable_ssid1"):
        ssid_list.append("ssid1")
    if data.get("enable_ssid5"):
        ssid_list.append("ssid5")
    ssid_bindings = " ".join(ssid_list)

    if vendor == "vsol":
        # V-SOL V5600X2/V5600X7 specific commands
        # Proper workflow for V-SOL OLT systems
        return [
            # Step 1: Register ONU
            f"onu add {onu_id} sn {gpon_sn}",
            
            # Step 2: Set ONU description  
            f"onu {onu_id} name \"{onu_desc}\"",
            
            # Step 3: Configure TCONT and GEM port
            f"onu {onu_id} tcont 1 profile default",
            f"onu {onu_id} gemport 1 tcont 1",
            
            # Step 4: Configure VLAN and service
            f"onu {onu_id} vlan {data['vlan_port']}",
            f"onu {onu_id} service-port 1 vlan {data['vlan_port']} gemport 1",
            
            # Step 5: Enable ONU
            f"onu {onu_id} enable",
        ]
    elif vendor == "huawei":
        # Huawei MA5608T/MA5683T style commands
        return [
            f"ont add {gpon_sn} {onu_id}",
            f"ont port native-vlan {onu_id} eth 1 vlan {data['vlan_port']}",
            f"service-port {onu_id} vlan {data['vlan_port']} gpon 0/{data.get('slot', '0')}/{data.get('port', '1')} ont {onu_id} gemport 1 multi-service user-vlan {data['vlan_port']}"
        ]
    elif vendor == "zte":
        # ZTE C300/C320 style commands  
        return [
            f"onu {onu_id} type ZTE-F460 sn {gpon_sn}",
            f"onu {onu_id} profile line ZTE-F460 remote ZTE-F460",
            f"pon-onu-mng gpon-onu_{data.get('slot', '0')}/{data.get('port', '1')}:{onu_id}",
            f"service HSI type internet gemport 1 vlan {data['vlan_port']}"
        ]
    elif vendor == "nokia":
        # Nokia/Alcatel ISAM commands
        return [
            f"configure equipment ont interface {data.get('slot', '0')}/{data.get('port', '1')}/{onu_id} admin-state enable",
            f"configure equipment ont interface {data.get('slot', '0')}/{data.get('port', '1')}/{onu_id} desc \"{onu_desc}\"", 
            f"configure service vpls {data['vlan_port']} sap {data.get('slot', '0')}/{data.get('port', '1')}/{onu_id}:0 create"
        ]
    elif vendor == "unknown":
        # Discovery-based commands for unknown V-SOL models
        # Keep the working patterns from discovery but with proper SN validation
        return [
            # Use normalized SN with working command patterns
            f"onu allow-list sn-auth {gpon_sn}",
            f"onu auto-upgrade equipment-id {onu_id} enable",
            f"onu auto-upgrade equipment-id {onu_id} version latest",
        ]
    else:
        # Generic/Original commands (keeping current format)
        commands = [
            f"onu add {onu_id} profile default sn {gpon_sn} us-rate 1g",
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
    """build commands specifically for v5600x7 based on discovery results"""
    # v5600x7 discovery shows: onu allow-list, onu application
    # use these instead of generic commands
    
    onu_id = data["onu_id"]
    onu_desc = data.get("onu_description", "") or f"{data.get('pppoe_username', 'auto')}_auto"
    wifi_name = data.get("wifi_username", "") or "ont_wifi"

    # build dynamic lan bindings from checkboxes
    lan_bindings = " ".join([f"lan{i}" for i in range(1, 5) if data.get(f"lan{i}")])

    # build dynamic ssid bindings from checkboxes
    ssid_list = []
    if data.get("enable_ssid1"):
        ssid_list.append("ssid1")
    if data.get("enable_ssid5"):
        ssid_list.append("ssid5")
    ssid_bindings = " ".join(ssid_list)

    # v5600x7 specific commands based on discovery
    commands = [
        # use discovered onu allow-list command
        f"onu allow-list add {data['gpon_sn']} {onu_id}",
        
        # use discovered onu application command  
        f"onu application {onu_id} internet",
        f"onu application {onu_id} config pppoe username {data['pppoe_username']} password {data['pppoe_password']}",
        f"onu application {onu_id} vlan {data['vlan_port']}",
        
        # wifi configuration using application
        f"onu application {onu_id} wifi ssid {wifi_name} password {data['wifi_shared_key']}",
    ]
    
    return commands


def execute_gpon_config(data: dict, log_callback, status_callback, done_callback):
    """Orchestrates Telnet session and sends commands line-by-line."""
    client = OLTTelnetClient(host=data["olt_ip"], port=23)

    try:
        # 1. Connect and login
        client.login(data["olt_username"], data["olt_password"], log_callback)

        # 1.4. Enter privileged EXEC mode (enable)
        log_callback(f"[+] Entering privileged mode (enable)...\n")
        enable_out = client.exec_cmd("enable", timeout=8.0)
        log_callback(f"Enable response: {enable_out.strip()}\n")
        
        # Check if enable mode requires password
        if "password" in enable_out.lower():
            # Use dedicated enable password if provided, otherwise use login password
            enable_password = data.get("olt_enable_password", "").strip()
            if not enable_password:
                enable_password = data["olt_password"]
            
            log_callback(f"[+] Enable mode requires password...\n")
            enable_pwd_out = client.exec_cmd(enable_password, timeout=8.0)
            log_callback(f"Enable password response: {enable_pwd_out.strip()}\n")
            
            # Check for authentication failure
            if any(fail_word in enable_pwd_out.lower() for fail_word in ["bad", "incorrect", "invalid", "denied", "fail"]):
                log_callback(f"❌ Enable password authentication failed!\n")
                log_callback(f"💡 Try setting a different Enable Password in OLT Connection section\n")
                raise Exception("Enable mode authentication failed")
                
        elif "#" in enable_out:
            log_callback(f"✅ No enable password required - direct privileged access\n")
        else:
            log_callback(f"⚠️ Unexpected enable response: {enable_out.strip()}\n")
        
        # Verify we're in enable mode (prompt should end with #)
        prompt_check = client.exec_cmd("", timeout=3.0)
        log_callback(f"Current prompt after enable: {prompt_check.strip()}\n")
        
        if "#" not in prompt_check:
            log_callback(f"⚠️ Warning: May not be in enable mode (no # prompt)\n")
            log_callback(f"💡 Try setting Enable Password field in OLT Connection\n")
        else:
            log_callback(f"✅ Successfully entered enable mode\n")
        
        time.sleep(1.0)

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
        #  log_callback(f"[+] Navigating to interface gpon-olt_{slot}/{port}...\n")
        
        # Try different interface command formats
        interface_formats = [
            # f"interface gpon-olt_{slot}/{port}",
              f"interface gpon {slot}/{port}", 
            # f"interface gpon-olt {slot}/{port}",
            # f"gpon-olt_{slot}/{port}",
            # f"pon-channel gpon {slot}/{port}"
        ]
        
        interface_success = False
        interface_response = ""
        for i, interface_cmd in enumerate(interface_formats):
            log_callback(f"    Trying format {i+1}: {interface_cmd}\n")
            out = client.exec_cmd(interface_cmd, timeout=8.0)
            log_callback(f"    Response: {out.strip()}\n")
            
            # Check for specific errors that indicate wrong slot/port
            if "isn't exist" in out.lower() or "not exist" in out.lower():
                log_callback(f"    ❌ Slot/Port doesn't exist - need to find correct interface\n")
                continue
            elif "unknown command" not in out.lower() and "invalid" not in out.lower():
                interface_success = True
                interface_response = out.strip()
                log_callback(f"    ✅ Interface command successful!\n")
                break
            else:
                log_callback(f"    ❌ Format failed: {interface_cmd}\n")
        
        # If all interface formats failed, try to discover available interfaces
        if not interface_success:
            log_callback(f"[+] All interface formats failed. Discovering available interfaces...\n")
            
            # Try to find available gpon interfaces
            discovery_cmds = [
                "show interface gpon ?",
                "show gpon ?", 
                "show interface ?",
                "interface gpon ?",
                "interface ?",
                "show running-config | include gpon",
                "show gpon",
                "show interface brief"
            ]
            
            available_interfaces = []
            for disc_cmd in discovery_cmds:
                try:
                    log_callback(f"    Discovering: {disc_cmd}\n")
                    disc_out = client.exec_cmd(disc_cmd, timeout=5.0)
                    
                    if disc_out and "unknown command" not in disc_out.lower():
                        log_callback(f"    ✅ Discovery success: {disc_cmd}\n")
                        
                        # Look for gpon interface patterns in response
                        import re
                        gpon_patterns = re.findall(r'gpon[-_]?\d+[/]\d+', disc_out.lower())
                        if gpon_patterns:
                            available_interfaces.extend(gpon_patterns)
                            log_callback(f"    🎯 Found GPON interfaces: {gpon_patterns}\n")
                        
                        # Show first few lines of response
                        lines = disc_out.split('\n')[:5]
                        for line in lines:
                            if line.strip() and 'gpon' in line.lower():
                                log_callback(f"      {line.strip()}\n")
                    else:
                        log_callback(f"    ❌ Discovery failed: {disc_cmd}\n")
                        
                except Exception:
                    continue
            
            if available_interfaces:
                log_callback(f"    📋 Available GPON interfaces found: {set(available_interfaces)}\n")
                log_callback(f"    💡 Try using one of these instead of gpon {slot}/{port}\n")
            else:
                log_callback(f"    ❌ No GPON interfaces discovered\n")
                log_callback(f"    💡 Continuing anyway - commands might work in global config mode\n")
        
        time.sleep(1.0)  # Wait for interface mode to be active

        # 1.7. Detect OLT vendor and get appropriate commands
        vendor = detect_olt_vendor(client, log_callback)
        
        # If unknown vendor, try to discover available commands
        if vendor == "unknown":
            log_callback("[+] Exploring available CLI commands...\n")
            
            # Try common command patterns to understand the CLI
            exploration_commands = [
                "help",
                "?",
                "show ?",
                "gpon ?", 
                "ont ?",
                "onu ?",
                "interface ?",
                "configure ?",
                "config ?",
                "enable",
                "en"
            ]
            
            working_commands = []
            for exp_cmd in exploration_commands:
                try:
                    log_callback(f"    Exploring: {exp_cmd}\n")
                    exp_response = client.exec_cmd(exp_cmd, timeout=5.0)
                    
                    if exp_response and "unknown command" not in exp_response.lower():
                        working_commands.append((exp_cmd, exp_response))
                        log_callback(f"    ✅ '{exp_cmd}' works!\n")
                        
                        # Look for hints about command structure
                        if "gpon" in exp_response.lower():
                            log_callback(f"    💡 Found GPON commands in response\n")
                        if "ont" in exp_response.lower():
                            log_callback(f"    💡 Found ONT commands in response\n")
                        if "interface" in exp_response.lower():
                            log_callback(f"    💡 Found interface commands in response\n")
                    
                except Exception:
                    continue
            
            if working_commands:
                log_callback(f"    📝 Found {len(working_commands)} working commands\n")
                
                # Now try specific interface-level commands
                log_callback(f"[+] Exploring interface-specific commands...\n")
                interface_commands = [
                    "?",
                    "help", 
                    "ont ?",
                    "onu ?",
                    "add ?",
                    "create ?",
                    "set ?",
                    "configure ?",
                    # Try direct commands without parameters
                    "ont",
                    "onu", 
                    "add",
                    "create",
                    "set"
                ]
                
                interface_working = []
                for int_cmd in interface_commands:
                    try:
                        log_callback(f"      Interface cmd: {int_cmd}\n")
                        int_response = client.exec_cmd(int_cmd, timeout=5.0)
                        
                        if int_response and "unknown command" not in int_response.lower():
                            interface_working.append((int_cmd, int_response))
                            log_callback(f"      ✅ '{int_cmd}' works in interface mode!\n")
                            
                            # Look for parameter hints in response
                            if "syntax" in int_response.lower() or "usage" in int_response.lower():
                                log_callback(f"      💡 Found syntax help\n")
                        else:
                            log_callback(f"      ❌ '{int_cmd}' failed\n")
                    except Exception:
                        continue
                
                log_callback(f"    📋 Interface commands working: {len(interface_working)}\n")
                
                # CRITICAL: Add syntax discovery for working commands
                log_callback(f"[+] SYNTAX DISCOVERY: Testing exact command patterns...\n")
                
                # Since 'onu ?' works, let's test ONLY successful patterns from discovery
                onu_syntax_tests = [
                    "onu allow-list ?",  # We know this works - get full syntax
                    "onu auto-upgrade ?", # We know this works - get full syntax
                ]
                
                for syntax_cmd in onu_syntax_tests:
                    try:
                        log_callback(f"      Testing syntax: {syntax_cmd}\n")
                        syntax_response = client.exec_cmd(syntax_cmd, timeout=5.0)
                        
                        if syntax_response and "unknown command" not in syntax_response.lower():
                            log_callback(f"      ✅ SYNTAX WORKS: {syntax_cmd}\n")
                            
                            # Show the syntax help
                            lines = syntax_response.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith("KKY-OLT") and not line.startswith("DOD-OLT") and "%" not in line:
                                    log_callback(f"        📝 {line}\n")
                        else:
                            log_callback(f"      ❌ Syntax failed: {syntax_cmd}\n")
                    except Exception:
                        continue
                
            else:
                log_callback(f"    ❌ No working commands found - OLT may need different approach\n")
        
        # 2. Build commands based on vendor
        commands = get_vendor_commands(vendor, data)

        # 3. Execution loop - send commands one by one with proper timing
        log_callback("\n" + "=" * 60 + "\n")
        log_callback(f"INANZA KUTUMA TELNET COMMANDS KWENYE OLT INTERFACE gpon-olt_{slot}/{port}:\n")
        log_callback("=" * 60 + "\n\n")

        # If unknown vendor and few commands, do focused discovery  
        if vendor == "unknown" and len(commands) <= 10:
            log_callback("[+] FOCUSED DISCOVERY: Testing ONLY working command patterns...\n")
            log_callback("=" * 40 + "\n")
            
            # Test ONLY commands we know work from discovery
            working_help_commands = ["onu allow-list ?", "onu auto-upgrade ?"]
            
            for help_cmd in working_help_commands:
                try:
                    log_callback(f"Testing working syntax: {help_cmd}\n")
                    help_response = client.exec_cmd(help_cmd, timeout=5.0)
                    
                    if help_response and "unknown command" not in help_response.lower():
                        log_callback(f"✅ SUCCESS: {help_cmd}\n")
                        
                        # Show useful lines from help output
                        lines = help_response.split('\n')
                        for line in lines[:10]:  # First 10 lines
                            line = line.strip()
                            if line and not line.startswith("KKY-OLT") and not line.startswith("DOD-OLT") and "%" not in line:
                                if any(keyword in line.lower() for keyword in ["sn", "auth", "equipment", "list", "onu"]):
                                    log_callback(f"  💡 {line}\n")
                        log_callback("\n")
                    else:
                        log_callback(f"❌ Failed: {help_cmd}\n")
                        
                except Exception as e:
                    log_callback(f"⚠️ Error: {help_cmd} - {str(e)}\n")
            
            log_callback("=" * 40 + "\n")
            log_callback("Now trying ONLY discovered working commands...\n\n")

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
                        
            elif "invalid sn" in response_lower:
                log_callback(f"    ⚠️ SERIAL NUMBER FORMAT ERROR!\n")
                log_callback(f"    💡 SN '{cmd.split()[-1]}' format is not accepted by OLT\n")
                log_callback(f"    🔧 Try: UPPERCASE, add/remove GPON prefix, or different format\n")
            elif "command incomplete" in response_lower:
                log_callback(f"    ⚠️ COMMAND INCOMPLETE: Needs more parameters\n")
                log_callback(f"    💡 The command syntax is correct but missing required parameters\n")
            elif any(error_word in response_lower for error_word in ["error", "fail", "denied"]):
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
        log_callback("✔ ONU CONFIGURATION COMPLETED!\n")
        log_callback(f"Total commands executed: {total_commands}\n")
        log_callback(f"Interface: gpon_{slot}/{port}\n")
        log_callback("=" * 60 + "\n")
        status_callback("Configuration completed successfully!", "#38a169")

    except Exception as e:
        log_callback(f"\n❌ ERROR: {str(e)}\n")
        status_callback("Configuration failed - please check connection!", "#e53e3e")

    finally:
        client.close()
        done_callback()