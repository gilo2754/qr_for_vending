import sys
import requests
import time
import os
from dotenv import load_dotenv
from enum import Enum
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qr_reader.log'),
        logging.StreamHandler()
    ]
)

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración del lector QR"""
    API_URL = os.getenv('API_URL', 'http://localhost:3000')
    QR_MIN_VALUE = float(os.getenv('QR_MIN_VALUE', '0.05'))

class QRStates(str, Enum):
    VALID = 'valido'
    USED = 'usado'
    EXPIRED = 'expirado'
    INVALIDATED = 'invalidado'

class QRReader:
    def __init__(self, api_url, min_value):
        self.api_url = api_url
        self.min_value = min_value
        self.session = requests.Session()
        self.server_available = False
        self.last_server_check = 0
        self.server_check_interval = 10  # segundos entre chequeos

    def check_server_status(self):
        """Verifica si el servidor está en funcionamiento"""
        current_time = time.time()
        
        # Solo verificar si han pasado server_check_interval segundos
        if current_time - self.last_server_check < self.server_check_interval:
            return self.server_available

        self.last_server_check = current_time
        try:
            response = self.session.get(f"{self.api_url}/", timeout=5)
            response.raise_for_status()
            if not self.server_available:  # Solo logear si el estado cambió
                logging.info(f"Conexión recuperada con el servidor: {self.api_url}")
            self.server_available = True
            return True
        except requests.exceptions.RequestException as e:
            if self.server_available:  # Solo logear si el estado cambió
                logging.error(f"Se perdió la conexión con el servidor: {str(e)}")
            self.server_available = False
            return False

    def wait_for_server(self):
        """Espera hasta que el servidor esté disponible"""
        retry_count = 0
        while not self.check_server_status():
            retry_count += 1
            if retry_count == 1:  # Solo mostrar en el primer intento
                logging.warning("Esperando conexión con el servidor...")
            time.sleep(5)  # Esperar 5 segundos entre intentos
            
    def get_qr_info(self, qr_code):
        url = f"{self.api_url}/api/qrdata/{qr_code}?fields=new_value,old_value,state"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def exchange_qr(self, qr_code):
        url = f"{self.api_url}/api/qrdata/exchange/{qr_code}"
        response = self.session.put(url)
        response.raise_for_status()
        return response.json()

    def calculate_pulses(self, value):
        return int(value / self.min_value)

    def process_qr(self, qr_code):
        # Verificar estado del servidor antes de procesar
        if not self.server_available and not self.check_server_status():
            logging.error("No se puede procesar el QR: Servidor no disponible")
            return False

        try:
            info = self.get_qr_info(qr_code)
            new_value = info.get('new_value', 0)
            old_value = info.get('old_value', 0)
            estado_qr = info.get('state', '')

            if new_value >= self.min_value and estado_qr == QRStates.VALID:
                pulsos = self.calculate_pulses(new_value)
                logging.info(f"Se generarían {pulsos} pulsos para el QR {qr_code}")
                logging.info(f"Valor anterior: {old_value}, Nuevo valor: {new_value}")

                result = self.exchange_qr(qr_code)
                logging.info(f"QR {qr_code} actualizado a {QRStates.USED.value} y valor a 0")
                return True
            else:
                if new_value < self.min_value:
                    logging.warning(f"El valor del QR {qr_code} es menor a {self.min_value}. No se generarían pulsos.")
                elif estado_qr != QRStates.VALID:
                    logging.warning(f"El estado del QR {qr_code} no es {QRStates.VALID.value}. No se generarían pulsos.")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"Error en la petición HTTP: {str(e)}")
            return False

def handle_qr_error(e, qr_code):
    if isinstance(e, requests.exceptions.ConnectionError):
        logging.error(f"Error de conexión al procesar QR {qr_code}: {e}")
    elif isinstance(e, requests.exceptions.Timeout):
        logging.error(f"Timeout al procesar QR {qr_code}: {e}")
    elif isinstance(e, requests.exceptions.HTTPError):
        logging.error(f"Error HTTP al procesar QR {qr_code}: {e}")
    else:
        logging.error(f"Error inesperado al procesar QR {qr_code}: {e}")

def leer_qr_desde_lector_usb():
    """Lee códigos QR desde un lector USB, procesa la información y actualiza la base de datos."""
    
    logging.info(f"Iniciando lector QR...")
    logging.info(f"API URL: {Config.API_URL}")
    logging.info(f"Valor mínimo QR: {Config.QR_MIN_VALUE}")

    # Crear instancia del lector QR
    reader = QRReader(Config.API_URL, Config.QR_MIN_VALUE)

    # Verificación inicial del servidor
    reader.wait_for_server()

    while True:
        try:
            # Verificar periódicamente el estado del servidor
            if not reader.check_server_status():
                logging.warning("Servidor no disponible - Esperando reconexión...")
                reader.wait_for_server()
                continue

            # Leer la línea completa enviada por el lector USB
            datos = input()
            datos = datos.strip()

            if not datos:
                continue

            logging.info(f"Código QR leído: {datos}")

            if reader.process_qr(datos):
                logging.info("Procesamiento de QR exitoso")
            else:
                logging.warning("No se pudo procesar el QR")

        except KeyboardInterrupt:
            logging.info("Programa terminado por el usuario.")
            break
        except Exception as e:
            handle_qr_error(e, datos if 'datos' in locals() else 'unknown')
            time.sleep(1)

if __name__ == "__main__":
    leer_qr_desde_lector_usb()

