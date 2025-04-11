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
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

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
        self.server_check_interval = 10
        self.reconnection_attempt = 0
        self.internet_check_urls = [
            "http://8.8.8.8",      # Google DNS
            "http://1.1.1.1"       # Cloudflare DNS
        ]

    def check_internet_connection(self):
        """Verifica si hay conexión a internet"""
        for url in self.internet_check_urls:
            try:
                requests.get(url, timeout=3)
                return True
            except requests.RequestException:
                continue
        return False

    def check_server_status(self):
        """Verifica si el servidor está en funcionamiento"""
        current_time = time.time()
        time_since_last_check = current_time - self.last_server_check
        
        # Mostrar cuenta regresiva si el servidor no está disponible
        if not self.server_available and time_since_last_check < self.server_check_interval:
            seconds_remaining = int(self.server_check_interval - time_since_last_check)
            print(f"\rPróximo intento de conexión en {seconds_remaining} segundos... (Intento #{self.reconnection_attempt})", end='')
            return False

        self.last_server_check = current_time
        
        # Primero verificar conexión a internet
        if not self.check_internet_connection():
            self.reconnection_attempt += 1
            if self.server_available:
                logging.error("="*50)
                logging.error("❌ SIN CONEXIÓN A INTERNET")
                logging.error("Verifique la conexión de red de la Raspberry Pi")
                logging.error(f"Intentando reconexión cada {self.server_check_interval} segundos...")
                logging.error("="*50)
            self.server_available = False
            return False

        # Si hay internet, verificar el servidor
        try:
            print("\r", end='')  # Limpiar la línea de la cuenta regresiva
            response = self.session.get(f"{self.api_url}/", timeout=5)
            response.raise_for_status()
            if not self.server_available:
                logging.info("✅ Conexión recuperada con el servidor")
                self.reconnection_attempt = 0
            self.server_available = True
            return True
        except requests.exceptions.ConnectionError:
            self.reconnection_attempt += 1
            if self.server_available:
                logging.error("="*50)
                logging.error("❌ SERVIDOR CAÍDO O INACCESIBLE")
                logging.error("Hay conexión a internet pero el servidor no responde")
                logging.error(f"Intentando reconexión cada {self.server_check_interval} segundos...")
                logging.error("="*50)
            self.server_available = False
            return False
        except requests.exceptions.Timeout:
            self.reconnection_attempt += 1
            if self.server_available:
                logging.error("="*50)
                logging.error("⏰ TIEMPO DE ESPERA AGOTADO")
                logging.error("El servidor está tardando demasiado en responder")
                logging.error(f"Intentando reconexión cada {self.server_check_interval} segundos...")
                logging.error("="*50)
            self.server_available = False
            return False
        except requests.exceptions.RequestException as e:
            self.reconnection_attempt += 1
            if self.server_available:
                logging.error("="*50)
                logging.error("❌ ERROR DE CONEXIÓN")
                logging.error(f"Error: {str(e)}")
                logging.error(f"Intentando reconexión cada {self.server_check_interval} segundos...")
                logging.error("="*50)
            self.server_available = False
            return False

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
        try:
            # Verificar estado del servidor primero
            if not self.server_available:
                has_internet = self.check_internet_connection()
                logging.warning("="*50)
                logging.warning(f"📱 QR leído: {qr_code}")
                if has_internet:
                    logging.warning("✅ Conexión a Internet: OK")
                    logging.warning("❌ Servidor: NO DISPONIBLE")
                else:
                    logging.warning("❌ Sin conexión a Internet")
                logging.warning(f"Próximo intento de conexión en {int(self.server_check_interval - (time.time() - self.last_server_check))} segundos")
                logging.warning("="*50)
                return False

            # Si hay conexión, proceder con el procesamiento normal
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
        logging.error(f"❌ Error de conexión al procesar QR {qr_code}: {e}")
    elif isinstance(e, requests.exceptions.Timeout):
        logging.error(f"⏰ Timeout al procesar QR {qr_code}: {e}")
    elif isinstance(e, requests.exceptions.HTTPError):
        logging.error(f"🌐 Error HTTP al procesar QR {qr_code}: {e}")
    else:
        logging.error(f"❗ Error inesperado al procesar QR {qr_code}: {e}")

def leer_qr_desde_lector_usb():
    """Lee códigos QR desde un lector USB, procesa la información y actualiza la base de datos."""
    
    logging.info("="*50)
    logging.info("Iniciando lector QR")
    logging.info(f"API URL: {Config.API_URL}")
    logging.info(f"Valor mínimo QR: {Config.QR_MIN_VALUE}")
    logging.info("="*50)

    # Crear instancia del lector QR
    reader = QRReader(Config.API_URL, Config.QR_MIN_VALUE)

    while True:
        try:
            # Verificar periódicamente el estado del servidor
            reader.check_server_status()  # Ahora incluye la cuenta regresiva

            # Leer la línea completa enviada por el lector USB
            datos = input()
            datos = datos.strip()

            if not datos:
                continue

            print("\r", end='')  # Limpiar la línea de la cuenta regresiva
            logging.info(f"📱 QR leído: {datos}")

            if reader.process_qr(datos):
                logging.info("✅ QR procesado exitosamente")
            else:
                if not reader.server_available:
                    logging.warning("⚠️ QR no procesado - Servidor no disponible")
                else:
                    logging.warning("⚠️ QR no procesado - Verificar estado y valor")

        except KeyboardInterrupt:
            print("\r", end='')  # Limpiar la línea de la cuenta regresiva
            logging.info("="*50)
            logging.info("🛑 Programa terminado por el usuario")
            logging.info("="*50)
            break
        except Exception as e:
            print("\r", end='')  # Limpiar la línea de la cuenta regresiva
            handle_qr_error(e, datos if 'datos' in locals() else 'unknown')
            time.sleep(1)

if __name__ == "__main__":
    leer_qr_desde_lector_usb()

