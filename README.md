# GPON ONU Configurator

A Python-based GUI application for configuring GPON ONUs (Optical Network Units) via Telnet connection to OLT (Optical Line Terminal) devices.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Features

- **User-friendly GUI** - Built with Tkinter for easy configuration
- **Telnet Connection** - Direct communication with OLT devices
- **Real-time Logging** - Live command execution feedback
- **Test Mode** - Preview commands without executing them
- **Standalone Executable** - No Python installation required for end users
- **Comprehensive Configuration** - Complete ONU setup including:
  - ONU positioning (Slot, Port, ID)
  - PPPoE authentication
  - VLAN configuration  
  - WiFi settings (2.4GHz & 5GHz)
  - LAN port bindings

## 📋 Requirements

### For Running Source Code
- Python 3.12 or higher
- tkinter (included with Python)
- Standard library modules: `socket`, `re`, `time`, `threading`, `json`

### For Building Executable
- PyInstaller 6.0+

## 🛠️ Installation

### Option 1: Download Executable (Recommended)
1. Download `GPON-ONU-Configurator.exe` from the releases page
2. Double-click to run - no installation needed!

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/mudddywa3/gpon-onu-configurator.git
cd gpon-onu-configurator

# Run the application
python main.py
```

### Option 3: Build Your Own Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "GPON-ONU-Configurator" main.py
```

## 💻 Usage

### Basic Setup
1. **Launch** the application
2. **Configure OLT Connection**:
   - Enter OLT IP address
   - Provide username and password
   - Optional: Enable "Test Mode" to preview commands

3. **Set ONU Details**:
   - Slot and Port numbers
   - ONU ID
   - GPON Serial Number
   - Description (optional)

4. **Configure Services**:
   - PPPoE username and password
   - VLAN settings
   - WiFi credentials and SSID preferences
   - LAN port bindings

5. **Execute Configuration**:
   - Click "Generate Command"
   - Monitor real-time execution in the log area

### Test Mode
Enable "Test Mode" to:
- Preview generated commands
- Verify configuration without connecting to OLT
- Debug command generation logic

## 🏗️ Architecture

The application consists of three main modules:

- **`main.py`** - GUI interface and user interaction
- **`olt_telnet.py`** - Telnet client for OLT communication
- **`olt_command.py`** - Command generation and execution logic

## 📊 Command Flow

```
User Input → Command Generation → Telnet Connection → OLT Execution → Real-time Feedback
```

1. **Input Validation** - Verify all required fields
2. **Command Building** - Generate OLT-specific CLI commands
3. **Telnet Session** - Establish secure connection to OLT
4. **Sequential Execution** - Execute commands with proper timing
5. **Response Monitoring** - Parse and display OLT responses

## 🔧 Configuration Examples

### Typical ONU Configuration
- **Slot**: 0, **Port**: 1, **ONU ID**: 1
- **GPON S/N**: GPON00663G65
- **PPPoE**: username@provider / password
- **VLAN**: Tag mode, Port 150
- **WiFi**: 2.4GHz + 5GHz enabled
- **LAN**: All ports (1-4) bound

## 🚨 Troubleshooting

### Application Won't Start
- Run as Administrator
- Check Windows Defender/Antivirus settings
- Verify .NET Framework is installed

### Connection Issues
- Verify OLT IP address and credentials
- Check network connectivity
- Use Test Mode to debug command generation

### Configuration Errors
- Review log output for specific error messages
- Verify ONU serial number format
- Check VLAN ID ranges (1-4094)

## 🧪 Testing

The application includes built-in testing features:
- **Test Mode** - Command preview without execution
- **Real-time Logging** - Detailed execution feedback
- **Error Detection** - Automatic error response parsing

## 📁 Project Structure

```
gpon-onu-configurator/
├── main.py                     # Main GUI application
├── olt_telnet.py              # Telnet client module
├── olt_command.py             # Command generation module
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── README_EXE.md             # Executable usage guide
├── .gitignore                # Git ignore rules
└── dist/                     # Built executables
    └── GPON-ONU-Configurator.exe
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛡️ Security

- **No sensitive data storage** - Credentials are used only during session
- **Local execution** - No data sent to external servers
- **Open source** - Code is available for security review

## 📞 Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Check `README_EXE.md` for executable usage
- **Email**: muddywa3@gmail.com

## 🏷️ Version History

- **v1.0** - Initial release with core functionality
  - GUI-based ONU configuration
  - Telnet OLT communication
  - Real-time command execution
  - Standalone executable build

## 🙏 Acknowledgments

- Built with Python and Tkinter
- Packaged with PyInstaller
- Designed for network administrators and field technicians

---

**⭐ Star this repository if it helps you configure ONUs more efficiently!**