from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import mysql.connector
import random
import string
import logging
import os
from dotenv import load_dotenv

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
async def create_qr_data(qr_data: QRCodeCreate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Create a new QR code entry."""
    cursor = db.cursor()

    # Generate unique qrcode_id
    while True:
        qrcode_id = generate_qrcode_id()
        cursor.execute('SELECT 1 FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        if cursor.fetchone() is None:
            break

    try:
        query = 'INSERT INTO qr_codes (qrcode_id, value, state, creation_date) VALUES (%s, %s, %s, %s)'
        values = (qrcode_id, qr_data.value, qr_data.state, qr_data.creation_date)
        cursor.execute(query, values)
        db.commit()

        # Fetch the created record
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        return QRCode(
            qrcode_id=result[0],
            value=float(result[1]),
            state=result[2],
            creation_date=result[3],
            used_date=result[4]
        )
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    finally:
        cursor.close()

@app.get("/api/qrdata/{qrcode_id}", response_model=QRCode)
async def get_qr_data(qrcode_id: str, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Get QR code information by qrcode_id."""
    cursor = db.cursor()
    try:
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Código QR no encontrado")
            
        return QRCode(
            qrcode_id=result[0],
            value=float(result[1]),
            state=result[2],
            creation_date=result[3],
            used_date=result[4]
        )
    finally:
        cursor.close()

@app.get("/api/qrcodes", response_model=List[QRCode])
async def get_all_qr_data(
    skip: int = 0,
    limit: int = 20,
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    """List all QR codes with pagination."""
    cursor = db.cursor()
    try:
        cursor.execute('SELECT * FROM qr_codes LIMIT %s OFFSET %s', (limit, skip))
        results = cursor.fetchall()
        
        return [
            QRCode(
                qrcode_id=row[0],
                value=float(row[1]),
                state=row[2],
                creation_date=row[3],
                used_date=row[4]
            )
            for row in results
        ]
    finally:
        cursor.close()

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
            
            return {"message": f"Código QR {qrcode_id} canjeado exitosamente"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"El código QR {qrcode_id} no cumple con los requisitos para ser canjeado"
            )
    finally:
        cursor.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "3000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    ) 