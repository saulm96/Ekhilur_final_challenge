from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import config  # Importa la configuración desde config.py

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
app.config.from_object(config)

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Modelo de prueba
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)

# Definir una ruta para probar que la API funciona
@app.route('/')
def home():
    return jsonify({'message': 'Hola FullStack!'})

# Endpoint para obtener usuarios
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([{"id": u.id, "nombre": u.nombre} for u in usuarios])

# Ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    app.run(debug=True, host="0.0.0.0", port=5000)  # Asegurar que corre en 5000


