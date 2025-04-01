import network
import urequests
import esp
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# WiFi credentials
WIFI_SSID = "x-x"
WIFI_PASSWORD = "x"

# AWS S3 configuration
S3_BUCKET_HOST = "YOUR_S3_BUCKET_HOST"
FIRMWARE_PATH = "YOUR_FIRMWARE_PATH"
FIRMWARE_URL = f"https://{S3_BUCKET_HOST}/{FIRMWARE_PATH}"

def connect_wifi():
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        logging.info('Connecting to WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection with timeout
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            
        if wlan.isconnected():
            logging.info('WiFi connected successfully')
            logging.info(f'Network config: {wlan.ifconfig()}')
            return True
        else:
            logging.error('Failed to connect to WiFi')
            return False
    else:
        logging.info('Already connected to WiFi')
        return True

def update_firmware():
    """Download and install firmware update from S3"""
    try:
        logging.info('Starting firmware update...')
        
        # Download firmware
        logging.info(f'Downloading firmware from {FIRMWARE_URL}')
        response = urequests.get(FIRMWARE_URL)
        
        if response.status_code != 200:
            logging.error(f'Failed to download firmware: {response.status_code}')
            return False
            
        firmware_size = len(response.content)
        logging.info(f'Firmware size: {firmware_size} bytes')
        
        # Start OTA update
        logging.info('Starting OTA update...')
        esp.ota_start()
        
        # Write firmware in chunks
        chunk_size = 1024
        bytes_written = 0
        
        while bytes_written < firmware_size:
            chunk = response.content[bytes_written:bytes_written + chunk_size]
            esp.ota_write(chunk)
            bytes_written += len(chunk)
            logging.info(f'Written {bytes_written}/{firmware_size} bytes')
            
        # Verify and finish update
        if bytes_written == firmware_size:
            logging.info('Firmware written successfully')
            esp.ota_end()
            logging.info('OTA update completed')
            return True
        else:
            logging.error('Firmware size mismatch')
            return False
            
    except Exception as e:
        logging.error(f'Error during update: {str(e)}')
        return False

def main():
    """Main function"""
    logging.info('Starting ESP32 OTA Update')
    
    # Connect to WiFi
    if not connect_wifi():
        logging.error('Failed to connect to WiFi')
        return
        
    # Update firmware
    if update_firmware():
        logging.info('Update successful, rebooting...')
        time.sleep(2)
        esp.ota_reboot()
    else:
        logging.error('Update failed')

if __name__ == '__main__':
    main()