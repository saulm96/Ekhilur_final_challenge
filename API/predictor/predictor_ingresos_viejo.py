# predictor_ingresos.py

import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def cargar_modelo_y_caracteristicas():
    """Carga el modelo y las características guardadas"""
    archivos_requeridos = ['modelo_ingresos_xgboost.pkl', 'caracteristicas_modelo.pkl']
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            raise FileNotFoundError(f"No se encuentra el archivo {archivo}")
    
    try:
        with open('modelo_ingresos_xgboost.pkl', 'rb') as file:
            modelo = pickle.load(file)
        
        with open('caracteristicas_modelo.pkl', 'rb') as file:
            caracteristicas = pickle.load(file)
        
        return modelo, caracteristicas
    except Exception as e:
        raise Exception(f"Error al cargar archivos: {str(e)}")

def obtener_estadisticas_historicas():
    """Obtiene estadísticas históricas para ajustar predicciones"""
    try:
        # Cargar datos originales
        fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
        dim_operaciones = pd.read_csv('csv_base_datos/dim_operaciones.csv', sep=';')
        dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')
        dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')
        
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
        
        # Calcular ingresos diarios para estadísticas más detalladas
        ingresos_diarios = df_ingresos_mes_historico.groupby('Fecha')['Cantidad'].sum()
        
        # Imprimir resumen de estadísticas
        print("\n=== RESUMEN DE DATOS HISTÓRICOS ===")
        print(f"\nPeríodo histórico analizado: {mes_historico.strftime('%B %Y')}")
        print(f"(Mes y año para predecir: {mes_prediccion.strftime('%B %Y')})")
        
        print(f"\nResumen general:")
        total_mensual = ingresos_mensuales['Total'].sum()
        dias_en_mes = len(ingresos_diarios)  # Usar el número real de días con operaciones
        promedio_diario = ingresos_diarios.mean()
        print(f"- Ingreso total del mes: {total_mensual:,.2f}€")
        print(f"- Ingreso diario promedio: {promedio_diario:,.2f}€")
        print(f"- Día con mayor ingreso: {ingresos_diarios.idxmax().strftime('%d/%m/%Y')} ({ingresos_diarios.max():,.2f}€)")
        print(f"- Día con menor ingreso: {ingresos_diarios.idxmin().strftime('%d/%m/%Y')} ({ingresos_diarios.min():,.2f}€)")
        
        print("\nIngresos por tipo de operación:")
        ops_summary = ingresos_mensuales.groupby('Operacion').agg({
            'Total': 'sum',
            'Promedio_Operacion': 'mean',
            'Num_Operaciones': ['sum', 'std']
        }).round(2)
        ops_summary.columns = ['Total', 'Promedio', 'Num. Operaciones', 'Desv. Est.']
        print(ops_summary)
        
        print("\nIngresos por tipo de usuario:")
        user_summary = ingresos_mensuales.groupby('Tipo_usuario').agg({
            'Total': 'sum',
            'Promedio_Operacion': 'mean',
            'Num_Operaciones': ['sum', 'std']
        }).round(2)
        user_summary.columns = ['Total', 'Promedio', 'Num. Operaciones', 'Desv. Est.']
        print(user_summary)
        
        return ingresos_mensuales
        
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar estadísticas históricas: {str(e)}")
        return None

def predecir_mes_siguiente():
    """Realiza predicciones para el próximo mes"""
    # Cargar modelo y características
    modelo, caracteristicas = cargar_modelo_y_caracteristicas()
    stats_historicas = obtener_estadisticas_historicas()
    
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
    X_futuro['Semana'] = ((X_futuro['DiaDelMes'] - 1) // 7 + 1).astype(int)  # Semana del mes en lugar de semana del año
    
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
                    # Usar directamente los valores mensuales históricos
                    total_mensual = stats_op_user['Total'].values[0]
                    num_ops_mensual = stats_op_user['Num_Operaciones'].values[0]
                    promedio_por_op = stats_op_user['Promedio_Operacion'].values[0]
                    
                    # Distribuir el total mensual entre los días
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
                # Usar el total mensual histórico como objetivo
                total_mensual = stats_op_user['Total'].values[0]
                # Ajustar predicciones para que sumen el total mensual histórico
                factor_ajuste = total_mensual / pred.sum() if pred.sum() > 0 else 0
                pred = pred * factor_ajuste
            
            # Guardar predicciones
            for dia, prediccion in zip(dias_siguiente_mes, pred):
                if prediccion > 0:  # Solo guardar predicciones positivas
                    predicciones_futuras.append({
                        'Fecha': dia,
                        'Operacion': op,
                        'Tipo_usuario': user,
                        'Prediccion': prediccion
                    })
    
    # Crear DataFrame con predicciones
    df_predicciones = pd.DataFrame(predicciones_futuras)
    
    if not df_predicciones.empty:
        predicciones_diarias = df_predicciones.groupby('Fecha')['Prediccion'].sum()
    else:
        predicciones_diarias = pd.Series(0, index=dias_siguiente_mes)
    
    return df_predicciones, predicciones_diarias

def generar_informe(df_predicciones, predicciones_diarias):
    """Genera un informe detallado de las predicciones"""
    print("\n=== INFORME DE PREDICCIONES ===")
    print(f"\nPeríodo: {df_predicciones['Fecha'].min().strftime('%d/%m/%Y')} - {df_predicciones['Fecha'].max().strftime('%d/%m/%Y')}")
    
    print(f"\nResumen general:")
    print(f"- Ingreso total predicho: {predicciones_diarias.sum():,.2f}€")
    print(f"- Ingreso diario promedio: {predicciones_diarias.mean():,.2f}€")
    print(f"- Día con mayor ingreso: {predicciones_diarias.idxmax().strftime('%d/%m/%Y')} ({predicciones_diarias.max():,.2f}€)")
    print(f"- Día con menor ingreso: {predicciones_diarias.idxmin().strftime('%d/%m/%Y')} ({predicciones_diarias.min():,.2f}€)")
    
    print("\nPredicciones por tipo de operación:")
    ops_summary = df_predicciones.groupby('Operacion').agg({
        'Prediccion': ['sum', 'mean', 'count', 'std']
    }).round(2)
    ops_summary.columns = ['Total', 'Promedio', 'Num. Operaciones', 'Desv. Est.']
    print(ops_summary)
    
    print("\nPredicciones por tipo de usuario:")
    user_summary = df_predicciones.groupby('Tipo_usuario').agg({
        'Prediccion': ['sum', 'mean', 'count', 'std']
    }).round(2)
    user_summary.columns = ['Total', 'Promedio', 'Num. Operaciones', 'Desv. Est.']
    print(user_summary)

def predict():
    """Función principal"""
    try:
        print("Iniciando predicciones...")
        df_predicciones, predicciones_diarias = predecir_mes_siguiente()
        
        if predicciones_diarias.sum() == 0:
            print("ADVERTENCIA: Todas las predicciones son cero. Verifica el modelo y los datos de entrada.")
            return None, None
        
        generar_informe(df_predicciones, predicciones_diarias)
        
        return df_predicciones, predicciones_diarias
    
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        return None, None

if __name__ == "__main__":
    df_predicciones, predicciones_diarias = ()