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

def read_esp32(port='COM4', baud_rate=115200):
    """
    Read ESP32 flash memory contents
    """
    try:
        print(f"Reading ESP32 flash memory on {port}")
        print("Please make sure your ESP32 is in bootloader mode")
        print("Hold the BOOT button and press RESET, then release BOOT")
        
        # Prepare arguments for esptool
        args = [
            '--port', port,
            '--baud', str(baud_rate),
            '--before', 'default_reset',
            '--after', 'hard_reset',
            'read_flash',
            '0x1000',  # Start address
            '0x1000',  # Size to read (4KB)
            'firmware_backup.bin'  # Output file
        ]

        # Run esptool with arguments
        command = esptool.main(args)
        
        if os.path.exists('firmware_backup.bin'):
            print("\nFlash contents have been saved to 'firmware_backup.bin'")
            print("This is a backup of the first 4KB of your ESP32's flash memory")
            print("The file contains the bootloader and partition table")
        else:
            print("Error: Failed to create backup file")
        
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # List available COM ports
    list_com_ports()
    
    # You can specify port as command line argument
    port = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
    read_esp32(port=port) 