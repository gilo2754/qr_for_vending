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

3. QR Code Detection:
   - Uses the camera to capture an image
   - Processes the image to detect QR codes locally
   - Decodes the QR code data if found
   - Sends the decoded value to the API

Date: 03-04-2025
"""

import camera
import machine
import network
import urequests
from time import sleep
import gc
import framebuf
import ubinascii

# Global configuration
WIFI_SSID = "Vodafone-C62B"
WIFI_PASSWORD = "aLDDeLbbngNL36Ch"
FLASH_PIN = 4
WIFI_TIMEOUT = 15
API_URL = "http://your-api-url/qrdata"
MAX_RESPONSE_LENGTH = 300

# QR Code detection parameters
QR_DETECTION_THRESHOLD = 30  # Adjust based on testing
QR_MIN_SIZE = 20  # Minimum size of QR code in pixels

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

def find_qr_patterns(image_data, width, height):
    """
    Busca patrones de QR en la imagen
    Retorna las coordenadas de posibles códigos QR
    """
    # Convertir imagen a framebuffer para procesamiento
    fb = framebuf.FrameBuffer(image_data, width, height, framebuf.GS8)
    
    # Buscar patrones de QR (marcadores de posición)
    qr_candidates = []
    
    # Buscar patrones de esquina (patrón de búsqueda)
    for y in range(height - QR_MIN_SIZE):
        for x in range(width - QR_MIN_SIZE):
            # Verificar patrón de esquina (cuadrado negro con borde blanco)
            if is_qr_corner_pattern(fb, x, y, width, height):
                qr_candidates.append((x, y))
    
    return qr_candidates

def is_qr_corner_pattern(fb, x, y, width, height):
    """
    Verifica si hay un patrón de esquina de QR en la posición (x,y)
    """
    # Tamaño del patrón a verificar
    pattern_size = 7
    
    # Verificar que estamos dentro de los límites
    if x + pattern_size >= width or y + pattern_size >= height:
        return False
    
    # Verificar patrón de esquina (cuadrado negro con borde blanco)
    # Primero verificar el borde exterior (debe ser blanco)
    for i in range(pattern_size):
        if fb.pixel(x + i, y) > QR_DETECTION_THRESHOLD or \
           fb.pixel(x, y + i) > QR_DETECTION_THRESHOLD or \
           fb.pixel(x + pattern_size - 1, y + i) > QR_DETECTION_THRESHOLD or \
           fb.pixel(x + i, y + pattern_size - 1) > QR_DETECTION_THRESHOLD:
            return False
    
    # Luego verificar el interior (debe ser negro)
    for i in range(1, pattern_size - 1):
        for j in range(1, pattern_size - 1):
            if fb.pixel(x + i, y + j) < QR_DETECTION_THRESHOLD:
                return False
    
    return True

def decode_qr_local(image_data, width, height):
    """
    Intenta decodificar un código QR localmente usando la biblioteca micropython-qr
    """
    try:
        # Importar la biblioteca QR
        import qr
        
        # Convertir imagen a formato adecuado para la biblioteca QR
        # Esto dependerá de la implementación específica de micropython-qr
        
        # Decodificar el QR
        qr_data = qr.decode(image_data)
        
        if qr_data:
            return qr_data
        return None
    except Exception as e:
        print(f"Error en decodificación QR: {e}")
        return None

def detect_and_decode_qr():
    print("\n5. Detectando y decodificando codigo QR...")
    flash = machine.Pin(FLASH_PIN, machine.Pin.OUT)
    
    try:
        # Encender el flash para mejor iluminación
        flash.on()
        sleep(0.1)
        
        # Capturar imagen
        img = camera.capture()
        
        # Apagar el flash
        flash.off()
        
        if img:
            print(f"Imagen capturada. Tamano: {len(img)} bytes")
            
            # Guardar la imagen para análisis
            try:
                with open("qr_capture.jpg", "wb") as f:
                    f.write(img)
                print("Imagen guardada como qr_capture.jpg")
            except Exception as e:
                print(f"Error al guardar imagen: {e}")
            
            # Decodificar QR localmente
            qr_value = decode_qr_local(img, 800, 600)
            
            if qr_value:
                print(f"Codigo QR detectado localmente: {qr_value}")
                
                # Enviar el valor decodificado a la API
                try:
                    print(f"Enviando valor QR a API: {qr_value}")
                    response = urequests.post(API_URL, json={"qr_data": qr_value})
                    print(f"API Response: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("Valor QR enviado exitosamente")
                    else:
                        print("Error al enviar valor QR a la API")
                    
                    response.close()
                except Exception as e:
                    print(f"Error en request de API: {e}")
            else:
                print("No se pudo decodificar el codigo QR")
        else:
            print("Error al capturar imagen para QR")
            
    except Exception as e:
        print(f"Error en deteccion QR: {e}")
        flash.off()

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
        
        # 5. Detectar y decodificar QR
        detect_and_decode_qr()
        
        print("\nPrueba completa finalizada!")
        
    finally:
        # Siempre desinicializar la cámara al terminar
        deinit_camera()

if __name__ == "__main__":
    main() 