import sys
import requests
import time

def leer_qr_desde_lector_usb():
    """Lee códigos QR desde un lector USB, procesa la información y actualiza la base de datos."""

    print("Esperando la lectura de códigos QR desde el lector USB...")

    while True:
        try:
            # Leer la línea completa enviada por el lector USB (terminada con Enter)
            datos = input()
            datos = datos.strip()  # Eliminar espacios en blanco al principio y al final

            print("Código QR leído:", datos)

            try:
                # Obtener información del QR
                url_get = f"http://localhost:3000/api/qrdata/{datos}"
                respuesta_get = requests.get(url_get)
                respuesta_get.raise_for_status()
                info_qr = respuesta_get.json()
                print("Información del QR:", info_qr)

                valor_qr = info_qr.get('valor', 0)
                estado_qr = info_qr.get('estado', '')

                if valor_qr >= 0.05 and estado_qr == 'valido':
                    pulsos = int(valor_qr / 0.05)
                    print(f"Generando {pulsos} pulsos para el QR {datos}")

                    # Actualizar el estado y el valor del QR
                    url_put = f"http://localhost:3000/api/qrdata/canjear/{datos}"
                    respuesta_put = requests.put(url_put)
                    respuesta_put.raise_for_status()
                    print(f"QR {datos} actualizado a 'usado' y valor a 0")
                else:
                    if valor_qr < 0.05:
                        print(f"El valor del QR {datos} es menor a 0.05. No se generan pulsos.")
                    elif estado_qr != 'valido':
                        print(f"El estado del QR {datos} no es 'valido'. No se generan pulsos.")
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

