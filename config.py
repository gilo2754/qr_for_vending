import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Configuration
    API_URL = os.getenv('API_URL', 'http://localhost:3000')
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '3000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Database Configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

    # QR Code Configuration
    QR_MIN_VALUE = float(os.getenv('QR_MIN_VALUE', '0.05'))
    QR_SHORT_ID_LENGTH = int(os.getenv('QR_SHORT_ID_LENGTH', '8'))

    # Security Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '100'))
    RATE_LIMIT_PERIOD = timedelta(minutes=int(os.getenv('RATE_LIMIT_PERIOD', '1')))
    SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_muy_segura_cambiar_en_produccion")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    