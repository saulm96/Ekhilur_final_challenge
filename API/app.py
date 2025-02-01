from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from dotenv import load_dotenv
import os
import time
from predictor_definitivo.predictor_ingresos import predecir_mes_siguiente, generar_informe, main
import pandas as pd

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
        COUNT(*) AS `Número total de operaciones`, 
        ROUND(SUM(Cantidad), 2) AS `Importe total (€)`
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

    # Consulta para obtener el flujo de caja mensual
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
        COALESCE(e.Entradas, 0) AS `Entradas (€)`,
        COALESCE(s.Salidas, 0) AS `Salidas (€)`
    FROM Entradas e
    LEFT JOIN Salidas s ON e.Mes = s.Mes
    UNION DISTINCT
    SELECT 
        CAST(COALESCE(e.Mes, s.Mes) AS UNSIGNED) AS Mes,
        COALESCE(e.Entradas, 0) AS `Entradas (€)`,
        COALESCE(s.Salidas, 0) AS `Salidas (€)`
    FROM Salidas s
    LEFT JOIN Entradas e ON s.Mes = e.Mes
    ORDER BY Mes;
    """

    mycursor.execute(query)
    monthly_results = mycursor.fetchall()

    # Consulta para obtener los totales anuales
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
        Total_Entradas AS `Total Entradas (€)`,
        Total_Salidas AS `Total Salidas (€)`,
        (Total_Entradas - Total_Salidas) AS `Balance Neto (€)`
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

# Nuevo endpoint 7 - "TRANSACCIONES" La suma por para cada tipo de transacción
@app.route('/suma_por_tipo_de_transaccion', methods=['GET'])
def suma_por_tipo_de_transaccion():
    mycursor = mydb.cursor(dictionary=True)

    # La suma por para cada tipo de transacción
    mycursor.execute("""
        SELECT o.Operacion, SUM(f.Cantidad) AS Total_Cantidad, COUNT(f.Id_transaccion) AS Total_Transacciones 
        FROM fact_table f
        LEFT JOIN dim_operaciones o ON o.Id_tipo_operacion = f.Id_tipo_operacion
        GROUP BY o.Operacion;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Endpoint para predicciones
@app.route('/predict', methods=['GET'])
def predict():
    """
    Endpoint principal para predicciones usando la base de datos
    """
    try:
        from predictor_definitivo.predictor_ingresos import predecir_mes_siguiente_db
        resultado = predecir_mes_siguiente_db()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict/csv', methods=['GET'])
def predict_csv():
    """
    Endpoint para realizar predicciones usando solo datos de CSV
    """
    try:
        from predictor_definitivo.predictor_ingresos import predecir_mes_siguiente_csv
        resultado = predecir_mes_siguiente_csv()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict/db', methods=['GET'])
def predict_db():
    """
    Endpoint para realizar predicciones usando solo datos de la base de datos
    """
    try:
        from predictor_definitivo.predictor_ingresos import predecir_mes_siguiente_db
        resultado = predecir_mes_siguiente_db()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model/retrain', methods=['POST'])
def retrain_model():
    """
    Endpoint para reentrenar el modelo con los datos más recientes
    """
    try:
        from predictor_definitivo.predictor_ingresos import entrenar_modelo
        resultado = entrenar_modelo()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": f"Error al reentrenar el modelo: {str(e)}",
            "detalles": {}
        }), 500

@app.route('/model/versions', methods=['GET'])
def list_model_versions():
    """
    Endpoint para listar todas las versiones disponibles del modelo
    """
    try:
        from predictor_definitivo.predictor_ingresos import listar_versiones
        resultado = listar_versiones()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": f"Error al listar versiones: {str(e)}",
            "versiones": []
        }), 500

@app.route('/model/revert/<version>', methods=['POST'])
def revert_model_version(version):
    """
    Endpoint para revertir el modelo a una versión específica
    """
    try:
        from predictor_definitivo.predictor_ingresos import revertir_modelo
        resultado = revertir_modelo(version)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            "estado": "error",
            "mensaje": f"Error al revertir el modelo: {str(e)}",
            "detalles": {}
        }), 500
    
