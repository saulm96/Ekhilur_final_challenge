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

# Nuevos 5 endpoint para landingpage "ekhilur"
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

@app.route('/analyze_monthly_average_simple', methods=['GET'])
def analyze_monthly_average_simple():
    mycursor = mydb.cursor(dictionary=True)

    query = """
    WITH UsuariosFiltrados AS (
        SELECT Id_usuario 
        FROM dim_usuarios 
        WHERE Tipo_usuario = 'usuario'
    ),
    Fechas2024 AS (
        SELECT Id_fecha, Mes 
        FROM dim_fecha 
        WHERE Ano = 2024
    ),
    Operaciones2024 AS (
        SELECT 
            f.Usuario_emisor, 
            f.Id_fecha, 
            f.Cantidad, 
            d.Mes
        FROM fact_table f
        INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
        WHERE f.Id_tipo_operacion IN (1, 7)
        AND f.Usuario_emisor IN (SELECT Id_usuario FROM UsuariosFiltrados)
    ),
    GastoMensual AS (
        SELECT Usuario_emisor, Mes, ROUND(SUM(Cantidad), 2) AS GastoMensual
        FROM Operaciones2024
        GROUP BY Usuario_emisor, Mes
    ),
    GastoMedioPorUsuario AS (
        SELECT Usuario_emisor, AVG(GastoMensual) AS GastoMedioMensual
        FROM GastoMensual
        GROUP BY Usuario_emisor
    )
    SELECT ROUND(AVG(GastoMedioMensual), 2) AS `Gasto medio mensual por usuario`
    FROM GastoMedioPorUsuario;
    """

    mycursor.execute(query)
    result = mycursor.fetchone()

    return jsonify(result)

@app.route('/analyze_monthly_savings', methods=['GET'])
def analyze_monthly_savings():
    mycursor = mydb.cursor(dictionary=True)

    query = """
    WITH UsuariosFiltrados AS (
        SELECT Id_usuario 
        FROM dim_usuarios 
        WHERE Tipo_usuario = 'usuario'
    ),
    Fechas2024 AS (
        SELECT Id_fecha, Mes 
        FROM dim_fecha 
        WHERE Ano = 2024
    ),
    Operaciones2024 AS (
        SELECT 
            f.Usuario_receptor, 
            f.Id_fecha, 
            f.Cantidad, 
            d.Mes
        FROM fact_table f
        INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
        WHERE f.Id_tipo_operacion IN (0, 4)
        AND f.Usuario_receptor IN (SELECT Id_usuario FROM UsuariosFiltrados)
    ),
    AhorroMensual AS (
        SELECT Usuario_receptor, Mes, ROUND(SUM(Cantidad), 2) AS AhorroMensual
        FROM Operaciones2024
        GROUP BY Usuario_receptor, Mes
    ),
    AhorroMedioPorUsuario AS (
        SELECT Usuario_receptor, AVG(AhorroMensual) AS AhorroMedioMensual
        FROM AhorroMensual
        GROUP BY Usuario_receptor
    )
    SELECT ROUND(AVG(AhorroMedioMensual), 2) AS `Ahorro medio mensual por usuario`
    FROM AhorroMedioPorUsuario;
    """

    mycursor.execute(query)
    result = mycursor.fetchone()

    return jsonify(result)

@app.route('/analyze_total_simple', methods=['GET'])
def analyze_total_simple():
    mycursor = mydb.cursor(dictionary=True)

    query = """
    WITH UltimoMes AS (
        SELECT Id_fecha 
        FROM dim_fecha 
        WHERE Ano = 2024 AND Mes = 12
    )
    SELECT 
        FORMAT(COUNT(*), 0) AS `Número total de operaciones`, 
        FORMAT(SUM(Cantidad), 2) AS `Importe total (€)`
    FROM fact_table
    WHERE Id_tipo_operacion IN (1, 7)
    AND Id_fecha IN (SELECT Id_fecha FROM UltimoMes);
    """

    mycursor.execute(query)
    result = mycursor.fetchone()

    return jsonify(result)

