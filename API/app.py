from flask import Flask, jsonify
from flask_cors import CORS
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
            return mydb
        except Exception as e:
            if i < max_tries - 1:  # si no es el último intento
                time.sleep(2)
            else:
                raise


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
    WHERE Tipo_usuario NOT IN ('Asociacion', 'ekhilur')
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
        ELSE 0
    END AS Incremento_Porcentual
FROM Totals;
    """
    
    mycursor.execute(query)
    results = mycursor.fetchall()
    print(type)
    return jsonify(results)

@app.route('/analyze_monthly_average_simple', methods=['GET'])
def analyze_monthly_average_simple():
    mycursor = mydb.cursor(dictionary=True)

    query = """
WITH Fechas2024 AS (
    SELECT Id_fecha, Mes 
    FROM dim_fecha 
    WHERE Ano = 2024
),
Operaciones2024 AS (
    SELECT 
        f.Usuario_emisor, 
        d.Mes,
        f.Cantidad
    FROM fact_table f
    INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
    INNER JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
    INNER JOIN dim_usuarios du_origen ON f.Usuario_emisor = du_origen.Id_usuario
    INNER JOIN dim_usuarios du_destino ON f.Usuario_receptor = du_destino.Id_usuario
    WHERE o.Operacion IN ('Pago a usuario', 'Cobro desde QR')
      AND (
          (du_origen.Tipo_usuario = 'usuario' AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo'))  -- Pago normal: usuario a profesional
          OR (du_origen.Tipo_usuario IN ('Empresa', 'autonomo') AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo'))  -- Pago entre profesionales
      )
      AND NOT (
          o.Operacion = 'Pago a usuario' 
          AND (
              (du_origen.Tipo_usuario IN ('Empresa', 'autonomo') AND du_destino.Tipo_usuario = 'usuario')  -- Recarga
              OR (du_origen.Tipo_usuario = 'usuario' AND du_destino.Tipo_usuario = 'usuario')  -- Bizum entre usuarios
          )
      )
),
GastoMensual AS (
    SELECT 
        Usuario_emisor, 
        Mes, 
        ROUND(SUM(Cantidad), 2) AS GastoMensual
    FROM Operaciones2024
    GROUP BY Usuario_emisor, Mes
)
SELECT 
    Mes,
    ROUND(AVG(GastoMensual), 2) AS Gasto_Medio_Mensual,
    COUNT(DISTINCT Usuario_emisor) AS Num_Usuarios
FROM GastoMensual
GROUP BY Mes
ORDER BY Mes;
    """

    mycursor.execute(query)
    result = mycursor.fetchall()

    return jsonify(result)

@app.route('/analyze_monthly_savings', methods=['GET'])
def analyze_monthly_savings():
    mycursor = mydb.cursor(dictionary=True)

    query = """
WITH Fechas2024 AS (
    SELECT Id_fecha, Mes 
    FROM dim_fecha 
    WHERE Ano = 2024
),
Bonificaciones AS (
    SELECT 
        f.Usuario_receptor,
        d.Mes,
        f.Cantidad
    FROM fact_table f
    INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
    INNER JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
    WHERE o.Operacion IN ('Bonificación por compra', 'Descuento automático')
),
AhorroMensual AS (
    SELECT 
        Usuario_receptor,
        Mes,
        ROUND(SUM(Cantidad), 2) AS AhorroMensual
    FROM Bonificaciones
    GROUP BY Usuario_receptor, Mes
)
SELECT 
    Mes,
    ROUND(AVG(AhorroMensual), 2) AS Ahorro_Medio_Mensual,
    COUNT(DISTINCT Usuario_receptor) AS Num_Usuarios,
    ROUND(SUM(AhorroMensual), 2) AS Total_Bonificaciones
FROM AhorroMensual
GROUP BY Mes
ORDER BY Mes;
    """

    mycursor.execute(query)
    result = mycursor.fetchall()

    return jsonify(result)

@app.route('/analyze_total_simple', methods=['GET'])
def analyze_total_simple():
    mycursor = mydb.cursor(dictionary=True)

    query = """
WITH UltimoMes AS (
    SELECT Id_fecha 
    FROM dim_fecha 
    WHERE Ano = 2024 AND Mes = 12
),
Operaciones AS (
    SELECT 
        f.Id_transaccion,
        f.Cantidad
    FROM fact_table f
    INNER JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
    INNER JOIN dim_usuarios du_origen ON f.Usuario_emisor = du_origen.Id_usuario
    INNER JOIN dim_usuarios du_destino ON f.Usuario_receptor = du_destino.Id_usuario
    WHERE f.Id_fecha IN (SELECT Id_fecha FROM UltimoMes)
      AND o.Operacion IN ('Pago a usuario', 'Cobro desde QR')
      AND (
          (du_origen.Tipo_usuario = 'usuario' AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo'))  -- Caso 1: Pago normal (usuario a profesional)
          OR (du_origen.Tipo_usuario IN ('Empresa', 'autonomo') AND du_destino.Tipo_usuario IN ('Empresa', 'autonomo'))  -- Caso 2: Pago entre profesionales
      )
)
SELECT 
    COUNT(DISTINCT Id_transaccion) AS `Número total de operaciones`, 
    ROUND(SUM(Cantidad), 2) AS `Importe total (€)`
FROM Operaciones;
    """

    mycursor.execute(query)
    result = mycursor.fetchone()

    return jsonify(result)
@app.route('/analyze_cash_flow', methods=['GET'])
def analyze_cash_flow():
    mycursor = mydb.cursor(dictionary=True)

    # Consulta para obtener el flujo de caja mensual
    monthly_query = """
WITH Fechas2024 AS (
    SELECT Id_fecha, Mes 
    FROM dim_fecha 
    WHERE Ano = 2024
),
Operaciones2024 AS (
    SELECT 
        f.Id_fecha, 
        f.Cantidad, 
        d.Mes,
        o.Operacion
    FROM fact_table f
    INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
    INNER JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
    WHERE o.Operacion IN (
        'Recarga por tarjeta',
        'Bonificación por compra',
        'Conversión a €',
        'Cuota mensual de socio',
        'Cuota variable'
    )
),
EntradasSalidas AS (
    SELECT 
        Mes,
        ROUND(SUM(CASE WHEN Operacion IN ('Recarga por tarjeta', 'Bonificación por compra') THEN Cantidad ELSE 0 END), 2) AS Entradas,
        ROUND(SUM(CASE WHEN Operacion IN ('Conversión a €', 'Cuota mensual de socio', 'Cuota variable') THEN Cantidad ELSE 0 END), 2) AS Salidas
    FROM Operaciones2024
    GROUP BY Mes
)
SELECT 
    Mes,
    Entradas,
    Salidas,
    (Entradas - Salidas) AS Balance
FROM EntradasSalidas
ORDER BY Mes;
    """

    # Consulta para obtener los totales anuales
    totals_query = """
WITH Fechas2024 AS (
    SELECT Id_fecha 
    FROM dim_fecha 
    WHERE Ano = 2024
),
Operaciones2024 AS (
    SELECT 
        f.Cantidad,
        o.Operacion
    FROM fact_table f
    INNER JOIN Fechas2024 d ON f.Id_fecha = d.Id_fecha
    INNER JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
    WHERE o.Operacion IN (
        'Recarga por tarjeta',
        'Bonificación por compra',
        'Conversión a €',
        'Cuota mensual de socio',
        'Cuota variable'
    )
)
SELECT 
    ROUND(SUM(CASE WHEN Operacion IN ('Recarga por tarjeta', 'Bonificación por compra') THEN Cantidad ELSE 0 END), 2) AS `Total Entradas (€)`,
    ROUND(SUM(CASE WHEN Operacion IN ('Conversión a €', 'Cuota mensual de socio', 'Cuota variable') THEN Cantidad ELSE 0 END), 2) AS `Total Salidas (€)`,
    ROUND(SUM(CASE WHEN Operacion IN ('Recarga por tarjeta', 'Bonificación por compra') THEN Cantidad ELSE 0 END) -
          SUM(CASE WHEN Operacion IN ('Conversión a €', 'Cuota mensual de socio', 'Cuota variable') THEN Cantidad ELSE 0 END), 2) AS `Balance Neto (€)`
FROM Operaciones2024;
    """

    mycursor.execute(monthly_query)
    monthly_results = mycursor.fetchall()

    mycursor.execute(totals_query)
    totals_result = mycursor.fetchone()

    response = {
        "Flujo de dinero mensual 2024": monthly_results,
        "Totales anuales": totals_result
    }

    return jsonify(response)
# fin Nuevos 5 endpoint para landingpage "ekhilur"

#ENDPOINTS PARA SECCION USUARIOS
#Nueva endpoint 1 - Gráfico de barras por cantidad de usuarios y grupo de edad
@app.route('/cantidad-usuarios-grupo-edad', methods=['GET'])
def cantidad_usuarios_grupo_edad():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT
            CASE 
                WHEN Edad BETWEEN 18 AND 25 THEN '18-25' 
                WHEN Edad BETWEEN 26 AND 35 THEN'26-35' 
                WHEN Edad BETWEEN 36 AND 45 THEN '36-45' 
                WHEN Edad BETWEEN 46 AND 55 THEN '46-55' 
                WHEN Edad BETWEEN 56 AND 65 THEN '56-65' 
                WHEN Edad > 65 THEN '66+' 
                ELSE 'Desconocido' 
            END AS Grupo_edad, 
        COUNT(*) AS cantidad_usuarios FROM dim_usuarios 
        WHERE Edad IS NOT NULL AND Tipo_usuario = 'usuario' 
        GROUP BY Grupo_edad 
        ORDER BY Grupo_edad;
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
        GROUP BY F.Ano, F.Mes;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Nueva endpoint 3: Patrones G1 - Pie chart porcentaje de pagos con qr y porcentaje de pagos con app
@app.route('/porcentaje-pagos-qr-app', methods=['GET'])
def porcentaje_pagos_qr_app():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT 
            op.Operacion,
            COUNT(f.Id_transaccion) AS total_operaciones,
            ROUND(
                100.0 * COUNT(f.Id_transaccion) / SUM(COUNT(f.Id_transaccion)) OVER (),
                2
            ) AS porcentaje
        FROM fact_table f
        JOIN dim_usuarios ue ON f.Usuario_emisor = ue.Id_usuario
        JOIN dim_usuarios ur ON f.Usuario_receptor = ur.Id_usuario
        JOIN dim_operaciones op ON f.Id_tipo_operacion = op.Id_tipo_operacion 
        WHERE 
            f.Id_tipo_operacion IN (1, 7)
            AND ue.Tipo_usuario = 'usuario'
            AND ur.Tipo_usuario IN ('Empresa', 'autonomo')
        GROUP BY f.Id_tipo_operacion, op.Operacion;
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
                WHEN ue.Edad BETWEEN 18 AND 25 THEN '18-25' 
                WHEN ue.Edad BETWEEN 26 AND 35 THEN '26-35' 
                WHEN ue.Edad BETWEEN 36 AND 45 THEN '36-45' 
                WHEN ue.Edad BETWEEN 46 AND 55 THEN '46-55' 
                WHEN ue.Edad BETWEEN 56 AND 65 THEN '56-65' 
                WHEN ue.Edad > 65 THEN '66+' 
                ELSE 'Desconocido' 
            END AS Grupo_edad,
            F.Id_tipo_operacion,
            COUNT(DISTINCT F.Id_transaccion) AS total_transacciones
        FROM fact_table AS F
        JOIN dim_usuarios AS ue ON F.Usuario_emisor = ue.Id_usuario
        JOIN dim_usuarios ur ON F.Usuario_receptor = ur.Id_usuario
        WHERE (F.Id_tipo_operacion = 1 OR F.Id_tipo_operacion = 7) 
        AND ue.Tipo_usuario = 'usuario'
        AND ur.Tipo_usuario IN ('Empresa', 'autonomo')
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
        SELECT o.Operacion, AVG(Cantidad) AS Ticket_medio
        FROM fact_table
        LEFT JOIN dim_operaciones AS o ON fact_table.Id_tipo_operacion = o.Id_tipo_operacion
        JOIN dim_usuarios ue ON fact_table.Usuario_emisor = ue.Id_usuario
        JOIN dim_usuarios ur ON fact_table.Usuario_receptor = ur.Id_usuario
        WHERE fact_table.Id_tipo_operacion IN (1, 7) 
            AND ue.Tipo_usuario = 'usuario'
            AND ur.Tipo_usuario IN ('Empresa', 'autonomo')
        GROUP BY o.Operacion;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

#Nuevo endpoint 6 - G4 Transacciones por horas
@app.route('/transacciones-por-horas', methods=['GET'])
def transacciones_por_horas():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        SELECT HOUR(Hora_transaccion) AS Hora_Dia, ROUND(SUM(Cantidad)/ COUNT(DISTINCT Id_fecha),2) AS Promedio_Cantidad
        FROM fact_table
        JOIN dim_usuarios ue ON fact_table.Usuario_emisor = ue.Id_usuario
        JOIN dim_usuarios ur ON fact_table.Usuario_receptor = ur.Id_usuario
        WHERE fact_table.Id_tipo_operacion IN (1, 7) 
            AND ue.Tipo_usuario = 'usuario'
            AND ur.Tipo_usuario IN ('Empresa', 'autonomo')
        GROUP BY HOUR(Hora_transaccion)
        ORDER BY HOUR(Hora_transaccion);
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Nuevo endpoint 7 - "TRANSACCIONES" La suma por para cada tipo de transacción
@app.route('/suma-por-tipo-de-transaccion', methods=['GET'])
def suma_por_tipo_operacion():
    mycursor = mydb.cursor(dictionary=True)

    # La suma por para cada tipo de transacción
    mycursor.execute("""
        SELECT
	fe.Ano AS Anho,
	fe.Mes AS Mes,
	CASE
		WHEN (op.Operacion = 'Pago a usuario' OR op.Operacion = 'Cobro desde QR') AND ue.Tipo_usuario = 'usuario' AND ur.Tipo_usuario IN ('autonomo', 'Empresa')
			THEN 'Pago en tienda'
		WHEN op.Operacion = 'Pago a usuario' AND ue.Tipo_usuario = 'usuario' AND ur.Tipo_usuario = 'usuario'
			THEN 'Transferencia entre usuarios'	
		WHEN (op.Operacion = 'Pago a usuario' OR op.Operacion = 'Cobro desde QR') AND ue.Tipo_usuario IN ('autonomo', 'Empresa') AND ur.Tipo_usuario IN ('autonomo', 'Empresa')
			THEN 'Transferencia entre comercios'
		WHEN op.Operacion = 'Recarga por tarjeta'
			THEN 'Recarga App'
		WHEN op.Operacion = 'Pago a usuario' AND ue.Tipo_usuario IN ('autonomo', 'Empresa') AND ur.Tipo_usuario = 'usuario'
			THEN 'Recarga en tienda'
		WHEN op.Operacion = 'Bonificación por compra'
			THEN 'Cashback Ayuntamiento'
		WHEN op.Operacion = 'Descuento automático'
			THEN 'Cashback Comercio'
		WHEN op.Operacion = 'Donación'
			THEN 'Donación'
		WHEN op.Operacion = 'Cuota de socio'
			THEN 'Matrícula de socio'
		WHEN op.Operacion = 'Cuota mensual de socio'
			THEN 'Cuota mensual de socio'
		WHEN op.Operacion = 'Cuota variable'
			THEN 'Cuota variable'
		WHEN op.Operacion = 'Retirada a cuenta bancaria'
			THEN 'Retirada a cuenta bancaria'
		WHEN  op.Operacion = 'Comisión por retirada'
			THEN 'Comisión por retirada'
		WHEN op.Operacion = 'Conversión a €'
			THEN 'Conversión a €'
		ELSE 'Otros'
	END AS Tipo_operacion,
	COUNT(DISTINCT ft.Id_transaccion) AS num_transacciones,
	SUM(Cantidad) AS Dinero_total
FROM fact_table ft
LEFT JOIN dim_operaciones op ON ft.Id_tipo_operacion = op.Id_tipo_operacion
LEFT JOIN dim_usuarios ue ON ft.Usuario_emisor = ue.Id_usuario
LEFT JOIN dim_usuarios ur ON ft.Usuario_receptor = ur.Id_usuario
LEFT JOIN dim_fecha fe ON ft.Id_fecha = fe.Id_fecha
WHERE op.Operacion != 'Transferencia interna'
GROUP BY fe.Ano, fe.Mes, Tipo_operacion
ORDER BY Anho ASC, Mes ASC, Dinero_total DESC;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Nuevo endpoint 8 - G6 Total gastado vs Total devuelto en cashback
@app.route('/gasto-total-vs-cashback-total', methods=['GET'])
def gasto_vs_cashback():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("""
        SELECT 
            CASE 
                WHEN Id_tipo_operacion IN (1, 7) 
                    AND Usuario_emisor IN (SELECT du.Id_usuario FROM dim_usuarios du WHERE du.Tipo_usuario = 'usuario')
                    AND Usuario_receptor IN (SELECT du.Id_usuario FROM dim_usuarios du WHERE du.Tipo_usuario IN ('Empresa', 'autonomo'))
                THEN 'Gasto_total'
                WHEN Id_tipo_operacion IN (0, 4) THEN 'Cashback_total'
            END AS Categoria,
            SUM(Cantidad) AS Total
        FROM fact_table
        WHERE Id_tipo_operacion IN (0, 1, 4, 7)
        GROUP BY Categoria
        HAVING Categoria IS NOT NULL
        ORDER BY Total DESC;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Nuevo endpoint 9 - G7 Distribución Mensual de Cantidad Total entre semana/findesemana
@app.route('/total-entresemana-findesemana', methods=['GET'])
def distribucion_semanal_mensual():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("""
        SELECT df.Mes, 
            CASE 
                WHEN df.DoW IN (0,1,2,3,4) THEN 'Entre semana'
                WHEN df.DoW IN (5,6) THEN 'Fin de semana'
            END AS dia_semana,
            SUM(ft.Cantidad) as Cantidad_total
        FROM fact_table ft
        LEFT JOIN dim_fecha df ON ft.Id_fecha = df.Id_fecha
        JOIN dim_usuarios ue ON ft.Usuario_emisor = ue.Id_usuario
        JOIN dim_usuarios ur ON ft.Usuario_receptor = ur.Id_usuario
        WHERE ft.Id_tipo_operacion IN (1, 7) 
            AND ue.Tipo_usuario = 'usuario'
            AND ur.Tipo_usuario IN ('Empresa', 'autonomo')
        GROUP BY df.Mes, dia_semana
        ORDER BY df.Mes;
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
    
@app.route('/usuarios-unicos-mensuales-semana-dia', methods=['GET'])
def usuarios_unicos_mensuales():
    query_datos_completo = """
    WITH Usuarios_distintos AS (
    SELECT Id_fecha, COUNT(DISTINCT Usuario_emisor) AS usuarios_distintos
    FROM fact_table ft
    LEFT JOIN dim_usuarios ue ON ft.Usuario_emisor = ue.Id_usuario
    WHERE ue.Tipo_usuario = 'usuario'
    GROUP BY Id_fecha
),
Usuarios_compra AS (
    SELECT Id_fecha, COUNT(DISTINCT Usuario_emisor) AS usuarios_compra
    FROM fact_table ft
    LEFT JOIN dim_usuarios ue ON ft.Usuario_emisor = ue.Id_usuario
    LEFT JOIN dim_usuarios ur ON ft.Usuario_receptor = ur.Id_usuario
    WHERE ue.Tipo_usuario = 'usuario'
        AND ft.Id_tipo_operacion IN (1,7)
        AND ur.Tipo_usuario IN ('autonomo', 'Empresa')
    GROUP BY Id_fecha
)
SELECT
    ud.Id_fecha,
    ud.usuarios_distintos,
    COALESCE(uc.usuarios_compra, 0) AS usuarios_compra  -- Maneja valores nulos si no hay compras ese día
FROM Usuarios_distintos ud
LEFT JOIN Usuarios_compra uc ON ud.Id_fecha = uc.Id_fecha
ORDER BY ud.Id_fecha;
    """
    
    # Ejecutar la consulta
    df = pd.read_sql(query_datos_completo, mydb)
    
    # Convertir Id_fecha a datetime
    df['fecha'] = pd.to_datetime(df['Id_fecha'], format='%Y%m%d')
    
    # Calcular medias móviles
    df['media_movil_14d'] = df['usuarios_unicos_dia'].rolling(window=14, center=True).mean()
    df['media_movil_28d'] = df['usuarios_unicos_dia'].rolling(window=28, center=True).mean()
    
    # Preparar datos para promedios semanales y mensuales
    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    promedios_semanales = df.groupby('dia_semana')['promedio_usuarios_dia'].first().reindex(orden_dias)
    
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    usuarios_mensuales = df.groupby('mes')['usuarios_unicos_mes'].first().reindex(orden_meses)
    
    # Crear el diccionario de resultados
    resultados = {
        "estadisticas_diarias": {
            "media_usuarios_dia": float(df['usuarios_unicos_dia'].mean()),
            "mediana_usuarios_dia": float(df['usuarios_unicos_dia'].median()),
            "maximo_usuarios_dia": float(df['usuarios_unicos_dia'].max()),
            "minimo_usuarios_dia": float(df['usuarios_unicos_dia'].min())
        },
        "datos_diarios": df[['Id_fecha', 'usuarios_unicos_dia', 'media_movil_14d', 'media_movil_28d']].to_dict('records'),
        "promedios_semanales": promedios_semanales.to_dict(),
        "usuarios_mensuales": usuarios_mensuales.to_dict()
    }
    
    return jsonify(resultados)
    
@app.route('/medias-moviles', methods=['GET'])
def medias_moviles():
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("""
        WITH merged AS (
          SELECT
            f.Id_fecha,
            f.Id_tipo_operacion,
            f.Cantidad,
            f.Usuario_emisor,
            f.Usuario_receptor,
            -- Convertimos Id_fecha al tipo DATE asumiendo el formato 'YYYYMMDD'
            STR_TO_DATE(f.Id_fecha, '%Y%m%d') AS fecha,
            du_em.Tipo_usuario AS Tipo_emisor,
            du_rec.Tipo_usuario AS Tipo_receptor
          FROM fact_table f
          LEFT JOIN dim_operaciones d
            ON f.Id_tipo_operacion = d.Id_tipo_operacion
          LEFT JOIN dim_usuarios du_em
            ON f.Usuario_emisor = du_em.Id_usuario
          LEFT JOIN dim_usuarios du_rec
            ON f.Usuario_receptor = du_rec.Id_usuario
        ),
        compras AS (
          SELECT
            *,
            CASE
              WHEN Id_tipo_operacion = 7 THEN 1
              WHEN Id_tipo_operacion = 1
                   AND Tipo_emisor IN ('usuario', 'autonomo', 'Empresa')
                   AND Tipo_receptor IN ('autonomo', 'Empresa') THEN 1
              ELSE 0
            END AS es_compra
          FROM merged
        ),
        compras_filtradas AS (
          SELECT *
          FROM compras
          WHERE es_compra = 1
        ),
        suma_diaria AS (
          SELECT
            fecha,
            SUM(Cantidad) AS suma_dia
          FROM compras_filtradas
          GROUP BY fecha
        ),
        rolling_sum AS (
          SELECT
            fecha,
            suma_dia,
            CASE
              WHEN COUNT(suma_dia) OVER (
                     ORDER BY fecha
                     ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                   ) < 14 THEN NULL
              ELSE SUM(suma_dia) OVER (
                     ORDER BY fecha
                     ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
                   )
            END AS sum_compras_acumulado
          FROM suma_diaria
        )
        SELECT
          fecha AS Id_fecha,
          suma_dia AS Cantidad,
          sum_compras_acumulado,
          LAG(sum_compras_acumulado, 14) OVER (ORDER BY fecha) AS shift_14
        FROM rolling_sum
        ORDER BY fecha;
    """)
    resultado = mycursor.fetchall()
    return jsonify(resultado)

    # MAPAS
# Endpoint mapa usuarios por zona
@app.route('/mapa-usuarios-zona', methods=['GET'])
def mapa_usuarios_zona():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("""
    SELECT Nombre_calle,
        Coordenadas,
        SUBSTRING_INDEX(Coordenadas, ',', 1) AS Latitud,
        SUBSTRING_INDEX(Coordenadas, ',', -1) AS Longitud,
        COUNT(DISTINCT Id_usuario) AS num_usuarios
    FROM dim_usuarios du    
    LEFT JOIN dim_direcciones dd ON du.Id_direccion = dd.Id_calle
    WHERE du.Tipo_usuario = 'usuario' AND Coordenadas IS NOT NULL
    GROUP BY Nombre_calle, Coordenadas
    ORDER BY Nombre_calle;
    """)
    
    
    resultado = mycursor.fetchall()
    return jsonify(resultado)

# Endpoint  MAPA usuarios unicos diarios    
@app.route('/mapa-ticket-medio', methods=['GET'])
def mapa_ticket_medio():
    mycursor = mydb.cursor(dictionary=True)

    mycursor.execute("""
    SELECT Nombre_calle,
        Coordenadas,
        SUBSTRING_INDEX(Coordenadas, ',', 1) AS Latitud,
        SUBSTRING_INDEX(Coordenadas, ',', -1) AS Longitud,
        AVG(Cantidad) AS Ticket_medio
    FROM fact_table ft
    LEFT JOIN dim_usuarios ue ON ft.Usuario_emisor = ue.Id_usuario
    LEFT JOIN dim_usuarios ur ON ft.Usuario_receptor = ur.Id_usuario
    LEFT JOIN dim_direcciones dd ON ue.Id_direccion = dd.Id_calle
    WHERE ft.Id_tipo_operacion IN (1,7) AND ue.Tipo_usuario = 'usuario' AND ur.Tipo_usuario IN ('Empresa', 'autonomo') AND Coordenadas IS NOT NULL
    GROUP BY Nombre_calle, Coordenadas
    ORDER BY Nombre_calle;
    """)
    
    
    resultado = mycursor.fetchall()
    return jsonify(resultado)



# Ejecutar la aplicación
if __name__ == '__main__':

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            pass
    
    app.run(debug=True, host="0.0.0.0", port= 5000)