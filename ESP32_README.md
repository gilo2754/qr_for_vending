# ESP32-CAM QR Code Reader Setup

This guide provides detailed instructions for setting up and using the ESP32-CAM module for QR code reading functionality.

## Hardware Specifications

### ESP32-CAM Module
- Chip: ESP32-D0WDQ6 (revision v1.0)
- Features: 
  - WiFi
  - Bluetooth
  - Dual Core
  - 240MHz CPU
  - VRef calibration in efuse
- Crystal: 40MHz
- Camera: OV2640 camera module
- Flash: 4MB

## Development Environment Setup

### 1. Python Environment Setup

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

3. Install required tools:
```bash
pip install mpremote
```

### 2. MicroPython Setup

1. Download the latest MicroPython firmware for ESP32-CAM
2. Flash the firmware to your ESP32-CAM module

## Working with ESP32

### File Management

1. Upload files to ESP32:
```bash
mpremote cp <filename> :
```

2. Run a program:
```bash
mpremote run <filename>
```

3. List files on ESP32:
```bash
mpremote ls
```

### Alternative Commands
If direct `mpremote` usage isn't working, use:
```bash
python -m mpremote cp <filename> :
python -m mpremote run <filename>
```

## Troubleshooting

1. **Connection Issues**
   - Ensure the ESP32 is in bootloader mode
   - Check USB connection
   - Verify correct COM port

2. **Upload Problems**
   - Make sure the correct firmware is installed
   - Check file permissions
   - Verify virtual environment is activated

## Additional Resources

- [ESP32-CAM Datasheet](https://docs.ai-thinker.com/en/esp32-cam)
- [MicroPython Documentation](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html)
- [ESP32-CAM Camera Examples](https://github.com/espressif/esp32-camera)

## Notes

- Always ensure your virtual environment is activated before running MPRemote commands
- Keep firmware updated to latest stable version
- Backup important files before major updates 