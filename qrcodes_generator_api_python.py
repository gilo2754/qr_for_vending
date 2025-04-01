from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import mysql.connector
import random
import string
import logging
from config import Config

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format=Config.LOG_FORMAT
)

# Pydantic models for request/response validation
class QRCodeBase(BaseModel):
    valor: float = Field(..., description="Value of the QR code")
    estado: str = Field(..., description="State of the QR code")
    fecha_creacion: datetime = Field(..., description="Creation date of the QR code")

class QRCodeCreate(QRCodeBase):
    pass

class QRCode(QRCodeBase):
    short_id: str
    fecha_usado: Optional[datetime] = None

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(
    title="QR Code Generator API",
    description="API for generating and managing QR codes for vending machines",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        yield connection
    finally:
        connection.close()

def generate_short_id(length: int = Config.QR_SHORT_ID_LENGTH) -> str:
    """Generate a unique short ID."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.post("/api/qrdata", response_model=QRCode)
async def create_qr_data(qr_data: QRCodeCreate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Create a new QR code entry."""
    cursor = db.cursor()

    # Generate unique short_id
    while True:
        short_id = generate_short_id()
        cursor.execute('SELECT 1 FROM qr_codes WHERE short_id = %s', (short_id,))
        if cursor.fetchone() is None:
            break

    try:
        query = 'INSERT INTO qr_codes (short_id, value, state, creation_date) VALUES (%s, %s, %s, %s)'
        values = (short_id, qr_data.valor, qr_data.estado, qr_data.fecha_creacion)
        cursor.execute(query, values)
        db.commit()

        # Fetch the created record
        cursor.execute('SELECT * FROM qr_codes WHERE short_id = %s', (short_id,))
        result = cursor.fetchone()
        
        return QRCode(
            short_id=result[0],
            valor=float(result[1]),
            estado=result[2],
            fecha_creacion=result[3],
            fecha_usado=result[4]
        )
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()

@app.get("/api/qrdata/{short_id}", response_model=QRCode)
async def get_qr_data(short_id: str, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Get QR code information by short_id."""
    cursor = db.cursor()
    try:
        cursor.execute('SELECT * FROM qr_codes WHERE short_id = %s', (short_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="QR code not found")
            
        return QRCode(
            short_id=result[0],
            valor=float(result[1]),
            estado=result[2],
            fecha_creacion=result[3],
            fecha_usado=result[4]
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
                short_id=row[0],
                valor=float(row[1]),
                estado=row[2],
                fecha_creacion=row[3],
                fecha_usado=row[4]
            )
            for row in results
        ]
    finally:
        cursor.close()

@app.put("/api/qrdata/canjear/{short_id}")
async def canjear_qr(short_id: str, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """Redeem a QR code."""
    cursor = db.cursor()
    try:
        # Check QR code status and value
        cursor.execute('SELECT state, value FROM qr_codes WHERE short_id = %s', (short_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="QR code not found")
            
        estado, valor = result
        if estado == 'valido' and valor > Config.QR_MIN_VALUE:
            # Update QR code
            update_query = 'UPDATE qr_codes SET state = "usado", value = 0, used_date = %s WHERE short_id = %s'
            used_date = datetime.now()
            cursor.execute(update_query, (used_date, short_id))
            db.commit()
            
            return {"message": f"QR {short_id} successfully redeemed"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"QR {short_id} does not meet the requirements for redemption"
            )
    finally:
        cursor.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level=Config.LOG_LEVEL.lower()
    ) 