@app.route('/usuarios-unicos-mensuales', methods=['GET'])
def usuarios_unicos_mensuales():
    query_datos_completo = """
    WITH actividad_mensual AS (
        SELECT 
            SUBSTRING(f.Id_fecha, 1, 6) as año_mes,
            du_origen.Tipo_usuario as tipo_usuario_origen,
            du_destino.Tipo_usuario as tipo_usuario_destino,
            CASE 
                WHEN o.Operacion = 'Cobro desde QR' THEN 'Cobro QR'
                WHEN o.Operacion = 'Pago a usuario' AND 
                     ((du_origen.Tipo_usuario = 'usuario' AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo')) OR
                      (du_origen.Tipo_usuario IN ('Empresa', 'autonomo') AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo')))
                    THEN 'Pago normal'
                WHEN o.Operacion = 'Pago a usuario' AND 
                     du_origen.Tipo_usuario IN ('Empresa', 'autonomo') AND 
                     du_destino.Tipo_usuario = 'usuario'
                    THEN 'Recarga'
            END as tipo_operacion,
            COUNT(DISTINCT f.Usuario_emisor) as usuarios_unicos_mes,
            COUNT(*) as num_transacciones_mes,
            ROUND(SUM(f.Cantidad), 2) as volumen_euros
        FROM fact_table f
        JOIN dim_usuarios du_origen ON f.Usuario_emisor = du_origen.Id_usuario
        JOIN dim_usuarios du_destino ON f.Usuario_receptor = du_destino.Id_usuario
        JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        WHERE SUBSTRING(f.Id_fecha, 1, 4) = '2024'
        AND (
            o.Operacion = 'Cobro desde QR'
            OR
            (o.Operacion = 'Pago a usuario' AND 
             NOT (du_origen.Tipo_usuario = 'usuario' AND du_destino.Tipo_usuario = 'usuario'))
        )
        GROUP BY 
            SUBSTRING(f.Id_fecha, 1, 6),
            du_origen.Tipo_usuario,
            du_destino.Tipo_usuario,
            tipo_operacion
    )
    SELECT 
        a.año_mes,
        CASE SUBSTRING(a.año_mes, 5, 2)
            WHEN '01' THEN 'Enero'
            WHEN '02' THEN 'Febrero'
            WHEN '03' THEN 'Marzo'
            WHEN '04' THEN 'Abril'
            WHEN '05' THEN 'Mayo'
            WHEN '06' THEN 'Junio'
            WHEN '07' THEN 'Julio'
            WHEN '08' THEN 'Agosto'
            WHEN '09' THEN 'Septiembre'
            WHEN '10' THEN 'Octubre'
            WHEN '11' THEN 'Noviembre'
            WHEN '12' THEN 'Diciembre'
        END as mes,
        a.tipo_usuario_origen,
        a.tipo_operacion,
        a.usuarios_unicos_mes,
        a.num_transacciones_mes,
        a.volumen_euros
    FROM actividad_mensual a
    WHERE a.tipo_operacion IS NOT NULL
    ORDER BY a.año_mes, a.tipo_usuario_origen, a.tipo_operacion;
    """
    
    df = pd.read_sql(query_datos_completo, mydb)
    
    # Crear diccionario para ordenar los meses
    orden_meses = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
    }
    
    # Preparar el resultado
    resultado = {
        "datos_mensuales": {},
        "resumen_estadistico": {}
    }
    
    # Procesar datos mensuales
    for tipo_usuario in ['usuario', 'Empresa', 'autonomo']:
        datos_tipo = df[df['tipo_usuario_origen'] == tipo_usuario]
        datos_agrupados = datos_tipo.groupby(['mes', 'tipo_operacion']).agg({
            'usuarios_unicos_mes': 'max',
            'num_transacciones_mes': 'sum',
            'volumen_euros': 'sum'
        }).reset_index()
        
        resultado["datos_mensuales"][tipo_usuario] = {}
        
        # Ordenar los meses cronológicamente
        for mes in sorted(datos_agrupados['mes'].unique(), key=lambda x: orden_meses[x]):
            datos_mes = datos_agrupados[datos_agrupados['mes'] == mes]
            resultado["datos_mensuales"][tipo_usuario][mes] = {}
            
            for _, row in datos_mes.iterrows():
                resultado["datos_mensuales"][tipo_usuario][mes][row['tipo_operacion']] = {
                    "usuarios_unicos": int(row['usuarios_unicos_mes']),
                    "num_transacciones": int(row['num_transacciones_mes']),
                    "volumen_euros": float(row['volumen_euros'])
                }
    
    # Procesar resumen estadístico
    for tipo_usuario in ['usuario', 'Empresa', 'autonomo']:
        datos_tipo = df[df['tipo_usuario_origen'] == tipo_usuario]
        datos_agrupados = datos_tipo.groupby(['mes', 'tipo_operacion']).agg({
            'usuarios_unicos_mes': 'max',
            'num_transacciones_mes': 'sum',
            'volumen_euros': 'sum'
        }).reset_index()
        
        resultado["resumen_estadistico"][tipo_usuario] = {}
        
        for operacion in datos_agrupados['tipo_operacion'].unique():
            datos_op = datos_agrupados[datos_agrupados['tipo_operacion'] == operacion]
            max_mes = datos_op.loc[datos_op['usuarios_unicos_mes'].idxmax()]
            min_mes = datos_op.loc[datos_op['usuarios_unicos_mes'].idxmin()]
            
            resultado["resumen_estadistico"][tipo_usuario][operacion] = {
                "promedio_mensual_usuarios": float(datos_op['usuarios_unicos_mes'].mean()),
                "maximo": {
                    "usuarios": int(max_mes['usuarios_unicos_mes']),
                    "mes": max_mes['mes']
                },
                "minimo": {
                    "usuarios": int(min_mes['usuarios_unicos_mes']),
                    "mes": min_mes['mes']
                },
                "volumen_total_euros": float(datos_op['volumen_euros'].sum()),
                "total_transacciones": int(datos_op['num_transacciones_mes'].sum())
            }
    
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