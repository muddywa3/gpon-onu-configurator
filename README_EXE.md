# GPON ONU Configurator - Executable File

## Maelezo
Hii ni Python application iliyotengenezwa kuwa standalone executable (.exe) file ambayo haihitaji Python kuwa installed kwenye computer.

## Mafaili Muhimu
- `GPON-ONU-Configurator.exe` - Main executable file (12.37MB)
- `GPON-ONU-Configurator.spec` - PyInstaller configuration file

## Jinsi ya Kutumia

### 1. Kukimbia Application
- Double-click kwenye `GPON-ONU-Configurator.exe`
- Au fungua Command Prompt/PowerShell na run: `.\GPON-ONU-Configurator.exe`

### 2. Application Features
- **OLT Connection**: Weka IP ya OLT, username na password
- **Test Mode**: Checkbox ya kuonyesha commands tu bila kuzituma kwenye OLT
- **ONU Configuration**: Weka slot, port, ONU ID, GPON Serial Number
- **PPPoE Settings**: Username na password ya internet
- **VLAN Configuration**: VLAN mode na port ID
- **WiFi Settings**: SSID names, password, na port bindings

### 3. Vipengele vya Muhimu
- **Generate Command**: Button ya kuanza configuration process
- **Execution Log**: Real-time output ya commands zilizoexecute
- **Status Bar**: Onyesha hali ya current operation

## Technical Details

### Vitu Vilivyojumuishwa
- Python 3.12.10 runtime
- Tkinter GUI framework
- Socket networking libraries
- All project modules (main.py, olt_command.py, olt_telnet.py)

### System Requirements
- Windows 10/11 (64-bit)
- Hakuna Python installation inahitajika
- Memory: Angalau 50MB free RAM
- Disk Space: 15MB free space

### Build Information
- **PyInstaller Version**: 6.22.3
- **Build Type**: Single file executable (--onefile)
- **Window Mode**: Windowed (--windowed) - no console window
- **Compression**: UPX enabled
- **Build Date**: October 2026

## Troubleshooting

### Kama .exe haitafunguka:
1. Hakikisha una admin rights
2. Check antivirus - labda imblock executable
3. Try kurun from command line kuona error messages

### Kama application inafunguka lakini haifanyi kazi:
1. Check network connection kwenye OLT
2. Verify OLT credentials
3. Use Test Mode kwanza kuona commands zinatengenezwa vizuri

### Performance Issues:
- First run inaweza kuchukua muda kidogo (5-10 seconds) kusoma files
- Baada ya hapo itakuwa haraka

## Building from Source
Kama unataka kutengeneza .exe file mwenyewe:

```powershell
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "GPON-ONU-Configurator" main.py
```

## Security Notes
- Executable hii ni safe - built from clean Python source code
- Hakuna malicious code au hidden functionality
- Source code iko available kwa verification
- Antivirus inaweza warn kuhusu "unknown publisher" - hii ni normal

## Support
Kama una maswali au problems:
1. Check log output kwenye application
2. Try Test Mode kwanza
3. Verify network settings
4. Contact developer na details za error

---
**Version**: 1.0  
**Platform**: Windows x64  
**Python Version**: 3.12.10  
**Build Tool**: PyInstaller 6.22.3