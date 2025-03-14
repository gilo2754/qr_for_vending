import cv2
import numpy as np
from pyzbar.pyzbar import decode

def leer_qr():
    """Lee códigos QR desde la cámara e imprime el valor en la consola."""

    cap = cv2.VideoCapture(0)  # Abre la cámara (0 es la cámara predeterminada)

    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    while True:
        ret, frame = cap.read()  # Lee un fotograma de la cámara

        if not ret:
            print("No se pudo leer el fotograma.")
            break

        # Decodifica códigos QR en el fotograma
        codigos_qr = decode(frame)

        for codigo in codigos_qr:
            datos = codigo.data.decode('utf-8')  # Decodifica los datos del código QR
            print("Código QR detectado:", datos)

            # Dibuja un rectángulo alrededor del código QR
            puntos = np.array([codigo.polygon], np.int32)
            puntos = puntos.reshape((-1, 1, 2))
            cv2.polylines(frame, [puntos], True, (0, 255, 0), 2)

        # Muestra el fotograma con los códigos QR detectados
        cv2.imshow("Lector de Códigos QR", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Sale del bucle si se presiona 'q'
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    leer_qr()