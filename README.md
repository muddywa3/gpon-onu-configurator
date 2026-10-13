# GPON ONU Configurator

A Python GUI application for automated GPON ONU configuration on OLT systems via Telnet.

## Features

- **Multi-Vendor Support**: V-SOL, Huawei, ZTE, Nokia/Alcatel OLT systems
- **Automatic Vendor Detection**: Detects OLT type from `show version` output
- **GPON SN Validation**: Supports multiple serial number formats (VSOL1A2B3C4D, GPON006523777)
- **Auto Enable Password Discovery**: Tries common enable passwords automatically
- **Test Mode**: Preview commands without connecting to OLT
- **Discovery Mode**: Explore available OLT commands
- **Configuration Save/Load**: Save and restore configuration settings

## Supported OLT Vendors

### V-SOL (V5600X2, V5600X7)
- Auto-detects V-SOL OLT systems
- Uses proper V-SOL workflow: register → configure → enable
- Commands: `onu add`, `onu tcont`, `onu gemport`, `onu vlan`

### Huawei (MA5608T, MA5683T)
- Standard Huawei ONT workflow
- Commands: `ont add`, `ont port native-vlan`, `service-port`

### ZTE (C300, C320)
- ZTE-specific command syntax
- Commands: `onu type`, `pon-onu-mng`, `service HSI`

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- Network access to OLT via Telnet (port 23)

## Installation

1. **Download/Clone** the application files
2. **Install Python** (if not already installed)
3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Basic Configuration

1. **OLT Connection**:
   - IP Address: Your OLT IP (e.g., 192.168.1.100)
   - Username: OLT username (usually `admin`)
   - Password: OLT login password
   - Enable Password: Leave empty to auto-detect

2. **ONU Position**:
   - Slot: GPON slot number (0-15)
   - Port: GPON port number (1-16)  
   - ONU ID: Unique ONU identifier (1-128)
   - GPON S/N: Valid GPON serial number

3. **Service Configuration**:
   - PPPoE Username/Password: Customer credentials
   - VLAN Port: Service VLAN ID
   - WiFi Settings: SSID name and password

### GPON Serial Number Formats

The application supports multiple GPON SN formats:

- **Vendor Format**: `VSOL1A2B3C4D` (4 letters + 8 hex digits)
- **GPON Format**: `GPON006523777` (GPON prefix + alphanumeric)

Examples of **valid** serial numbers:
- `VSOL12345678`
- `HWTC1A2B3C4D` 
- `GPON00663G65`
- `GPON382956573`

### Test Mode

Use **Test Mode** to preview generated commands without connecting to the OLT:

1. Check "Test Mode" checkbox
2. Fill in configuration fields
3. Click "Start Configuration"
4. Commands will be displayed in a message box

### Discovery Mode

Use **Discovery Mode** to explore available commands on unknown OLT systems:

1. Check "Discovery Mode" checkbox  
2. Enter OLT connection details
3. Click "Start Configuration"
4. System will test various commands and show results

## Configuration Files

### Save/Load Settings

- **Save Config**: Export current form data to JSON file (passwords excluded for security)
- **Load Config**: Import previously saved configuration

### Example Configuration
```json
{
  "olt_ip": "192.168.1.100",
  "olt_username": "admin", 
  "slot": "2",
  "port": "16",
  "onu_id": "5",
  "gpon_sn": "VSOL12345678",
  "pppoe_username": "customer@isp.com",
  "vlan_port": "150",
  "wifi_username": "CustomerWiFi"
}
```

## Troubleshooting

### Common Issues

**"Enable password authentication failed"**
- Try common passwords: `admin`, `enable`, `password`
- Leave Enable Password field empty for auto-detection
- Check if OLT requires privileged access

**"Unknown command" errors**
- Verify you're connected to the correct OLT interface  
- Use Discovery Mode to explore available commands
- Check if OLT vendor is properly detected

**"Invalid GPON SN" errors**
- Verify SN format: 4 letters + 8 hex OR GPON + alphanumeric
- Examples: `VSOL1A2B3C4D`, `GPON006523777`
- Remove spaces and special characters

**Connection timeout**
- Verify OLT IP address and Telnet port (23)
- Check network connectivity
- Ensure OLT allows Telnet connections

### Enable Password Auto-Detection

The system automatically tries these passwords in order:
1. User-provided enable password
2. Same as login password  
3. `admin`
4. `enable`
5. `password`
6. `vsol` 
7. Empty password

## File Structure

```
gpon-onu-configurator/
├── main.py              # GUI application
├── olt_command.py       # OLT command generation and execution
├── olt_telnet.py        # Telnet client implementation
├── README.md            # This documentation
└── requirements.txt     # Python dependencies
```

## Security Notes

- **Passwords**: Not saved in configuration files for security
- **Telnet**: Uses unencrypted Telnet protocol (standard for OLT management)
- **Credentials**: Only stored in memory during execution

## License

This project is provided as-is for educational and professional use.

## Contributing

Contributions welcome! Please test thoroughly with your specific OLT models before submitting changes.

---

**Version**: 2.0  
**Author**: Network Automation Tools  
**Last Updated**: 2024