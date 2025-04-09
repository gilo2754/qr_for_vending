from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
import mysql.connector
import random
import string
import logging
import os
import base64
from config import Config
from api.auth import check_admin_role, get_current_active_user
from api.utils import get_db
from api.logger import logger

# Crear router
router = APIRouter()

# Pydantic models for request/response validation
class QRCodeBase(BaseModel):
    value: float = Field(..., description="Value of the QR code")
    state: str = Field(..., description="State of the QR code")
    creation_date: datetime = Field(..., description="Creation date of the QR code")
    qr_image: Optional[str] = Field(None, description="Base64 encoded QR image")

    @validator('creation_date', pre=True)
    def parse_creation_date(cls, v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        return v

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError("El valor del código QR no puede ser negativo")
        return v

class QRCodeCreate(BaseModel):
    value: float = Field(..., description="Value of the QR code")
    state: str = Field(..., description="State of the QR code")
    creation_date: datetime = Field(..., description="Creation date of the QR code")
    qr_image: Optional[str] = Field(None, description="Base64 encoded QR image")

    @validator('creation_date', pre=True)
    def parse_creation_date(cls, v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        return v

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError("El valor del código QR no puede ser negativo")
        return v

class QRCode(QRCodeBase):
    qrcode_id: str
    used_date: Optional[datetime] = None

    class Config:
        from_attributes = True

def generate_qrcode_id(length: int = int(os.getenv("QR_SHORT_ID_LENGTH", "8"))) -> str:
    """Generate a unique QR code ID."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@router.post("/qrdata", response_model=QRCode)
async def create_qr_data(
    qr_data: QRCodeCreate,
    current_user: dict = Depends(check_admin_role)
):
    """Create a new QR code entry."""
    if qr_data.value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El valor del código QR debe ser mayor que 0"
        )

    # Convert both to naive datetimes for comparison
    now = datetime.now().replace(tzinfo=None)
    creation_date = qr_data.creation_date.replace(tzinfo=None)
    
    if creation_date > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de creación no puede ser futura"
        )

    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
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
            if ',' in qr_data.qr_image:
                qr_data.qr_image = qr_data.qr_image.split(',')[1]
            try:
                qr_image_binary = base64.b64decode(qr_data.qr_image)
            except Exception as e:
                logger.error(f"Error decoding QR image: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al decodificar la imagen QR"
                )

        # Insert the QR code data
        query = 'INSERT INTO qr_codes (qrcode_id, value, state, creation_date, qr_image) VALUES (%s, %s, %s, %s, %s)'
        values = (qrcode_id, qr_data.value, qr_data.state, qr_data.creation_date, qr_image_binary)
        cursor.execute(query, values)
        db.commit()

        # Fetch the created record
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recuperar el código QR creado"
            )
        
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
        logger.error(f"Database error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@router.get("/qrdata/{qrcode_id}", response_model=QRCode)
async def get_qr_data(
    qrcode_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get QR code information by qrcode_id."""
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
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
        logger.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@router.get("/qrcodes", response_model=List[QRCode])
async def get_all_qrcodes(
    current_user: dict = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """List all QR codes with pagination."""
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM qr_codes LIMIT %s OFFSET %s', (limit, skip))
        results = cursor.fetchall()
        
        qr_codes = []
        for row in results:
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
        
        return qr_codes
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@router.put("/qrdata/exchange/{qrcode_id}")
async def exchange_qr(qrcode_id: str):
    """Exchange a QR code. This endpoint is public and does not require authentication."""
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = db.cursor()
        
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
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@router.put("/qrdata/{qrcode_id}", response_model=QRCode)
async def update_qr_data(
    qrcode_id: str,
    qr_data: QRCodeBase,
    current_user: dict = Depends(check_admin_role)
):
    """Update QR code information."""
    if qr_data.value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El valor del código QR debe ser mayor que 0"
        )

    # Convert both to naive datetimes for comparison
    now = datetime.now().replace(tzinfo=None)
    creation_date = qr_data.creation_date.replace(tzinfo=None)
    
    if creation_date > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de creación no puede ser futura"
        )

    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = db.cursor()

        # Check if QR code exists
        cursor.execute('SELECT 1 FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código QR no encontrado"
            )

        # Convert base64 image to binary if provided
        qr_image_binary = None
        if qr_data.qr_image:
            if ',' in qr_data.qr_image:
                qr_data.qr_image = qr_data.qr_image.split(',')[1]
            try:
                qr_image_binary = base64.b64decode(qr_data.qr_image)
            except Exception as e:
                logger.error(f"Error decoding QR image: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al decodificar la imagen QR"
                )

        # Update the QR code data
        query = 'UPDATE qr_codes SET value = %s, state = %s, creation_date = %s, qr_image = %s WHERE qrcode_id = %s'
        values = (qr_data.value, qr_data.state, qr_data.creation_date, qr_image_binary, qrcode_id)
        cursor.execute(query, values)
        db.commit()

        # Fetch the updated record
        cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al recuperar el código QR actualizado"
            )
        
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
        logger.error(f"Database error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close() 