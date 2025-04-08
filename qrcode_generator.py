from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import mysql.connector
import random
import string
import logging
import os
import base64
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    check_admin_role,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Pydantic models for request/response validation
class QRCodeBase(BaseModel):
    value: float = Field(..., description="Value of the QR code")
    state: str = Field(..., description="State of the QR code")
    creation_date: datetime = Field(..., description="Creation date of the QR code")
    qr_image: Optional[str] = Field(None, description="Base64 encoded QR image")

class QRCodeCreate(QRCodeBase):
    pass

class QRCode(QRCodeBase):
    qrcode_id: str
    used_date: Optional[datetime] = None

    class Config:
        from_attributes = True  # Updated for Pydantic 2.x

# FastAPI app
app = FastAPI(
    title="QR Code Generator API",
    description="API for generating and managing QR codes for vending machines",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta de autenticación
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Serve index.html at root
@app.get("/")
async def read_root():
    try:
        return FileResponse("static/index.html")
    except Exception as e:
        logging.error(f"Error serving index.html: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error loading the application interface"}
        )

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "waterDB")
}

# Database dependency
def get_db():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
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

def generate_qrcode_id(length: int = int(os.getenv("QR_SHORT_ID_LENGTH", "8"))) -> str:
    """Generate a unique QR code ID."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.post("/api/qrdata", response_model=QRCode)
async def create_qr_data(
    qr_data: QRCodeCreate,
    current_user: dict = Depends(check_admin_role)  # Solo administradores pueden crear QR
):
    """Create a new QR code entry."""
    db = None
    cursor = None
    try:
        # Obtener conexión a la base de datos
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        # Generate unique qrcode_id
        while True:
            qrcode_id = generate_qrcode_id()
            cursor.execute('SELECT 1 FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
            if cursor.fetchone() is None:
                break

        # Convert base64 image to binary if provided
        qr_image_binary = None
        if qr_data.qr_image:
            # Remove the data URL prefix if present
            if ',' in qr_data.qr_image:
                qr_data.qr_image = qr_data.qr_image.split(',')[1]
            try:
                qr_image_binary = base64.b64decode(qr_data.qr_image)
                logging.info(f"QR image decoded successfully, size: {len(qr_image_binary)} bytes")
            except Exception as e:
                logging.error(f"Error decoding QR image: {e}")
                # Continue without the image if there's an error

        # Insert the QR code data with the image
        query = 'INSERT INTO qr_codes (qrcode_id, value, state, creation_date, qr_image) VALUES (%s, %s, %s, %s, %s)'
        values = (qrcode_id, qr_data.value, qr_data.state, qr_data.creation_date, qr_image_binary)
        cursor.execute(query, values)
        db.commit()
        logging.info(f"QR code created with ID: {qrcode_id}")

        # Fetch the created record
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        # Convert binary image back to base64 for response
        qr_image_base64 = None
        if result[5]:  # If qr_image is not None
            qr_image_base64 = base64.b64encode(result[5]).decode('utf-8')
        
        return QRCode(
            qrcode_id=result[0],
            value=float(result[1]),
            state=result[2],
            creation_date=result[3],
            used_date=result[4],
            qr_image=qr_image_base64
        )
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@app.get("/api/qrdata/{qrcode_id}", response_model=QRCode)
async def get_qr_data(
    qrcode_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get QR code information by qrcode_id."""
    db = None
    cursor = None
    try:
        # Obtener conexión a la base de datos
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Código QR no encontrado")
        
        # Convert binary image back to base64 for response
        qr_image_base64 = None
        if result[5]:  # If qr_image is not None
            qr_image_base64 = base64.b64encode(result[5]).decode('utf-8')
            
        return QRCode(
            qrcode_id=result[0],
            value=float(result[1]),
            state=result[2],
            creation_date=result[3],
            used_date=result[4],
            qr_image=qr_image_base64
        )
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@app.get("/api/qrcodes", response_model=List[QRCode])
async def get_all_qrcodes(
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """List all QR codes with pagination."""
    logging.info(f"Obteniendo códigos QR con paginación: skip={skip}, limit={limit}")
    db = None
    cursor = None
    try:
        # Obtener conexión a la base de datos
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SHOW TABLES LIKE 'qr_codes'")
        if not cursor.fetchone():
            logging.error("La tabla 'qr_codes' no existe en la base de datos")
            raise HTTPException(status_code=500, detail="La tabla 'qr_codes' no existe en la base de datos")
        
        # Obtener el total de registros
        cursor.execute('SELECT COUNT(*) FROM qr_codes')
        total_count = cursor.fetchone()[0]
        logging.info(f"Total de códigos QR: {total_count}")
        
        # Obtener los registros con paginación
        cursor.execute('SELECT * FROM qr_codes LIMIT %s OFFSET %s', (limit, skip))
        results = cursor.fetchall()
        logging.info(f"Obtenidos {len(results)} códigos QR")
        
        qr_codes = []
        for row in results:
            try:
                # Convert binary image back to base64 for response
                qr_image_base64 = None
                if row[5]:  # If qr_image is not None
                    qr_image_base64 = base64.b64encode(row[5]).decode('utf-8')
                    
                qr_codes.append(QRCode(
                    qrcode_id=row[0],
                    value=float(row[1]),
                    state=row[2],
                    creation_date=row[3],
                    used_date=row[4],
                    qr_image=qr_image_base64
                ))
            except Exception as e:
                logging.error(f"Error procesando fila {row}: {e}")
                # Continuar con la siguiente fila
                continue
        
        return qr_codes
    except mysql.connector.Error as err:
        logging.error(f"Error de base de datos: {err}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(err)}")
    except Exception as e:
        logging.error(f"Error al obtener códigos QR: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cargar los códigos QR: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@app.put("/api/qrdata/exchange/{qrcode_id}")
async def exchange_qr(qrcode_id: str, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Exchange a QR code."""
    cursor = db.cursor()
    try:
        # Check QR code status and value
        cursor.execute('SELECT state, value FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Código QR no encontrado")
            
        state, value = result
        min_value = float(os.getenv("QR_MIN_VALUE", "0.05"))
        if state == 'valido' and value > min_value:
            # Update QR code
            update_query = 'UPDATE qr_codes SET state = "usado", value = 0, used_date = %s WHERE qrcode_id = %s'
            used_date = datetime.now()
            cursor.execute(update_query, (used_date, qrcode_id))
            db.commit()
            return {"status": "success", "message": "QR code exchanged successfully"}
        else:
            raise HTTPException(status_code=400, detail="QR code cannot be exchanged")
    finally:
        cursor.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "3000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    ) 