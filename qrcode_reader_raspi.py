import sys
import requests
import time
import os
from dotenv import load_dotenv
import RPi.GPIO as GPIO

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración del lector QR"""
    API_URL = os.getenv('API_URL', 'http://localhost:3000')
    QR_MIN_VALUE = float(os.getenv('QR_MIN_VALUE', '0.05'))
    LED_PIN = 18  # Pin GPIO para el LED externo
    PULSE_DURATION = 0.2  # Duración de cada pulso en segundos
    PULSE_INTERVAL = 0.3  # Intervalo entre pulsos en segundos

def setup_led():
    """Configura el pin del LED"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Config.LED_PIN, GPIO.OUT)
        GPIO.output(Config.LED_PIN, GPIO.LOW)
        print(f"LED configurado en el pin GPIO {Config.LED_PIN}")
    except Exception as e:
        print(f"Error al configurar el LED: {e}")
        print("Asegúrate de ejecutar el script con privilegios de superusuario (sudo)")
        sys.exit(1)

def pulse_led(times):
    """Genera pulsos visuales en el LED"""
    try:
        for _ in range(times):
            GPIO.output(Config.LED_PIN, GPIO.HIGH)
            time.sleep(Config.PULSE_DURATION)
            GPIO.output(Config.LED_PIN, GPIO.LOW)
            time.sleep(Config.PULSE_INTERVAL)
    except Exception as e:
        print(f"Error al generar pulsos en el LED: {e}")

def leer_qr_desde_lector_usb():
    """Lee códigos QR desde un lector USB, procesa la información y actualiza la base de datos."""

    print(f"Esperando la lectura de códigos QR desde el lector USB...")
    print(f"API URL: {Config.API_URL}")
    print(f"Valor mínimo QR: {Config.QR_MIN_VALUE}")

    # Configurar el LED
    setup_led()

    while True:
        try:
            # Leer la línea completa enviada por el lector USB (terminada con Enter)
            datos = input()
            datos = datos.strip()  # Eliminar espacios en blanco al principio y al final

            print("Código QR leído:", datos)

            try:
                # Obtener información del QR (new_value, old_value y state)
                url_get_info_qr = f"{Config.API_URL}/api/qrdata/{datos}?fields=new_value,old_value,state"
                respuesta_get = requests.get(url_get_info_qr)
                respuesta_get.raise_for_status()
                info_qr = respuesta_get.json()
                print("Información del QR:", info_qr)

                new_value = info_qr.get('new_value', 0)
                old_value = info_qr.get('old_value', 0)
                estado_qr = info_qr.get('state', '')

                # Usar new_value para determinar los pulsos
                if new_value >= Config.QR_MIN_VALUE and estado_qr == 'valido':
                    pulsos = int(new_value / Config.QR_MIN_VALUE)
                    print(f"Generando {pulsos} pulsos para el QR {datos}")
                    print(f"Valor anterior: {old_value}, Nuevo valor: {new_value}")

                    # Generar pulsos visuales en el LED
                    pulse_led(pulsos)

                    # Actualizar el estado y el valor del QR
                    url_exchange_qr = f"{Config.API_URL}/api/qrdata/exchange/{datos}"
                    respuesta_put = requests.put(url_exchange_qr)
                    respuesta_put.raise_for_status()
                    print(f"QR {datos} actualizado a 'usado' y valor a 0")
                else:
                    if new_value < Config.QR_MIN_VALUE:
                        print(f"El valor del QR {datos} es menor a {Config.QR_MIN_VALUE}. No se generan pulsos.")
                    elif estado_qr != 'valido':
                        print(f"El estado del QR {datos} no es 'valido'. No se generan pulsos.")
                    else:
                        print(f"El QR {datos} no cumple con los requisitos para generar pulsos.")

            except requests.exceptions.RequestException as e:
                print(f"Error al procesar el QR: {e}")

        except KeyboardInterrupt:
            print("Programa terminado por el usuario.")
            GPIO.cleanup()  # Limpiar configuración GPIO al salir
            break
        except Exception as e:
            print(f"Error al leer desde el lector USB: {e}")
            time.sleep(1)

if __name__ == "__main__":
    leer_qr_desde_lector_usb()

