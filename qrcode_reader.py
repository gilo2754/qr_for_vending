import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests

def leer_qr():
    """Lee códigos QR, procesa la información y actualiza la base de datos."""

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            print("No se pudo leer el fotograma.")
            break

        codigos_qr = decode(frame)

        for codigo in codigos_qr:
            datos = codigo.data.decode('utf-8')
            print("Código QR detectado:", datos)

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

            puntos = np.array([codigo.polygon], np.int32)
            puntos = puntos.reshape((-1, 1, 2))
            cv2.polylines(frame, [puntos], True, (0, 255, 0), 2)

        cv2.imshow("Lector de Códigos QR", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    leer_qr()