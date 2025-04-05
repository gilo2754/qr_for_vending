"""
ESP32-CAM MicroPython Test Script

Important Notes:
---------------
1. Serial Communication:
   - Use only ASCII characters in print statements
   - Special characters (like á,é,ñ) can cause serial communication issues
   - Avoid non-ASCII characters in messages

2. Camera Management:
   - Always deinitialize the camera before ending the program
   - Camera must be deinitialized before loading a new program
   - This prevents the need for manual ESP32 reset
   - The sequence init -> use -> deinit is crucial for proper operation

Date: 03-04-2025
"""

# test_cam_led_wifi.py - ESP32 MicroPython script to test camera and flash LED (Simplified)

import camera
import machine
import network
import urequests
from time import sleep

# Configuracion global al inicio del archivo
WIFI_SSID = "SSID"
WIFI_PASSWORD = "PASSWORD"
FLASH_PIN = 4
WIFI_TIMEOUT = 15
API_URL = "http://httpbin.org/get"
MAX_RESPONSE_LENGTH = 300  # Nueva constante para controlar longitud de respuesta

def connect_wifi():
    print("\n1. Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    
    if not sta_if.active():
        sta_if.active(True)
        sleep(1)
        print("Interfaz WiFi activada")

    if sta_if.isconnected():
        print("Ya conectado al WiFi")
        print("Config de red:", sta_if.ifconfig())
        return True

    print(f"Intentando conectar a {WIFI_SSID}")
    try:
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        attempts = 0
        while not sta_if.isconnected() and attempts < WIFI_TIMEOUT:
            print(".", end="")
            sleep(1)
            attempts += 1
            
        if sta_if.isconnected():
            print("\nConexion exitosa!")
            print("Config de red:", sta_if.ifconfig())
            return True
        else:
            print("\nTimeout en conexion")
            return False
            
    except Exception as e:
        print(f"\nError en conexion: {e}")
        return False

def deinit_camera():
    try:
        camera.deinit()
        print("Camara desinicializada")
    except:
        pass

def initialize_camera():
    print("\n2. Iniciando camara...")
    # Primero desinicializar por si acaso
    deinit_camera()
    sleep(1)  # Dar tiempo a que se limpie
    
    # Configurar el flash
    flash = machine.Pin(4, machine.Pin.OUT)
    flash.off()

    # Test flash inicial
    flash.on()
    sleep(0.5)
    flash.off()
    
    # wait for camera ready
    for i in range(5):
        try:
            cam = camera.init()
            print("Camera ready?: ", cam)
            if cam:
                # Configurar la cámara
                camera.framesize(10)     # 800x600
                camera.contrast(2)       # increase contrast
                camera.speffect(2)       # jpeg grayscale
                
                # Flash para indicar éxito
                flash.on()
                sleep(0.1)
                flash.off()
                return True
            else:
                print("Camera not ready, retrying...")
                sleep(2)
        except Exception as e:
            print(f"Camera init error: {e}")
            sleep(2)
    
    print("Camera initialization failed")
    return False

def take_test_photos():
    print("\n3. Tomando fotos de prueba...")
    flash = machine.Pin(FLASH_PIN, machine.Pin.OUT)
    
    for i in range(3):
        try:
            flash.on()
            sleep(0.1)
            img = camera.capture()
            flash.off()
            
            if img:
                print(f"Foto {i+1} capturada. Tamano: {len(img)} bytes")
            sleep(1)
            
        except Exception as e:
            print(f"Error en foto {i+1}: {e}")
            flash.off()

def make_api_request():
    print("\n4. Consultando API...")
    try:
        print(f"Intentando conectar a: {API_URL}")
        response = urequests.get(API_URL)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.text
                print("Respuesta recibida:")
                print(data[:MAX_RESPONSE_LENGTH])  # Usando la constante
            except Exception as e:
                print(f"Error al procesar respuesta: {e}")
        else:
            print("Error en la respuesta del servidor")
            
        response.close()
    except Exception as e:
        print(f"Error en API request: {e}")

def main():
    try:
        print("Iniciando prueba completa...")
        
        # 1. WiFi
        if not connect_wifi():
            print("Error: Fallo conexion WiFi")
            return
        
        # 2. Camara
        if not initialize_camera():
            print("Error: Fallo inicio de camara")
            return
        
        # 3. Fotos de prueba
        take_test_photos()
        
        # 4. Prueba API
        make_api_request()
        
        print("\nPrueba completa finalizada!")
        
    finally:
        # Siempre desinicializar la cámara al terminar
        deinit_camera()

if __name__ == "__main__":
    main()