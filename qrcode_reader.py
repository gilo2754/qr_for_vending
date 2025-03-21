import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests

def leer_qr():
    """Lee códigos QR desde la cámara con mejoras en el procesamiento de imagen."""

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            print("No se pudo leer el fotograma.")
            break

        # Decodifica códigos QR
        codigos_qr = decode(frame)

        for codigo in codigos_qr:
            datos = codigo.data.decode('utf-8')
            print("Código QR detectado:", datos)

            try:
                url_api = f"http://localhost:3000/api/qrdata/{datos}"
                respuesta = requests.get(url_api)
                respuesta.raise_for_status()
                info_qr = respuesta.json()
                print("Información de la API:", info_qr)
            except requests.exceptions.RequestException as e:
                print(f"Error al obtener información de la API: {e}")

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