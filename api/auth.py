from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import mysql.connector
from dotenv import load_dotenv
import logging
from config import Config

# Cargar variables de entorno
load_dotenv()

# Configuración de seguridad
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2 para tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuración de logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    """Obtiene una conexión a la base de datos"""
    connection = None
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos"
        )

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash para la contraseña"""
    return pwd_context.hash(password)

def get_user(username: str):
    """Obtiene un usuario por su nombre de usuario desde la base de datos"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user:
            # Convertir el usuario a un diccionario con los campos necesarios
            return {
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "hashed_password": user["password_hash"],
                "disabled": not user["is_active"],
                "role": user["role"]
            }
        return None
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return None
    finally:
        cursor.close()
        db.close()

def authenticate_user(username: str, password: str):
    """Autentica un usuario con su nombre de usuario y contraseña"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    
    # Actualizar último login
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE users SET last_login = NOW() WHERE username = %s",
            (username,)
        )
        db.commit()
    except mysql.connector.Error as err:
        logging.error(f"Error updating last_login: {err}")
    finally:
        cursor.close()
        db.close()
    
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """Crea un token JWT con los datos proporcionados"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Obtiene el usuario actual a partir del token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Dict = Depends(get_current_user)):
    """Verifica que el usuario actual esté activo"""
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def check_admin_role(current_user: Dict = Depends(get_current_active_user)):
    """Verifica que el usuario tenga rol de administrador"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes para realizar esta acción"
        )
    return current_user 