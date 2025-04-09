import logging
import os
from config import Config

# Configurar el logging una sola vez para toda la aplicación
logging.basicConfig(
    level=Config.LOG_LEVEL.upper(),
    format=Config.LOG_FORMAT
)

# Configurar el logger para la aplicación
logger = logging.getLogger("qr_app")
logger.setLevel(Config.LOG_LEVEL.upper())

# Evitar que los mensajes se propaguen al logger raíz
logger.propagate = False

# Añadir un manejador si no tiene ninguno
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    logger.addHandler(handler)

def setup_logging():
    """
    Configura el logging para toda la aplicación.
    Esta función centraliza la configuración de logging.
    """
    return logger

# Crear una instancia del logger
logger = setup_logging() 