@app.route('/analyze_cash_flow', methods=['GET'])
def analyze_cash_flow():
    mycursor = mydb.cursor(dictionary=True)

    query = """
    WITH Fechas2024 AS (
    SELECT Id_fecha, Mes 
    FROM dim_fecha 
    WHERE Ano = 2024
),
Operaciones2024 AS (
    SELECT 
        f.Id_fecha, 
        f.Id_tipo_operacion, 
        f.Cantidad, 
        d.Mes
    FROM fact_table f
    INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
    WHERE f.Id_tipo_operacion IN (2, 6, 12)
),
Entradas AS (
    SELECT Mes, ROUND(SUM(Cantidad), 2) AS Entradas
    FROM Operaciones2024
    WHERE Id_tipo_operacion = 6
    GROUP BY Mes
),
Salidas AS (
    SELECT Mes, ROUND(SUM(Cantidad), 2) AS Salidas
    FROM Operaciones2024
    WHERE Id_tipo_operacion IN (2, 12)
    GROUP BY Mes
)
SELECT 
    CAST(COALESCE(e.Mes, s.Mes) AS UNSIGNED) AS Mes,
    FORMAT(COALESCE(e.Entradas, 0), 2) AS `Entradas (€)`,
    FORMAT(COALESCE(s.Salidas, 0), 2) AS `Salidas (€)`
FROM Entradas e
LEFT JOIN Salidas s ON e.Mes = s.Mes
UNION DISTINCT
SELECT 
    CAST(COALESCE(e.Mes, s.Mes) AS UNSIGNED) AS Mes,
    FORMAT(COALESCE(e.Entradas, 0), 2) AS `Entradas (€)`,
    FORMAT(COALESCE(s.Salidas, 0), 2) AS `Salidas (€)`
FROM Salidas s
LEFT JOIN Entradas e ON s.Mes = e.Mes
ORDER BY Mes;
    """

    mycursor.execute(query)
    monthly_results = mycursor.fetchall()

    totals_query = """
    WITH Fechas2024 AS (
        SELECT Id_fecha 
        FROM dim_fecha 
        WHERE Ano = 2024
    ),
    Operaciones2024 AS (
        SELECT 
            f.Id_tipo_operacion, 
            f.Cantidad
        FROM fact_table f
        INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
        WHERE f.Id_tipo_operacion IN (2, 6, 12)
    ),
    TotalEntradas AS (
        SELECT ROUND(SUM(Cantidad), 2) AS Total_Entradas
        FROM Operaciones2024
        WHERE Id_tipo_operacion = 6
    ),
    TotalSalidas AS (
        SELECT ROUND(SUM(Cantidad), 2) AS Total_Salidas
        FROM Operaciones2024
        WHERE Id_tipo_operacion IN (2, 12)
    )
    SELECT 
        FORMAT(Total_Entradas, 2) AS `Total Entradas (€)`,
        FORMAT(Total_Salidas, 2) AS `Total Salidas (€)`,
        FORMAT(Total_Entradas - Total_Salidas, 2) AS `Balance Neto (€)`
    FROM TotalEntradas, TotalSalidas;
    """

    mycursor.execute(totals_query)
    totals_result = mycursor.fetchone()

    response = {
        "Flujo de dinero mensual 2024": monthly_results,
        "Totales anuales": totals_result
    }

    return jsonify(response)
# fin Nuevos 5 endpoint para landingpage "ekhilur"

#Nueva endpoint 1 - Gráfico de barras por cantidad de usuarios y grupo de edad
@app.route('/cantidad-usuarios-grupo-edad', methods=['GET'])
def cantidad_usuarios_grupo_edad():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            CASE
                WHEN Edad BETWEEN 18 AND 25 THEN '18-25'
                WHEN Edad BETWEEN 26 AND 35 THEN '26-35'
                WHEN Edad BETWEEN 36 AND 45 THEN '36-45'
                WHEN Edad BETWEEN 46 AND 55 THEN '46-55'
                WHEN Edad BETWEEN 56 AND 65 THEN '56-65'
                WHEN Edad > 65 THEN '65+'
                ELSE 'Desconocido'
            END AS Grupo_edad,
            COUNT(*) AS cantidad_usuarios
        FROM dim_usuarios
        WHERE Edad IS NOT NULL
        GROUP BY Grupo_edad
        ORDER BY Grupo_edad
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

