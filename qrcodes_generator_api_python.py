from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
import random
import string
import logging
import os

app = Flask(__name__)
CORS(app)

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la base de datos desde variables de entorno
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'gilo'),
    'password': os.environ.get('DB_PASSWORD', 'adminadmin'),
    'database': os.environ.get('DB_NAME', 'waterplus_short_id')
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Error al conectar a la base de datos: {err}")
        return None

def generate_short_id(length=8):
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
    per_page = request.args.get('per_page', 10, type=int)

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
if __name__ == '__main__':
    app.run(debug=True, port=3000)