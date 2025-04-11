import sys
import requests
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración del lector QR"""
    API_URL = os.getenv('API_URL', 'http://localhost:3000')
    QR_MIN_VALUE = float(os.getenv('QR_MIN_VALUE', '0.05'))

def leer_qr_desde_lector_usb():
    """Lee códigos QR desde un lector USB, procesa la información y actualiza la base de datos."""

    print(f"Esperando la lectura de códigos QR desde el lector USB...")
    print(f"API URL: {Config.API_URL}")
    print(f"Valor mínimo QR: {Config.QR_MIN_VALUE}")

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
                    print(f"Se generarían {pulsos} pulsos para el QR {datos}")
                    print(f"Valor anterior: {old_value}, Nuevo valor: {new_value}")

                    # Actualizar el estado y el valor del QR
                    url_exchange_qr = f"{Config.API_URL}/api/qrdata/exchange/{datos}"
                    respuesta_put = requests.put(url_exchange_qr)
                    respuesta_put.raise_for_status()
                    print(f"QR {datos} actualizado a 'usado' y valor a 0")
                else:
                    if new_value < Config.QR_MIN_VALUE:
                        print(f"El valor del QR {datos} es menor a {Config.QR_MIN_VALUE}. No se generarían pulsos.")
                    elif estado_qr != 'valido':
                        print(f"El estado del QR {datos} no es 'valido'. No se generarían pulsos.")
                    else:
                        print(f"El QR {datos} no cumple con los requisitos para generar pulsos.")

            except requests.exceptions.RequestException as e:
                print(f"Error al procesar el QR: {e}")

        except KeyboardInterrupt:
            print("Programa terminado por el usuario.")
            break
        except Exception as e:
            print(f"Error al leer desde el lector USB: {e}")
            time.sleep(1)

if __name__ == "__main__":
    leer_qr_desde_lector_usb()

