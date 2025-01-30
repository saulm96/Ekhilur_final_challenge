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
        db.create_all()  # Crear las tablas si no existen
    app.run(debug=True, host="0.0.0.0", port=5000)  # Ejecutar la aplicación

