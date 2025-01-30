from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from dotenv import load_dotenv
import os
import time

load_dotenv()

def wait_for_db():
    max_tries = 30
    for i in range(max_tries):
        try:
            mydb = mysql.connector.connect(
                host=os.getenv('DATA_DB_HOST'),
                user=os.getenv('DATA_DB_USER'),
                password=os.getenv('DATA_DB_PASSWORD'),
                database=os.getenv('DATA_DB_DATABASE'),
                port=3306  # Puerto interno de Docker
            )
            print("¡Conexión a la base de datos exitosa!")
            return mydb
        except Exception as e:
            if i < max_tries - 1:  # si no es el último intento
                print(f"Intento {i+1}: No se pudo conectar a la base de datos. Reintentando en 2 segundos...")
                time.sleep(2)
            else:
                print(f"Error final conectando a la base de datos: {str(e)}")
                raise

print("Variables de entorno cargadas:")
print(f"DATA_DB_HOST: {os.getenv('DATA_DB_HOST')}")
print(f"DATA_DB_USER: {os.getenv('DATA_DB_USER')}")
print(f"DATA_DB_DATABASE: {os.getenv('DATA_DB_DATABASE')}")

# Intentar conectar a la base de datos con reintentos
mydb = wait_for_db()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('CORS_ORIGIN', 'http://localhost:5173'),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True
    }
})

# Configuración de SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DATA_DB_USER')}:{os.getenv('DATA_DB_PASSWORD')}@{os.getenv('DATA_DB_HOST')}:3306/{os.getenv('DATA_DB_DATABASE')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def home():
    return jsonify({'message': 'Hola FullStack!'})

@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM dim_usuarios")
    usuarios = mycursor.fetchall()
    return jsonify(usuarios)

# Nuevo endpoint para analizar usuarios sin "Asociacion" ni "ekhilur"
@app.route('/analyze_users', methods=['GET'])
def analyze_users():
    mycursor = mydb.cursor(dictionary=True)
    
    query = """
    WITH CategorizedUsers AS (
        SELECT 
            Id_usuario, 
            Id_fecha_alta, 
            CASE 
                WHEN Tipo_usuario IN ('autonomo', 'Empresa') THEN 'Empresas'
                ELSE Tipo_usuario
            END AS Categoria_Agrupada
        FROM dim_usuarios
        WHERE Tipo_usuario NOT IN ('Asociacion', 'ekhilur')  -- Excluir categorías no deseadas
    ),
    Totals AS (
        SELECT 
            Categoria_Agrupada,
            SUM(CASE WHEN Id_fecha_alta <= '20241130' THEN 1 ELSE 0 END) AS Total_Noviembre_2024,
            SUM(CASE WHEN Id_fecha_alta <= '20241231' THEN 1 ELSE 0 END) AS Total_Diciembre_2024
        FROM CategorizedUsers
        GROUP BY Categoria_Agrupada
    )
    SELECT 
        Categoria_Agrupada AS Categoria,
        Total_Noviembre_2024,
        Total_Diciembre_2024,
        (Total_Diciembre_2024 - Total_Noviembre_2024) AS Incremento_Absoluto,
        CASE 
            WHEN Total_Noviembre_2024 > 0 
            THEN ROUND(((Total_Diciembre_2024 - Total_Noviembre_2024) / Total_Noviembre_2024) * 100, 1)
            ELSE 'N/A'
        END AS Incremento_Porcentual
    FROM Totals;
    """
    
    mycursor.execute(query)
    results = mycursor.fetchall()
    
    return jsonify(results)

# Ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("¡Tablas creadas exitosamente!")
        except Exception as e:
            print(f"Error creando tablas: {str(e)}")
    
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv('DATA_API_APP_PORT', 5000)))