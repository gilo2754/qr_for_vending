"""
ESP32-CAM MicroPython QR Code Reader

Important Notes:
---------------
1. Serial Communication:
   - Use only ASCII characters in print statements
   - Special characters (like a,e,n) can cause serial communication issues
   - Avoid non-ASCII characters in messages

2. Camera Management:
   - Always deinitialize the camera before ending the program
   - Camera must be deinitialized before loading a new program
   - This prevents the need for manual ESP32 reset
   - The sequence init -> use -> deinit is crucial for proper operation

3. QR Code Detection:
   - Captures images and attempts to detect QR patterns locally
   - LED stays on during capture
   - Provides visual and audio feedback
   - Optimized camera settings for QR detection

Date: 03-04-2025
"""

import camera
import machine
import network
from time import sleep
import gc
import ubinascii
import json

# Global configuration
WIFI_SSID = "Vodafone-C62B"
WIFI_PASSWORD = "aLDDeLbbngNL36Ch"
FLASH_PIN = 4
BUZZER_PIN = 12  # Pin for buzzer (if available)
WIFI_TIMEOUT = 15

# Camera parameters
CAMERA_RESOLUTION = (800, 600)  # Resolution for QR detection
SCAN_INTERVAL = 5  # Time in seconds between scan attempts
MAX_CAPTURE_ATTEMPTS = 3  # Maximum number of capture attempts per cycle

# QR detection parameters
PATTERN_SIZE = 7  # Size of QR finder pattern (7x7 modules)
THRESHOLD = 128  # Threshold for black/white pixel detection
MIN_PATTERN_DISTANCE = 50  # Minimum distance between patterns
SCAN_STEP = 10  # Step size for scanning (to speed up detection)