#Nueva endpoint 2 - Evolución del número de altas por mes
@app.route('/evolucion-altas-mes', methods=['GET'])
def evolucion_altas_mes():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            F.Ano,
            F.Mes,
            COUNT(DISTINCT Id_usuario) AS total_usuarios
        FROM dim_usuarios
        LEFT JOIN dim_fecha AS F ON dim_usuarios.Id_fecha_alta = F.Id_fecha
        WHERE Tipo_usuario = 'usuario'
        GROUP BY F.Ano, F.Mes
        ORDER BY F.Ano, F.Mes
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Nueva endpoint 3: Patrones G1 - Pie chart porcentaje de pagos con qr y porcentaje de pagos con app
@app.route('/porcentaje-pagos-qr-app', methods=['GET'])
def porcentaje_pagos_qr_app():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        WITH total AS (
            SELECT COUNT(DISTINCT Id_transaccion) AS total_transacciones_global
            FROM fact_table
            WHERE Id_tipo_operacion IN (1, 7)
        )
        SELECT
            t.Operacion,
            COUNT(DISTINCT fact_table.Id_transaccion) AS total_transacciones,
            ROUND(
                (COUNT(DISTINCT fact_table.Id_transaccion) * 100.0) / total.total_transacciones_global, 2
            ) AS porcentaje
        FROM fact_table
        LEFT JOIN dim_operaciones AS t ON fact_table.Id_tipo_operacion = t.Id_tipo_operacion
        JOIN total ON 1=1
        WHERE fact_table.Id_tipo_operacion IN (1, 7)
        GROUP BY t.Operacion, fact_table.Id_tipo_operacion, total.total_transacciones_global
        ORDER BY porcentaje DESC;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

#nueva endpoint 4 - Transacciones por Grupo de Edad y Tipo de Operación
@app.route('/transacciones-grupo-edad-operacion', methods=['GET'])
def transacciones_grupo_edad_operacion():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            CASE
                WHEN U.Edad BETWEEN 18 AND 25 THEN '18-25'
                WHEN U.Edad BETWEEN 26 AND 35 THEN '26-35'
                WHEN U.Edad BETWEEN 36 AND 45 THEN '36-45'
                WHEN U.Edad BETWEEN 46 AND 55 THEN '46-55'
                WHEN U.Edad BETWEEN 56 AND 65 THEN '56-65'
                WHEN U.Edad > 65 THEN '65+'
                ELSE 'Desconocido'
            END AS Grupo_edad,
            F.Id_tipo_operacion,
            COUNT(DISTINCT F.Id_transaccion) AS total_transacciones
        FROM fact_table AS F
        LEFT JOIN dim_usuarios AS U ON F.Usuario_emisor = U.Id_usuario
        WHERE (F.Id_tipo_operacion = 1 OR F.Id_tipo_operacion = 7)
          AND U.Tipo_usuario = 'usuario'
        GROUP BY Grupo_edad, F.Id_tipo_operacion
        ORDER BY Grupo_edad, F.Id_tipo_operacion;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

#Nueva endpoint 5 - G3 Ticket medio QR, ticket medio App
@app.route('/ticket-medio-qr-app', methods=['GET'])
def ticket_medio_qr_app():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            o.Operacion,
            AVG(Cantidad) AS Ticket_medio
        FROM fact_table
        LEFT JOIN dim_operaciones AS o ON fact_table.Id_tipo_operacion = o.Id_tipo_operacion
        WHERE fact_table.Id_tipo_operacion IN (1, 7)
        GROUP BY o.Operacion;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

#Nuevo endpoint 6 - Transacciones por horas
@app.route('/transacciones-por-horas', methods=['GET'])
def transacciones_por_horas():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            HOUR(Hora_transaccion) AS Hora_Dia,
            SUM(Cantidad) AS Promedio_Cantidad
        FROM fact_table
        WHERE fact_table.Id_tipo_operacion IN (1, 7)
        GROUP BY HOUR(Hora_transaccion)
        ORDER BY HOUR(Hora_transaccion);
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Ejecutar la aplicación
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("¡Tablas creadas exitosamente!")
        except Exception as e:
            print(f"Error creando tablas: {str(e)}")
    
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv('DATA_API_APP_PORT', 5000)))