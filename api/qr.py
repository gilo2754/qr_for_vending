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
    new_value: float = Field(..., description="Current value of the QR code")
    old_value: float = Field(0.0, description="Previous value of the QR code before being used/expired")
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

    @validator('new_value', 'old_value')
    def validate_values(cls, v):
        if v < 0:
            raise ValueError("Los valores del código QR no pueden ser negativos")
        return v

class QRCodeCreate(BaseModel):
    new_value: float = Field(..., description="Initial value of the QR code")
    old_value: float = Field(0.0, description="Previous value of the QR code (usually 0 for new codes)")
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

    @validator('new_value', 'old_value')
    def validate_values(cls, v):
        if v < 0:
            raise ValueError("Los valores del código QR no pueden ser negativos")
        return v

class QRCode(QRCodeBase):
    qrcode_id: str
    used_date: Optional[datetime] = None

    class Config:
        from_attributes = True

def generate_qrcode_id(length: int = int(os.getenv("QR_SHORT_ID_LENGTH", "8"))) -> str:
    """Generate a unique QR code ID."""
    # Excluir las letras Y y Z (mayúsculas y minúsculas) para evitar problemas de layout de teclado
    characters = string.ascii_letters.replace('y', '').replace('z', '').replace('Y', '').replace('Z', '') + string.digits
    return ''.join(random.choices(characters, k=length))

@router.post("/qrdata", response_model=QRCode)
async def create_qr_data(
    qr_data: QRCodeCreate,
    current_user: dict = Depends(check_admin_role)
):
    """
    Crea un nuevo código QR.
    
    Requiere autenticación de administrador.
    - Endpoint: POST /api/qrdata
    - Auth: Sí (admin)
    - Request: QRCodeCreate (valor, estado, fecha_creacion, imagen_opcional)
    - Response: QRCode
    """
    if qr_data.new_value <= 0:
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
        query = 'INSERT INTO qr_codes (qrcode_id, new_value, old_value, state, creation_date, qr_image) VALUES (%s, %s, %s, %s, %s, %s)'
        values = (qrcode_id, qr_data.new_value, qr_data.old_value, qr_data.state, qr_data.creation_date, qr_image_binary)
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
            new_value=float(result[1]),
            old_value=float(result[2]),
            state=result[3],
            creation_date=result[4],
            used_date=result[5],
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

