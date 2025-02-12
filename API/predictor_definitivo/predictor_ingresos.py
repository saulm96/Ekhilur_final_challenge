# predictor_ingresos.py

import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import mysql.connector

# Definir rutas base
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, 'models')
DATA_DIR = os.path.join(SCRIPT_DIR, 'csv_base_datos')

def cargar_modelo_y_caracteristicas():
    """Carga el modelo y las características guardadas"""
    modelo_path = os.path.join(SCRIPT_DIR, 'modelo_ingresos_xgboost.pkl')
    caract_path = os.path.join(SCRIPT_DIR, 'caracteristicas_modelo.pkl')
    
    archivos_requeridos = [modelo_path, caract_path]
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            raise FileNotFoundError(f"No se encuentra el archivo {archivo}")
    
    try:
        with open(modelo_path, 'rb') as file:
            modelo = pickle.load(file)
        
        with open(caract_path, 'rb') as file:
            caracteristicas = pickle.load(file)
        
        return modelo, caracteristicas
    except Exception as e:
        raise Exception(f"Error al cargar archivos: {str(e)}")

def obtener_datos_historicos():
    """Obtiene los datos históricos de la base de datos"""
    try:
        # Conectar a la base de datos usando el puerto interno de Docker
        mydb = mysql.connector.connect(
            host=os.getenv('DATA_DB_HOST'),
            user=os.getenv('DATA_DB_USER'),
            password=os.getenv('DATA_DB_PASSWORD'),
            database=os.getenv('DATA_DB_DATABASE'),
            port=3306  # Puerto interno en la red de Docker
        )
        
        # Crear un cursor
        cursor = mydb.cursor()
        
        # Consulta SQL para obtener los datos necesarios
        query = """
        SELECT 
            df.Fecha,
            o.Operacion,
            u.Tipo_usuario,
            CAST(f.Cantidad AS FLOAT) as Cantidad,
            'Ingresos' as Tipo_Flujo
        FROM fact_table f
        LEFT JOIN dim_fecha df ON f.Id_fecha = df.Id_fecha
        LEFT JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        LEFT JOIN dim_usuarios u ON f.Usuario_emisor = u.Id_usuario
        WHERE o.Operacion IN (
            'Cuota mensual de socio',
            'Cuota variable',
            'Comisión por retirada',
            'Cuota de socio'
        )
        AND df.Fecha BETWEEN '2024-01-01' AND '2024-12-31'
        """
        
        # Ejecutar la consulta
        cursor.execute(query)
        
        # Obtener los resultados
        resultados = cursor.fetchall()
        
        # Crear DataFrame
        df = pd.DataFrame(resultados, columns=['Fecha', 'Operacion', 'Tipo_usuario', 'Cantidad', 'Tipo_Flujo'])
        
        # Asegurarse de que Cantidad sea float
        df['Cantidad'] = df['Cantidad'].astype(float)
        
        # Cerrar cursor y conexión
        cursor.close()
        mydb.close()
        
        return df
        
    except Exception as e:
        print(f"Error al obtener datos históricos: {str(e)}")
        return None

def obtener_estadisticas_historicas():
    """Obtiene estadísticas históricas para ajustar predicciones"""
    try:
        # Cargar datos originales usando rutas absolutas
        fact_table = pd.read_csv(os.path.join(DATA_DIR, 'fact_table.csv'), sep=';')
        dim_operaciones = pd.read_csv(os.path.join(DATA_DIR, 'dim_operaciones.csv'), sep=';')
        dim_usuarios = pd.read_csv(os.path.join(DATA_DIR, 'dim_usuarios.csv'), sep=';')
        dim_fecha = pd.read_csv(os.path.join(DATA_DIR, 'dim_fecha.csv'), sep=';')
        
        # Clasificar operaciones por tipo de flujo
        operaciones_ingreso = [
            'Cuota mensual de socio',
            'Cuota variable',
            'Comisión por retirada',
            'Cuota de socio'
        ]
        
        operaciones_salida = [
            'Conversión a €',
            'Retirada a cuenta bancaria'
        ]
        
        dim_operaciones['Tipo_Flujo'] = 'Movimientos'  # Por defecto
        dim_operaciones.loc[dim_operaciones['Operacion'].isin(operaciones_ingreso), 'Tipo_Flujo'] = 'Ingresos'
        dim_operaciones.loc[dim_operaciones['Operacion'].isin(operaciones_salida), 'Tipo_Flujo'] = 'Salidas'
        
        # Unir tablas
        df = fact_table.merge(dim_operaciones, on='Id_tipo_operacion', how='left')
        df = df.merge(dim_fecha, on='Id_fecha', how='left')
        df = df.merge(dim_usuarios, 
                     left_on='Usuario_emisor', 
                     right_on='Id_usuario', 
                     how='left',
                     suffixes=('', '_emisor'))

        # Convertir fecha
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Filtrar solo operaciones de ingreso
        df_ingresos = df[df['Tipo_Flujo'] == 'Ingresos'].copy()
        
        # Determinar el mes que queremos predecir (mes siguiente al actual)
        fecha_actual = pd.Timestamp.now()
        mes_prediccion = (fecha_actual.replace(day=1) + pd.DateOffset(months=1))
        
        # Obtener el mismo mes pero del año anterior
        mes_historico = mes_prediccion - pd.DateOffset(years=1)
        
        # Filtrar datos del mes histórico correspondiente
        mask_mes_historico = (df_ingresos['Fecha'].dt.year == mes_historico.year) & \
                            (df_ingresos['Fecha'].dt.month == mes_historico.month)
        df_ingresos_mes_historico = df_ingresos[mask_mes_historico]
        
        # Calcular ingresos mensuales por tipo de operación y usuario
        ingresos_mensuales = df_ingresos_mes_historico.groupby([
            'Operacion',
            'Tipo_usuario'
        ])['Cantidad'].agg([
            'sum',    # suma total
            'count',  # número de operaciones
            'mean'    # promedio por operación
        ]).reset_index()
        
        # Renombrar columnas para mantener consistencia
        ingresos_mensuales.columns = ['Operacion', 'Tipo_usuario', 'Total', 'Num_Operaciones', 'Promedio_Operacion']
        
        return ingresos_mensuales
    
    except Exception as e:
        print(f"Error al obtener estadísticas históricas: {str(e)}")
        return None