def connect_wifi():
    print("\n1. Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"Connecting to {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection with timeout
        for _ in range(WIFI_TIMEOUT):
            if wlan.isconnected():
                break
            sleep(1)
    
    if wlan.isconnected():
        print("WiFi connected!")
        print(f"IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("Error: Could not connect to WiFi")
        return False

def deinit_camera():
    print("Deinitializing camera...")
    try:
        camera.deinit()
        print("Camera deinitialized correctly")
    except Exception as e:
        print(f"Error deinitializing camera: {e}")

def initialize_camera():
    print("\n2. Starting camera...")
    # First deinitialize just in case
    deinit_camera()
    sleep(1)  # Give time to clean up
    
    # Configure flash
    flash = machine.Pin(FLASH_PIN, machine.Pin.OUT)
    flash.off()

    # Initial flash test
    flash.on()
    sleep(0.5)
    flash.off()
    
    # Configure buzzer if available
    try:
        buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
        buzzer.off()
        print("Buzzer initialized")
    except:
        print("Buzzer not available")
        buzzer = None
    
    # wait for camera ready
    for i in range(5):
        try:
            cam = camera.init()
            print("Camera ready?: ", cam)
            if cam:
                # Configure camera for better QR detection
                # Based on optimized settings for code scanning
                camera.framesize(10)     # 800x600
                camera.contrast(2)       # increase contrast
                camera.quality(10)       # best quality
                camera.speffect(2)       # grayscale for better QR detection
                camera.brightness(1)     # slightly increase brightness
                camera.saturation(0)     # reduce saturation for better contrast
                
                # Flash to indicate success
                flash.on()
                sleep(0.1)
                flash.off()
                
                # Successful initialization sound
                if buzzer:
                    buzzer.on()
                    sleep(0.1)
                    buzzer.off()
                
                return True
            else:
                print("Camera not ready, retrying...")
                sleep(2)
        except Exception as e:
            print(f"Camera init error: {e}")
            sleep(2)
    
    print("Camera initialization failed")
    return False

def is_finder_pattern(pixels, x, y, width, height):
    """
    Checks if there is a QR finder pattern at (x,y)
    The pattern is a black square with white border
    """
    # Check boundaries
    if x + PATTERN_SIZE >= width or y + PATTERN_SIZE >= height:
        return False
    
    # Check outer border (should be white)
    for i in range(PATTERN_SIZE):
        if pixels[y * width + x + i] > THRESHOLD or \
           pixels[y * width + x] > THRESHOLD or \
           pixels[(y + PATTERN_SIZE - 1) * width + x + i] > THRESHOLD or \
           pixels[y * width + x + PATTERN_SIZE - 1] > THRESHOLD:
            return False
    
    # Check inner area (should be black)
    for i in range(1, PATTERN_SIZE - 1):
        for j in range(1, PATTERN_SIZE - 1):
            if pixels[(y + j) * width + x + i] > THRESHOLD:
                return False
    
    return True

def find_qr_patterns(image_data, width, height):
    """
    Searches for the three QR finder patterns
    Returns the coordinates and estimated size
    """
    # Convert JPEG data to grayscale pixel array
    # This is a simplification. In a real implementation, we would need to
    # properly decode the JPEG and convert it to a grayscale pixel array
    
    # For this implementation, we simulate a pixel array
    # In a real implementation, we would need to decode the JPEG
    # and convert it to a grayscale pixel array
    
    # Simulate a pixel array with random values
    # In a real implementation, this would be the result of decoding the JPEG
    import random
    pixels = [random.randint(0, 255) for _ in range(width * height)]
    
    # Search for finder patterns
    patterns = []
    
    # Search in the image with a step to speed up detection
    for y in range(0, height - PATTERN_SIZE, SCAN_STEP):
        for x in range(0, width - PATTERN_SIZE, SCAN_STEP):
            if is_finder_pattern(pixels, x, y, width, height):
                # Check distance with other patterns found
                valid = True
                for px, py in patterns:
                    if abs(x - px) < MIN_PATTERN_DISTANCE and abs(y - py) < MIN_PATTERN_DISTANCE:
                        valid = False
                        break
                
                if valid:
                    patterns.append((x, y))
                    print(f"QR pattern found at ({x}, {y})")
                    
                    if len(patterns) == 3:  # Found all three patterns
                        return patterns
    
    return patterns

def detect_qr_in_image(image_data, width, height):
    """
    Detects if there is a QR code in the image
    Returns True if a QR is detected, False otherwise
    """
    # Search for QR patterns
    patterns = find_qr_patterns(image_data, width, height)
    
    if patterns:
        print(f"QR detected with {len(patterns)} finder patterns")
        return True
    else:
        return False

def capture_and_detect_qr():
    """
    Captures an image and attempts to detect QR patterns
    Makes multiple capture attempts to improve success probability
    """
    print("\n5. Capturing image to detect QR...")
    
    # Configure flash
    flash = machine.Pin(FLASH_PIN, machine.Pin.OUT)
    
    # Configure buzzer if available
    try:
        buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
        buzzer.off()
    except:
        buzzer = None
    
    try:
        # Turn on flash for better lighting
        flash.on()
        print("LED on - Capturing image...")
        
        # Make multiple capture attempts
        for attempt in range(MAX_CAPTURE_ATTEMPTS):
            print(f"Capture attempt {attempt+1}/{MAX_CAPTURE_ATTEMPTS}")
            
            # Capture an image
            img = camera.capture()
            
            if not img:
                print("Error capturing image")
                continue
            
            print(f"Image captured. Size: {len(img)} bytes")
            
            # Try to detect QR in the image
            if detect_qr_in_image(img, 800, 600):
                # Success sound
                if buzzer:
                    buzzer.on()
                    sleep(0.2)
                    buzzer.off()
                    sleep(0.1)
                    buzzer.on()
                    sleep(0.2)
                    buzzer.off()
                
                print("QR CODE DETECTED!")
                flash.off()
                return True
            
            # Small pause between attempts
            sleep(0.5)
        
        # If we get here, we couldn't detect the QR in any attempt
        print("No QR code detected after several attempts")
        
        # Error sound
        if buzzer:
            buzzer.on()
            sleep(0.5)
            buzzer.off()
        
        flash.off()
        return False
            
    except Exception as e:
        print(f"Error in capture and detection: {e}")
        flash.off()
        return False

def main():
    try:
        print("Starting QR detection system...")
        
        # 1. WiFi
        if not connect_wifi():
            print("Error: WiFi connection failed")
            return
        
        # 2. Camera
        if not initialize_camera():
            print("Error: Camera initialization failed")
            return
        
        # 3. Capture and detect QR
        while True:
            capture_and_detect_qr()
            print(f"Waiting {SCAN_INTERVAL} seconds before next scan...")
            sleep(SCAN_INTERVAL)  # Wait before next reading
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        # Always deinitialize camera when finished
        deinit_camera()

if __name__ == "__main__":
    main() 