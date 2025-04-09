import mysql.connector
import logging
from fastapi import HTTPException
from config import Config

def get_db():
    """
    Obtiene una conexión a la base de datos.
    Esta función centraliza la lógica de conexión a la base de datos.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos. Por favor, verifique que el servidor MySQL esté ejecutándose."
        )

def get_db_dependency():
    """
    Función para usar como dependencia en FastAPI.
    Retorna un generador que cierra la conexión automáticamente.
    """
    connection = None
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        yield connection
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos. Por favor, verifique que el servidor MySQL esté ejecutándose."
        )
    finally:
        if connection and connection.is_connected():
            connection.close() 