import os
import sys
import time
import serial
import esptool
from pathlib import Path
from serial.tools import list_ports

def list_com_ports():
    """List all available COM ports"""
    ports = list_ports.comports()
    if not ports:
        print("No COM ports found!")
        return
    
    print("\nAvailable COM ports:")
    for port in ports:
        print(f"- {port.device}: {port.description}")

def flash_esp32(port='COM4', baud_rate=115200, firmware_path='firmware/esp32-firmware.bin'):
    """
    Flash firmware to ESP32 using esptool
    """
    try:
        # Check if firmware file exists
        if not os.path.exists(firmware_path):
            print(f"Error: Firmware file not found at {firmware_path}")
            return False

        print(f"Flashing firmware from {firmware_path} to ESP32 on {port}")
        print("Please make sure your ESP32 is in bootloader mode")
        print("Hold the BOOT button and press RESET, then release BOOT")
        
        # Prepare arguments for esptool
        args = [
            '--port', port,
            '--baud', str(baud_rate),
            '--before', 'default_reset',
            '--after', 'hard_reset',
            'write_flash',
            '--flash_mode', 'dio',
            '--flash_size', '4MB',
            '--flash_freq', '40m',
            '0x1000', firmware_path
        ]

        # Run esptool with arguments
        command = esptool.main(args)
        
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # List available COM ports
    list_com_ports()
    
    # You can specify port as command line argument
    port = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
    flash_esp32(port=port) 