def predecir_mes_siguiente():
    """Realiza predicciones para el próximo mes y devuelve los resultados en formato JSON"""
    try:
        # Cargar modelo y características
        modelo, caracteristicas = cargar_modelo_y_caracteristicas()
        
        print("Intentando obtener datos de la base de datos...")
        # Intentar primero obtener datos de la base de datos
        df = obtener_datos_historicos()
        fuente_datos = {
            "principal": "Base de datos",
            "fallback": None,
            "razon_fallback": None
        }
        
        # Si falla la base de datos, usar CSV como respaldo
        if df is None:
            print("No se pudo obtener datos de la base de datos, usando CSV como respaldo...")
            stats_historicas = obtener_estadisticas_historicas()
            fuente_datos = {
                "principal": "CSV",
                "fallback": "Si",
                "razon_fallback": "Error de conexión con la base de datos"
            }
        else:
            print("Datos obtenidos exitosamente de la base de datos")
            # Calcular estadísticas de la base de datos
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            stats_historicas = df.groupby(['Operacion', 'Tipo_usuario']).agg({
                'Cantidad': ['sum', 'count', 'mean']
            }).reset_index()
            stats_historicas.columns = ['Operacion', 'Tipo_usuario', 'Total', 'Num_Operaciones', 'Promedio_Operacion']
        
        # Determinar fecha inicio (mes siguiente al último dato)
        ultima_fecha = pd.Timestamp.now()
        fecha_inicio = (ultima_fecha.replace(day=1) + pd.DateOffset(months=1))
        dias_siguiente_mes = pd.date_range(
            start=fecha_inicio,
            end=fecha_inicio + pd.DateOffset(months=1) - pd.DateOffset(days=1),
            freq='D'
        )
        
        # Preparar características para predicción
        X_futuro = pd.DataFrame()
        X_futuro['Mes'] = dias_siguiente_mes.month
        X_futuro['DiaSemana'] = dias_siguiente_mes.dayofweek
        X_futuro['DiaDelMes'] = dias_siguiente_mes.day
        X_futuro['EsFinDeSemana'] = X_futuro['DiaSemana'].isin([5,6]).astype(int)
        X_futuro['Semana'] = ((X_futuro['DiaDelMes'] - 1) // 7 + 1).astype(int)
        
        # Generar predicciones
        predicciones_futuras = []
        for op in caracteristicas['categorias_operacion']:
            for user in caracteristicas['categorias_tipo_usuario']:
                X_temp = X_futuro.copy()
                
                # Codificar variables categóricas
                X_temp['Operacion'] = pd.Categorical([op] * len(X_futuro), 
                                                   categories=caracteristicas['categorias_operacion']).codes
                X_temp['Tipo_usuario'] = pd.Categorical([user] * len(X_futuro), 
                                                      categories=caracteristicas['categorias_tipo_usuario']).codes
                
                # Ajustar características según estadísticas históricas
                if stats_historicas is not None:
                    stats_op = stats_historicas[stats_historicas['Operacion'] == op]
                    stats_op_user = stats_op[stats_op['Tipo_usuario'] == user]
                    
                    if not stats_op_user.empty:
                        total_mensual = stats_op_user['Total'].values[0]
                        num_ops_mensual = stats_op_user['Num_Operaciones'].values[0]
                        promedio_por_op = stats_op_user['Promedio_Operacion'].values[0]
                        
                        total_diario = total_mensual / len(dias_siguiente_mes)
                        ops_por_dia = num_ops_mensual / len(dias_siguiente_mes)
                        
                        X_temp['Num_Operaciones'] = ops_por_dia
                        X_temp['Promedio_Operacion'] = promedio_por_op
                    else:
                        X_temp['Num_Operaciones'] = 0
                        X_temp['Promedio_Operacion'] = 0
                else:
                    X_temp['Num_Operaciones'] = 0
                    X_temp['Promedio_Operacion'] = 0
                
                # Predicción
                pred = modelo.predict(X_temp)
                
                # Ajustar predicciones negativas
                pred = np.maximum(0, pred)
                
                # Ajustar predicciones según estadísticas históricas
                if stats_historicas is not None and not stats_op_user.empty:
                    total_mensual = stats_op_user['Total'].values[0]
                    factor_ajuste = total_mensual / pred.sum() if pred.sum() > 0 else 0
                    pred = pred * factor_ajuste
                
                # Guardar predicciones
                for dia, prediccion in zip(dias_siguiente_mes, pred):
                    if prediccion > 0:  # Solo guardar predicciones positivas
                        predicciones_futuras.append({
                            'Fecha': dia.strftime('%d/%m/%Y'),
                            'Operacion': op,
                            'Tipo_usuario': user,
                            'Prediccion': float(prediccion)
                        })
        
        # Crear DataFrame con predicciones
        df_predicciones = pd.DataFrame(predicciones_futuras)
        
        if not df_predicciones.empty:
            predicciones_diarias = df_predicciones.groupby('Fecha')['Prediccion'].sum()
        else:
            predicciones_diarias = pd.Series(0, index=dias_siguiente_mes.strftime('%d/%m/%Y'))

        # Preparar resumen de predicciones
        resumen = {
            'periodo': {
                'inicio': fecha_inicio.strftime('%d/%m/%Y'),
                'fin': (fecha_inicio + pd.DateOffset(months=1) - pd.DateOffset(days=1)).strftime('%d/%m/%Y')
            },
            'resumen_general': {
                'ingreso_total_predicho': float(predicciones_diarias.sum()),
                'ingreso_diario_promedio': float(predicciones_diarias.mean()),
                'dia_mayor_ingreso': {
                    'fecha': predicciones_diarias.idxmax(),
                    'cantidad': float(predicciones_diarias.max())
                },
                'dia_menor_ingreso': {
                    'fecha': predicciones_diarias.idxmin(),
                    'cantidad': float(predicciones_diarias.min())
                }
            },
            'predicciones_por_operacion': {},
            'predicciones_por_usuario': {},
            'predicciones_diarias': predicciones_diarias.to_dict(),
            'predicciones_futuras': predicciones_futuras,
            'fuente_datos': fuente_datos,
            'metadata': {
                'fecha_prediccion': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version_modelo': caracteristicas.get('fecha_entrenamiento', 'Desconocida')
            }
        }

        # Aplanar las predicciones por operación
        ops_summary = df_predicciones.groupby('Operacion').agg({
            'Prediccion': ['sum', 'mean', 'count']
        }).round(2)
        
        for operacion in ops_summary.index:
            resumen['predicciones_por_operacion'][operacion] = {
                'total': float(ops_summary.loc[operacion, ('Prediccion', 'sum')]),
                'promedio': float(ops_summary.loc[operacion, ('Prediccion', 'mean')]),
                'num_operaciones': int(ops_summary.loc[operacion, ('Prediccion', 'count')])
            }

        # Aplanar las predicciones por usuario
        user_summary = df_predicciones.groupby('Tipo_usuario').agg({
            'Prediccion': ['sum', 'mean', 'count']
        }).round(2)
        
        for usuario in user_summary.index:
            resumen['predicciones_por_usuario'][usuario] = {
                'total': float(user_summary.loc[usuario, ('Prediccion', 'sum')]),
                'promedio': float(user_summary.loc[usuario, ('Prediccion', 'mean')]),
                'num_operaciones': int(user_summary.loc[usuario, ('Prediccion', 'count')])
            }

        return resumen
    
    except Exception as e:
        return {'error': str(e)}

def generar_informe(df_predicciones, predicciones_diarias):
    """Genera un informe detallado de las predicciones"""
    # Obtener estadísticas históricas
    stats_historicas = obtener_estadisticas_historicas()
    fecha_actual = pd.Timestamp.now()
    # Obtener el mes que vamos a predecir (mes siguiente al actual)
    mes_prediccion = (fecha_actual.replace(day=1) + pd.DateOffset(months=1))
    # Obtener el mismo mes del año anterior para los datos históricos
    mes_historico = mes_prediccion - pd.DateOffset(years=1)

    # Preparar el diccionario de salida
    informe = {
        "datos_historicos": {
            "periodo": {
                "mes_analizado": mes_historico.strftime('%B %Y'),
                "mes_prediccion": mes_prediccion.strftime('%B %Y')
            }
        },
        "predicciones": {
            "periodo": {
                "inicio": min(predicciones_diarias.index),
                "fin": max(predicciones_diarias.index)
            }
        }
    }
    
    if stats_historicas is not None:
        # Cargar datos originales para obtener ingresos diarios históricos
        fact_table = pd.read_csv(os.path.join(DATA_DIR, 'fact_table.csv'), sep=';')
        dim_operaciones = pd.read_csv(os.path.join(DATA_DIR, 'dim_operaciones.csv'), sep=';')
        dim_fecha = pd.read_csv(os.path.join(DATA_DIR, 'dim_fecha.csv'), sep=';')
        
        # Definir operaciones de ingreso
        operaciones_ingreso = [
            'Cuota mensual de socio',
            'Cuota variable',
            'Comisión por retirada',
            'Cuota de socio'
        ]
        
        # Unir tablas
        df = fact_table.merge(dim_operaciones, on='Id_tipo_operacion', how='left')
        df = df.merge(dim_fecha, on='Id_fecha', how='left')
        
        # Filtrar solo operaciones de ingreso
        df = df[df['Operacion'].isin(operaciones_ingreso)]
        
        # Convertir fecha y filtrar el mes histórico
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        mask_mes_historico = (df['Fecha'].dt.year == mes_historico.year) & \
                           (df['Fecha'].dt.month == mes_historico.month)
        df_mes_historico = df[mask_mes_historico]
        
        # Calcular ingresos diarios históricos
        ingresos_diarios_hist = df_mes_historico.groupby('Fecha')['Cantidad'].sum()
        
        # Añadir resumen histórico al informe
        total_mensual = ingresos_diarios_hist.sum()
        promedio_diario = total_mensual / mes_historico.days_in_month
        
        informe["datos_historicos"]["resumen_general"] = {
            "ingreso_total": float(total_mensual),
            "ingreso_diario_promedio": float(promedio_diario),
            "dia_mayor_ingreso": {
                "fecha": ingresos_diarios_hist.idxmax().strftime('%d/%m/%Y'),
                "cantidad": float(ingresos_diarios_hist.max())
            },
            "dia_menor_ingreso": {
                "fecha": ingresos_diarios_hist.idxmin().strftime('%d/%m/%Y'),
                "cantidad": float(ingresos_diarios_hist.min())
            }
        }

    # Añadir resumen de predicciones al informe
    informe["predicciones"]["resumen_general"] = {
        "ingreso_total_predicho": float(predicciones_diarias.sum()),
        "ingreso_diario_promedio": float(predicciones_diarias.mean()),
        "dia_mayor_ingreso": {
            "fecha": predicciones_diarias.idxmax(),
            "cantidad": float(predicciones_diarias.max())
        },
        "dia_menor_ingreso": {
            "fecha": predicciones_diarias.idxmin(),
            "cantidad": float(predicciones_diarias.min())
        }
    }

    return informe

def comparar_datos():
    """Compara los datos de la base de datos con los CSV"""
    print("\n=== COMPARACIÓN DE DATOS ===\n")
    
    # Obtener datos de la base de datos
    print("Obteniendo datos de la base de datos...")
    df_db = obtener_datos_historicos()
    if df_db is not None:
        df_db['Fecha'] = pd.to_datetime(df_db['Fecha'])
        print("\nDatos de la base de datos:")
        print(f"Total de registros: {len(df_db)}")
        print("\nDistribución por operación:")
        print(df_db.groupby('Operacion')['Cantidad'].agg(['count', 'sum', 'mean']))
        print("\nDistribución por tipo de usuario:")
        print(df_db.groupby('Tipo_usuario')['Cantidad'].agg(['count', 'sum', 'mean']))
    
    # Obtener datos de los CSV
    print("\nObteniendo datos de los CSV...")
    try:
        fact_table = pd.read_csv(os.path.join(DATA_DIR, 'fact_table.csv'), sep=';')
        dim_operaciones = pd.read_csv(os.path.join(DATA_DIR, 'dim_operaciones.csv'), sep=';')
        dim_usuarios = pd.read_csv(os.path.join(DATA_DIR, 'dim_usuarios.csv'), sep=';')
        
        # Unir tablas
        df_csv = fact_table.merge(dim_operaciones, on='Id_tipo_operacion', how='left')
        df_csv = df_csv.merge(dim_usuarios, 
                            left_on='Usuario_emisor', 
                            right_on='Id_usuario', 
                            how='left',
                            suffixes=('', '_emisor'))
        
        # Filtrar operaciones de ingreso
        operaciones_ingreso = [
            'Cuota mensual de socio',
            'Cuota variable',
            'Comisión por retirada',
            'Cuota de socio'
        ]
        df_csv = df_csv[df_csv['Operacion'].isin(operaciones_ingreso)]
        
        print("\nDatos de los CSV:")
        print(f"Total de registros: {len(df_csv)}")
        print("\nDistribución por operación:")
        print(df_csv.groupby('Operacion')['Cantidad'].agg(['count', 'sum', 'mean']))
        print("\nDistribución por tipo de usuario:")
        print(df_csv.groupby('Tipo_usuario')['Cantidad'].agg(['count', 'sum', 'mean']))
        
    except Exception as e:
        print(f"Error al leer los CSV: {str(e)}")

def entrenar_modelo():
    """Entrena el modelo con los datos actuales de la base de datos"""
    try:
        resultado = {
            "estado": "error",
            "mensaje": "",
            "detalles": {}
        }

        # Crear directorio de modelos si no existe
        models_dir = os.path.join(SCRIPT_DIR, 'models_history')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        print("Obteniendo datos para entrenamiento...")
        df = obtener_datos_historicos()
        if df is None:
            resultado["mensaje"] = "No se pudieron obtener los datos de la base de datos"
            return resultado

        # Preparar datos para entrenamiento
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Mes'] = df['Fecha'].dt.month
        df['DiaSemana'] = df['Fecha'].dt.dayofweek
        df['DiaDelMes'] = df['Fecha'].dt.day
        df['EsFinDeSemana'] = df['DiaSemana'].isin([5,6]).astype(int)
        df['Semana'] = ((df['DiaDelMes'] - 1) // 7 + 1).astype(int)

        # Calcular características adicionales
        ingresos_diarios = df.groupby(['Fecha', 'Operacion', 'Tipo_usuario'])['Cantidad'].agg({
            'Num_Operaciones': 'count',
            'Promedio_Operacion': 'mean'
        }).reset_index()

        # Preparar X e y
        X = ingresos_diarios[['Mes', 'DiaSemana', 'DiaDelMes', 'EsFinDeSemana', 'Semana', 
                             'Operacion', 'Tipo_usuario', 'Num_Operaciones', 'Promedio_Operacion']]
        y = ingresos_diarios['Cantidad']

        # Codificar variables categóricas
        categorias_operacion = sorted(df['Operacion'].unique())
        categorias_tipo_usuario = sorted(df['Tipo_usuario'].unique())
        
        X['Operacion'] = pd.Categorical(X['Operacion'], categories=categorias_operacion).codes
        X['Tipo_usuario'] = pd.Categorical(X['Tipo_usuario'], categories=categorias_tipo_usuario).codes

        # Entrenar modelo XGBoost
        import xgboost as xgb
        modelo = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        # Registrar tiempo de inicio del entrenamiento
        tiempo_inicio = pd.Timestamp.now()
        
        modelo.fit(X, y)
        
        # Registrar tiempo de fin del entrenamiento
        tiempo_fin = pd.Timestamp.now()
        duracion_entrenamiento = (tiempo_fin - tiempo_inicio).total_seconds()

        # Guardar modelo y características con versión
        caracteristicas = {
            'categorias_operacion': categorias_operacion,
            'categorias_tipo_usuario': categorias_tipo_usuario,
            'fecha_entrenamiento': tiempo_inicio.strftime('%Y-%m-%d %H:%M:%S'),
            'rango_datos': {
                'inicio': df['Fecha'].min().strftime('%Y-%m-%d'),
                'fin': df['Fecha'].max().strftime('%Y-%m-%d')
            }
        }

        # Generar nombre de versión basado en la fecha
        version = tiempo_inicio.strftime('%Y%m%d_%H%M%S')
        modelo_version_path = os.path.join(models_dir, f'modelo_ingresos_xgboost_{version}.pkl')
        caract_version_path = os.path.join(models_dir, f'caracteristicas_modelo_{version}.pkl')

        # Guardar versión del modelo
        with open(modelo_version_path, 'wb') as f:
            pickle.dump(modelo, f)
        
        with open(caract_version_path, 'wb') as f:
            pickle.dump(caracteristicas, f)

        # Guardar también como modelo actual
        modelo_path = os.path.join(SCRIPT_DIR, 'modelo_ingresos_xgboost.pkl')
        caract_path = os.path.join(SCRIPT_DIR, 'caracteristicas_modelo.pkl')

        with open(modelo_path, 'wb') as f:
            pickle.dump(modelo, f)
        
        with open(caract_path, 'wb') as f:
            pickle.dump(caracteristicas, f)

        # Preparar detalles del entrenamiento
        resultado["estado"] = "exitoso"
        resultado["mensaje"] = "Modelo entrenado y guardado exitosamente"
        resultado["detalles"] = {
            "fecha_entrenamiento": tiempo_inicio.strftime('%Y-%m-%d %H:%M:%S'),
            "duracion_entrenamiento_segundos": duracion_entrenamiento,
            "numero_registros_entrenamiento": len(df),
            "rango_fechas_datos": {
                "inicio": df['Fecha'].min().strftime('%Y-%m-%d'),
                "fin": df['Fecha'].max().strftime('%Y-%m-%d')
            },
            "categorias_operacion": categorias_operacion,
            "categorias_tipo_usuario": categorias_tipo_usuario,
            "parametros_modelo": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6
            },
            "archivos_generados": {
                "modelo_actual": modelo_path,
                "caracteristicas_actual": caract_path,
                "modelo_version": modelo_version_path,
                "caracteristicas_version": caract_version_path,
                "version": version
            }
        }

        print("Modelo entrenado y guardado exitosamente")
        return resultado

    except Exception as e:
        resultado["estado"] = "error"
        resultado["mensaje"] = f"Error entrenando el modelo: {str(e)}"
        return resultado

def predecir_mes_siguiente_csv():
    """Realiza predicciones para el próximo mes usando solo CSV"""
    try:
        # Cargar modelo y características
        modelo, caracteristicas = cargar_modelo_y_caracteristicas()
        stats_historicas = obtener_estadisticas_historicas()  # Esta función ya usa CSV
        
        # Determinar fecha inicio (mes siguiente al último dato)
        ultima_fecha = pd.Timestamp.now()
        fecha_inicio = (ultima_fecha.replace(day=1) + pd.DateOffset(months=1))
        dias_siguiente_mes = pd.date_range(
            start=fecha_inicio,
            end=fecha_inicio + pd.DateOffset(months=1) - pd.DateOffset(days=1),
            freq='D'
        )
        
        # Preparar características para predicción
        X_futuro = pd.DataFrame()
        X_futuro['Mes'] = dias_siguiente_mes.month
        X_futuro['DiaSemana'] = dias_siguiente_mes.dayofweek
        X_futuro['DiaDelMes'] = dias_siguiente_mes.day
        X_futuro['EsFinDeSemana'] = X_futuro['DiaSemana'].isin([5,6]).astype(int)
        X_futuro['Semana'] = ((X_futuro['DiaDelMes'] - 1) // 7 + 1).astype(int)
        
        # Generar predicciones
        predicciones_futuras = []
        for op in caracteristicas['categorias_operacion']:
            for user in caracteristicas['categorias_tipo_usuario']:
                X_temp = X_futuro.copy()
                
                # Codificar variables categóricas
                X_temp['Operacion'] = pd.Categorical([op] * len(X_futuro), 
                                                   categories=caracteristicas['categorias_operacion']).codes
                X_temp['Tipo_usuario'] = pd.Categorical([user] * len(X_futuro), 
                                                      categories=caracteristicas['categorias_tipo_usuario']).codes
                
                # Ajustar características según estadísticas históricas
                if stats_historicas is not None:
                    stats_op = stats_historicas[stats_historicas['Operacion'] == op]
                    stats_op_user = stats_op[stats_op['Tipo_usuario'] == user]
                    
                    if not stats_op_user.empty:
                        total_mensual = stats_op_user['Total'].values[0]
                        num_ops_mensual = stats_op_user['Num_Operaciones'].values[0]
                        promedio_por_op = stats_op_user['Promedio_Operacion'].values[0]
                        
                        total_diario = total_mensual / len(dias_siguiente_mes)
                        ops_por_dia = num_ops_mensual / len(dias_siguiente_mes)
                        
                        X_temp['Num_Operaciones'] = ops_por_dia
                        X_temp['Promedio_Operacion'] = promedio_por_op
                    else:
                        X_temp['Num_Operaciones'] = 0
                        X_temp['Promedio_Operacion'] = 0
                else:
                    X_temp['Num_Operaciones'] = 0
                    X_temp['Promedio_Operacion'] = 0
                
                # Predicción
                pred = modelo.predict(X_temp)
                pred = np.maximum(0, pred)
                
                # Ajustar predicciones según estadísticas históricas
                if stats_historicas is not None and not stats_op_user.empty:
                    total_mensual = stats_op_user['Total'].values[0]
                    factor_ajuste = total_mensual / pred.sum() if pred.sum() > 0 else 0
                    pred = pred * factor_ajuste
                
                # Guardar predicciones
                for dia, prediccion in zip(dias_siguiente_mes, pred):
                    if prediccion > 0:
                        predicciones_futuras.append({
                            'Fecha': dia.strftime('%d/%m/%Y'),
                            'Operacion': op,
                            'Tipo_usuario': user,
                            'Prediccion': float(prediccion)
                        })
        
        # Crear DataFrame con predicciones
        df_predicciones = pd.DataFrame(predicciones_futuras)
        
        if not df_predicciones.empty:
            predicciones_diarias = df_predicciones.groupby('Fecha')['Prediccion'].sum()
        else:
            predicciones_diarias = pd.Series(0, index=dias_siguiente_mes.strftime('%d/%m/%Y'))
        
        if predicciones_diarias.sum() == 0:
            return {"error": "Todas las predicciones son cero. Verifica el modelo y los datos de entrada."}
        
        # Generar informe usando la misma función que usa predecir_mes_siguiente_db
        informe = generar_informe(df_predicciones, predicciones_diarias)
        informe['fuente_datos'] = 'CSV'
        
        return informe
        
    except Exception as e:
        return {'error': str(e)}

def predecir_mes_siguiente_db():
    """Realiza predicciones para el próximo mes usando solo la base de datos"""
    try:
        # Cargar modelo y características
        modelo, caracteristicas = cargar_modelo_y_caracteristicas()
        
        # Obtener datos históricos de la base de datos
        df = obtener_datos_historicos()
        if df is None:
            raise Exception("No se pudieron obtener datos de la base de datos")
        
        # Determinar fecha inicio
        ultima_fecha = pd.Timestamp.now()
        fecha_inicio = (ultima_fecha.replace(day=1) + pd.DateOffset(months=1))
        dias_siguiente_mes = pd.date_range(
            start=fecha_inicio,
            end=fecha_inicio + pd.DateOffset(months=1) - pd.DateOffset(days=1),
            freq='D'
        )
        
        # Preparar características para predicción
        X_futuro = pd.DataFrame()
        X_futuro['Mes'] = dias_siguiente_mes.month
        X_futuro['DiaSemana'] = dias_siguiente_mes.dayofweek
        X_futuro['DiaDelMes'] = dias_siguiente_mes.day
        X_futuro['EsFinDeSemana'] = X_futuro['DiaSemana'].isin([5,6]).astype(int)
        X_futuro['Semana'] = ((X_futuro['DiaDelMes'] - 1) // 7 + 1).astype(int)
        
        # Calcular estadísticas de la base de datos
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Filtrar datos del mismo mes del año anterior
        mes_prediccion = fecha_inicio
        mes_historico = mes_prediccion - pd.DateOffset(years=1)
        mask_mes_historico = (df['Fecha'].dt.year == mes_historico.year) & \
                           (df['Fecha'].dt.month == mes_historico.month)
        df_mes_historico = df[mask_mes_historico]
        
        # Calcular estadísticas solo con los datos del mes histórico
        stats_db = df_mes_historico.groupby(['Operacion', 'Tipo_usuario']).agg({
            'Cantidad': ['sum', 'count', 'mean']
        }).reset_index()
        stats_db.columns = ['Operacion', 'Tipo_usuario', 'Total', 'Num_Operaciones', 'Promedio_Operacion']
        
        # Generar predicciones
        predicciones_futuras = []
        for op in caracteristicas['categorias_operacion']:
            for user in caracteristicas['categorias_tipo_usuario']:
                X_temp = X_futuro.copy()
                
                # Codificar variables categóricas
                X_temp['Operacion'] = pd.Categorical([op] * len(X_futuro), 
                                                   categories=caracteristicas['categorias_operacion']).codes
                X_temp['Tipo_usuario'] = pd.Categorical([user] * len(X_futuro), 
                                                      categories=caracteristicas['categorias_tipo_usuario']).codes
                
                # Ajustar características según estadísticas de la base de datos
                stats_op_user = stats_db[(stats_db['Operacion'] == op) & (stats_db['Tipo_usuario'] == user)]
                
                if not stats_op_user.empty:
                    total_mensual = stats_op_user['Total'].values[0]
                    num_ops_mensual = stats_op_user['Num_Operaciones'].values[0]
                    promedio_por_op = stats_op_user['Promedio_Operacion'].values[0]
                    
                    total_diario = total_mensual / len(dias_siguiente_mes)
                    ops_por_dia = num_ops_mensual / len(dias_siguiente_mes)
                    
                    X_temp['Num_Operaciones'] = ops_por_dia
                    X_temp['Promedio_Operacion'] = promedio_por_op
                else:
                    X_temp['Num_Operaciones'] = 0
                    X_temp['Promedio_Operacion'] = 0
                
                # Predicción
                pred = modelo.predict(X_temp)
                pred = np.maximum(0, pred)
                
                # Ajustar predicciones según estadísticas
                if not stats_op_user.empty:
                    total_mensual = stats_op_user['Total'].values[0]
                    factor_ajuste = total_mensual / pred.sum() if pred.sum() > 0 else 0
                    pred = pred * factor_ajuste
                
                # Guardar predicciones
                for dia, prediccion in zip(dias_siguiente_mes, pred):
                    if prediccion > 0:
                        predicciones_futuras.append({
                            'Fecha': dia.strftime('%d/%m/%Y'),
                            'Operacion': op,
                            'Tipo_usuario': user,
                            'Prediccion': float(prediccion)
                        })
        
        # Crear DataFrame con predicciones
        df_predicciones = pd.DataFrame(predicciones_futuras)
        
        if not df_predicciones.empty:
            predicciones_diarias = df_predicciones.groupby('Fecha')['Prediccion'].sum()
        else:
            predicciones_diarias = pd.Series(0, index=dias_siguiente_mes.strftime('%d/%m/%Y'))
        
        if predicciones_diarias.sum() == 0:
            raise Exception("No se generaron predicciones válidas")
        
        # Generar informe completo
        informe = generar_informe(df_predicciones, predicciones_diarias)
        informe['fuente_datos'] = 'Base de datos'
        
        return informe
        
    except Exception as e:
        return {'error': str(e)}

def main():
    """Función principal"""
    try:
        predicciones = predecir_mes_siguiente()
        
        if predicciones['resumen_general']['ingreso_total_predicho'] == 0:
            return {"error": "Todas las predicciones son cero. Verifica el modelo y los datos de entrada."}
        
        informe = generar_informe(pd.DataFrame(predicciones['predicciones_futuras']), 
                                pd.Series(predicciones['predicciones_diarias']))
        
        return informe
    
    except Exception as e:
        return {"error": str(e)}

def listar_versiones():
    """Lista todas las versiones disponibles del modelo"""
    try:
        models_dir = os.path.join(SCRIPT_DIR, 'models_history')
        if not os.path.exists(models_dir):
            return {
                "estado": "error",
                "mensaje": "No existe el directorio de histórico de modelos",
                "versiones": []
            }
        
        versiones = []
        for archivo in os.listdir(models_dir):
            if archivo.startswith('caracteristicas_modelo_') and archivo.endswith('.pkl'):
                version = archivo.replace('caracteristicas_modelo_', '').replace('.pkl', '')
                caract_path = os.path.join(models_dir, archivo)
                
                try:
                    with open(caract_path, 'rb') as f:
                        caracteristicas = pickle.load(f)
                    
                    versiones.append({
                        "version": version,
                        "fecha_entrenamiento": caracteristicas.get('fecha_entrenamiento', 'Desconocida'),
                        "rango_datos": caracteristicas.get('rango_datos', {
                            'inicio': 'Desconocido',
                            'fin': 'Desconocido'
                        })
                    })
                except Exception as e:
                    print(f"Error leyendo características de versión {version}: {str(e)}")
        
        return {
            "estado": "exitoso",
            "mensaje": f"Se encontraron {len(versiones)} versiones",
            "versiones": sorted(versiones, key=lambda x: x['version'], reverse=True)
        }
    
    except Exception as e:
        return {
            "estado": "error",
            "mensaje": f"Error listando versiones: {str(e)}",
            "versiones": []
        }

def revertir_modelo(version):
    """Revierte el modelo a una versión específica"""
    try:
        models_dir = os.path.join(SCRIPT_DIR, 'models_history')
        modelo_version_path = os.path.join(models_dir, f'modelo_ingresos_xgboost_{version}.pkl')
        caract_version_path = os.path.join(models_dir, f'caracteristicas_modelo_{version}.pkl')
        
        # Verificar que existan los archivos
        if not os.path.exists(modelo_version_path) or not os.path.exists(caract_version_path):
            return {
                "estado": "error",
                "mensaje": f"No se encuentra la versión {version} del modelo",
                "detalles": {}
            }
        
        # Cargar la versión antigua para verificar que sea válida
        try:
            with open(modelo_version_path, 'rb') as f:
                modelo = pickle.load(f)
            with open(caract_version_path, 'rb') as f:
                caracteristicas = pickle.load(f)
        except Exception as e:
            return {
                "estado": "error",
                "mensaje": f"Error al cargar la versión {version}: {str(e)}",
                "detalles": {}
            }
        
        # Copiar los archivos a la ubicación actual
        modelo_actual_path = os.path.join(SCRIPT_DIR, 'modelo_ingresos_xgboost.pkl')
        caract_actual_path = os.path.join(SCRIPT_DIR, 'caracteristicas_modelo.pkl')
        
        import shutil
        shutil.copy2(modelo_version_path, modelo_actual_path)
        shutil.copy2(caract_version_path, caract_actual_path)
        
        return {
            "estado": "exitoso",
            "mensaje": f"Modelo revertido exitosamente a la versión {version}",
            "detalles": {
                "version": version,
                "fecha_entrenamiento": caracteristicas.get('fecha_entrenamiento', 'Desconocida'),
                "rango_datos": caracteristicas.get('rango_datos', {
                    'inicio': 'Desconocido',
                    'fin': 'Desconocido'
                })
            }
        }
        
    except Exception as e:
        return {
            "estado": "error",
            "mensaje": f"Error al revertir el modelo: {str(e)}",
            "detalles": {}
        }

if __name__ == "__main__":
    print("Entrenando nuevo modelo con datos de la base de datos...")
    if entrenar_modelo():
        print("\nProbando predicciones con el nuevo modelo:")
        predicciones = main()
    else:
        print("No se pudo entrenar el modelo")