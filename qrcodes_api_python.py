from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'xx',
    'password': 'xx',
    'database': 'xx'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: '{err}'")
        return None

@app.route('/api/qrdata', methods=['POST'])
def create_qr_data():
    data = request.get_json()
    uuid = data.get('uuid')
    valor = data.get('valor')
    estado = data.get('estado')
    fecha_creacion = data.get('fecha_creacion')

    connection = get_db_connection()
    if not connection:
        return 'Error connecting to database', 500

    cursor = connection.cursor()
    # Nombres de columna corregidos para coincidir con la tabla
    query = 'INSERT INTO qr_codes (UUID, value, state, creation_date) VALUES (%s, %s, %s, %s)'
    values = (uuid, valor, estado, fecha_creacion)

    try:
        cursor.execute(query, values)
        connection.commit()
        connection.close()
        return 'Data inserted successfully', 200
    except mysql.connector.Error as err:
        connection.close()
        print(f"Error: '{err}'")
        return 'Error inserting data', 500

@app.route('/api/qrdata/<uuid>', methods=['GET'])
def get_qr_data(uuid):
    connection = get_db_connection()
    if not connection:
        return 'Error connecting to database', 500

    cursor = connection.cursor()
    # Nombre de columna corregido para coincidir con la tabla
    query = 'SELECT * FROM qr_codes WHERE UUID = %s'
    cursor.execute(query, (uuid,))
    result = cursor.fetchone()
    connection.close()

    if result:
        qr_data = {
            'uuid': result[0],
            'valor': float(result[1]),
            'estado': result[2],
            'fecha_creacion': str(result[3])
        }
        return jsonify(qr_data), 200
    else:
        return 'Data not found', 404

if __name__ == '__main__':
    app.run(debug=True, port=3000)