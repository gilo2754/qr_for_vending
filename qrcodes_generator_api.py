from datetime import datetime
from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
import random
import string
import logging
from config import Config

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Configuración de Logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)

def get_db_connection():
    try:
        connection = mysql.connector.connect(**Config.DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Error al conectar a la base de datos: {err}")
        return None

def generate_short_id(length=Config.QR_SHORT_ID_LENGTH):
    """Genera un ID alfanumérico corto y único."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@app.route('/api/qrdata', methods=['POST'])
def create_qr_data():
    data = request.get_json()
    valor = data.get('valor')
    estado = data.get('estado')
    fecha_creacion = data.get('fecha_creacion')

    # Validación de datos
    if not all([valor, estado, fecha_creacion]):
        logging.warning("Datos incompletos recibidos.")
        return jsonify({'error': 'Datos incompletos'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Error al conectar a la base de datos'}), 500

    cursor = connection.cursor()

    # Genera un ID corto y verifica su unicidad
    while True:
        short_id = generate_short_id()
        cursor.execute('SELECT 1 FROM qr_codes WHERE short_id = %s', (short_id,))
        if cursor.fetchone() is None:
            break  # ID es único, sal del bucle

    query = 'INSERT INTO qr_codes (short_id, value, state, creation_date) VALUES (%s, %s, %s, %s)'
    values = (short_id, valor, estado, fecha_creacion)

    try:
        cursor.execute(query, values)
        connection.commit()
        connection.close()
        logging.info(f"Datos insertados correctamente para short_id: {short_id}")
        return jsonify({'short_id': short_id, 'message': 'Datos insertados correctamente'}), 200
    except mysql.connector.Error as err:
        connection.close()
        logging.error(f"Error al insertar datos: {err}")
        return jsonify({'error': 'Error al insertar datos'}), 500

@app.route('/api/qrdata/<short_id>', methods=['GET'])
def get_qr_data(short_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Error al conectar a la base de datos'}), 500

    cursor = connection.cursor()
    query = 'SELECT * FROM qr_codes WHERE short_id = %s'
    cursor.execute(query, (short_id,))
    result = cursor.fetchone()
    connection.close()

    if result:
        qr_data = {
            'short_id': result[0],
            'valor': float(result[1]),
            'estado': result[2],
            'fecha_creacion': str(result[3]),
            'fecha_usado': str(result[4]) if result[4] else None,
        }
        logging.info(f"Datos obtenidos del QR: {qr_data}")
        return jsonify(qr_data), 200
    else:
        logging.warning(f"Datos no encontrados para short_id: {short_id}")
        return jsonify({'error': 'Datos no encontrados'}), 404

@app.route('/api/qrcodes', methods=['GET'])
def get_all_qr_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Error al conectar a la base de datos'}), 500

    cursor = connection.cursor()
    offset = (page - 1) * per_page
    query = 'SELECT * FROM qr_codes LIMIT %s OFFSET %s'
    cursor.execute(query, (per_page, offset))
    results = cursor.fetchall()
    connection.close()

    qr_codes = []
    for result in results:
        qr_data = {
            'short_id': result[0],
            'valor': float(result[1]),
            'estado': result[2],
            'fecha_creacion': str(result[3]),
            'fecha_usado': str(result[4]) if result[4] else None,
        }
        qr_codes.append(qr_data)
    logging.info(f"Datos de QRs obtenidos. Página: {page}, Registros por página: {per_page}")
    return jsonify(qr_codes), 200

@app.route('/api/qrdata/canjear/<short_id>', methods=['PUT'])
def canjear_qr(short_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Error al conectar a la base de datos'}), 500

    cursor = connection.cursor()

    # Verificar el estado y el valor del QR
    check_query = 'SELECT state, value FROM qr_codes WHERE short_id = %s'
    cursor.execute(check_query, (short_id,))
    result = cursor.fetchone()

    if result:
        estado, valor = result
        if estado == 'valido' and valor > Config.QR_MIN_VALUE:
            # Actualizar el QR
            update_query = 'UPDATE qr_codes SET state = "usado", value = 0, used_date = %s WHERE short_id = %s'
            used_date = datetime.now()
            try:
                cursor.execute(update_query, (used_date, short_id))
                connection.commit()
                connection.close()
                logging.info(f"QR {short_id} canjeado correctamente.")
                return jsonify({'message': f"QR {short_id} canjeado correctamente."}), 200
            except mysql.connector.Error as err:
                connection.close()
                logging.error(f"Error al canjear el QR {short_id}: {err}")
                return jsonify({'error': f"Error al canjear el QR {short_id}: {err}"}), 500
        else:
            connection.close()
            logging.warning(f"QR {short_id} no cumple con los requisitos para ser canjeado.")
            return jsonify({'error': f"QR {short_id} no cumple con los requisitos para ser canjeado."}), 400
    else:
        connection.close()
        logging.warning(f"QR {short_id} no encontrado.")
        return jsonify({'error': f"QR {short_id} no encontrado."}), 404
    
if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        port=Config.API_PORT,
        host=Config.API_HOST
    )