@router.get("/qrdata/{qrcode_id}")
async def get_qr_data(
    qrcode_id: str,
    fields: str = None
):
    """
    Obtiene la información de un código QR por su ID.
    
    Endpoint público para consultar el estado y valor de un QR.
    - Endpoint: GET /api/qrdata/{qrcode_id}
    - Auth: No
    - Params: 
        - qrcode_id: ID del código QR
        - fields: Campos a devolver (separados por comas). Ej: "value,state"
    - Response: QRCode (campos solicitados)
    """
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = db.cursor()
        
        # Si se especifican campos, solo seleccionamos esos
        if fields:
            requested_fields = fields.split(',')
            valid_fields = {'qrcode_id', 'new_value', 'old_value', 'state', 'creation_date', 'used_date', 'qr_image'}
            # Validar que los campos solicitados sean válidos
            if not all(field in valid_fields for field in requested_fields):
                raise HTTPException(
                    status_code=400,
                    detail="Campos inválidos. Los campos válidos son: qrcode_id, new_value, old_value, state, creation_date, used_date, qr_image"
                )
            # Siempre incluir qrcode_id
            if 'qrcode_id' not in requested_fields:
                requested_fields.append('qrcode_id')
            # Construir la consulta SQL
            fields_sql = ', '.join(requested_fields)
            cursor.execute(f'SELECT {fields_sql} FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        else:
            cursor.execute('SELECT * FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Código QR no encontrado")
        
        # Construir la respuesta con los campos solicitados
        response = {}
        if fields:
            for i, field in enumerate(requested_fields):
                if field == 'qr_image' and result[i] is not None:
                    response[field] = base64.b64encode(result[i]).decode('utf-8')
                elif field == 'new_value':
                    response[field] = float(result[i])
                elif field == 'old_value':
                    response[field] = float(result[i])
                else:
                    response[field] = result[i]
        else:
            # Si no se especifican campos, devolver todo
            response = {
                'qrcode_id': result[0],
                'new_value': float(result[1]),
                'old_value': float(result[2]),
                'state': result[3],
                'creation_date': result[4],
                'used_date': result[5],
                'qr_image': base64.b64encode(result[6]).decode('utf-8') if result[6] else None
            }
        
        return response
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
    """
    Lista todos los códigos QR con paginación.
    
    Requiere autenticación de usuario.
    - Endpoint: GET /api/qrcodes
    - Auth: Sí (usuario)
    - Params: skip (offset), limit (cantidad)
    - Response: List[QRCode]
    """
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
            if row[6]:  # If qr_image is not None
                qr_image_base64 = base64.b64encode(row[6]).decode('utf-8')
                
            qr_codes.append(QRCode(
                qrcode_id=row[0],
                new_value=float(row[1]),
                old_value=float(row[2]),
                state=row[3],
                creation_date=row[4],
                used_date=row[5],
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
    """
    Canjea un código QR.
    
    Endpoint público para máquinas expendedoras.
    - Endpoint: PUT /api/qrdata/exchange/{qrcode_id}
    - Auth: No
    - Params: qrcode_id
    - Response: {"status": "success", "message": string, "new_value": float, "old_value": float} | HTTPException
    - Estados posibles: 
      * 200: Canjeado exitosamente
      * 400: No se puede canjear (inválido/usado)
      * 404: No encontrado
      * 500: Error de base de datos
    """
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = db.cursor()
        
        # Check QR code status and new_value
        cursor.execute('SELECT state, new_value FROM qr_codes WHERE qrcode_id = %s', (qrcode_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Código QR no encontrado")
            
        state, new_value = result
        min_value = float(os.getenv("QR_MIN_VALUE", "0.05"))
        
        if state == 'valido' and new_value > min_value:
            # Update QR code: move new_value to old_value and set new_value to 0
            update_query = '''
                UPDATE qr_codes 
                SET state = "usado", 
                    old_value = new_value,
                    new_value = 0, 
                    used_date = %s 
                WHERE qrcode_id = %s
            '''
            used_date = datetime.now()
            cursor.execute(update_query, (used_date, qrcode_id))
            db.commit()
            
            return {
                "status": "success", 
                "message": "QR code exchanged successfully",
                "new_value": 0,
                "old_value": new_value
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"QR code cannot be exchanged (state: {state}, new_value: {new_value})"
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

@router.put("/qrdata/{qrcode_id}", response_model=QRCode)
async def update_qr_data(
    qrcode_id: str,
    qr_data: QRCodeBase,
    current_user: dict = Depends(check_admin_role)
):
    """
    Actualiza la información de un código QR.
    
    Requiere autenticación de administrador.
    - Endpoint: PUT /api/qrdata/{qrcode_id}
    - Auth: Sí (admin)
    - Params: qrcode_id
    - Request: QRCodeBase
    - Response: QRCode
    """
    if qr_data.new_value <= 0:
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
        query = 'UPDATE qr_codes SET new_value = %s, old_value = %s, state = %s, creation_date = %s, qr_image = %s WHERE qrcode_id = %s'
        values = (qr_data.new_value, qr_data.old_value, qr_data.state, qr_data.creation_date, qr_image_binary, qrcode_id)
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
        if result[6]:  # If qr_image is not None
            qr_image_base64 = base64.b64encode(result[6]).decode('utf-8')
        
        return QRCode(
            qrcode_id=result[0],
            new_value=float(result[1]),
            old_value=float(result[2]),
            state=result[3],
            creation_date=result[4],
            used_date=result[5],
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