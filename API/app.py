from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import config  # Importa la configuración desde config.py
import mysql.connector

mydb = mysql.connector.connect(
  host=config.DB_HOST,
  user=config.DB_USER,
  password=config.DB_PASSWORD,
  database=config.DB_NAME
)
# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
app.config.from_object(config)

# Inicializar SQLAlchemy
db = SQLAlchemy(app)


# Definir una ruta para probar que la API funciona
@app.route('/')
def home():
    return jsonify({'message': 'Hola FullStack!'})

# Endpoint para obtener usuarios
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM dim_usuarios")
    usuarios = mycursor.fetchall()
    return jsonify(usuarios)

# Ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear las tablas si no existen
    app.run(debug=True, host="0.0.0.0", port=5000)  # Ejecutar la aplicación

