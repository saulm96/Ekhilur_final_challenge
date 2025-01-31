import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import os
from flask import Flask, jsonify

app = Flask(__name__)

def cargar_modelo_y_caracteristicas():
    """Carga el modelo y las características guardadas"""
    path= os.getcwd()+"/predictor/"
    archivos_requeridos = [path+'modelo_ingresos_xgboost.pkl', path+'caracteristicas_modelo.pkl']
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            raise FileNotFoundError(f"No se encuentra el archivo {archivo}")
    
    try:
        with open(path+'modelo_ingresos_xgboost.pkl', 'rb') as file:
            modelo = pickle.load(file)
        
        with open(path+'caracteristicas_modelo.pkl', 'rb') as file:
            caracteristicas = pickle.load(file)
        
        return modelo, caracteristicas
    except Exception as e:
        raise Exception(f"Error al cargar archivos: {str(e)}")

def predecir_mes_siguiente():
    """Realiza predicciones para el próximo mes y devuelve un JSON"""
    modelo, caracteristicas = cargar_modelo_y_caracteristicas()
    
    # Determinar fecha inicio (mes siguiente al actual)
    fecha_actual = pd.Timestamp.now()
    fecha_inicio = (fecha_actual.replace(day=1) + pd.DateOffset(months=1))
    dias_siguiente_mes = pd.date_range(
        start=fecha_inicio,
        end=fecha_inicio + pd.DateOffset(months=1) - pd.DateOffset(days=1),
        freq='D'
    )
    
    X_futuro = pd.DataFrame()
    X_futuro['Mes'] = dias_siguiente_mes.month
    X_futuro['DiaSemana'] = dias_siguiente_mes.dayofweek
    X_futuro['DiaDelMes'] = dias_siguiente_mes.day
    X_futuro['EsFinDeSemana'] = X_futuro['DiaSemana'].isin([5,6]).astype(int)
    X_futuro['Semana'] = ((X_futuro['DiaDelMes'] - 1) // 7 + 1).astype(int)
    
    predicciones_futuras = []
    for op in caracteristicas['categorias_operacion']:
        for user in caracteristicas['categorias_tipo_usuario']:
            X_temp = X_futuro.copy()
            X_temp['Operacion'] = pd.Categorical([op] * len(X_futuro), categories=caracteristicas['categorias_operacion']).codes
            X_temp['Tipo_usuario'] = pd.Categorical([user] * len(X_futuro), categories=caracteristicas['categorias_tipo_usuario']).codes
            
            pred = modelo.predict(X_temp)
            pred = np.maximum(0, pred)
            
            for dia, prediccion in zip(dias_siguiente_mes, pred):
                if prediccion > 0:
                    predicciones_futuras.append({
                        'Fecha': dia.strftime('%Y-%m-%d'),
                        'Operacion': op,
                        'Tipo_usuario': user,
                        'Prediccion': float(prediccion)
                    })
    
    df_predicciones = pd.DataFrame(predicciones_futuras)
    
    if not df_predicciones.empty:
        predicciones_diarias = df_predicciones.groupby('Fecha')['Prediccion'].sum().to_dict()
    else:
        predicciones_diarias = {fecha.strftime('%Y-%m-%d'): 0 for fecha in dias_siguiente_mes}
    
    return {
        "predicciones": predicciones_futuras,
        "resumen": {
            "total_mes": sum(predicciones_diarias.values()),
            "promedio_diario": np.mean(list(predicciones_diarias.values())),
            "dia_max_ingreso": max(predicciones_diarias, key=predicciones_diarias.get),
            "dia_min_ingreso": min(predicciones_diarias, key=predicciones_diarias.get)
        },
        "predicciones_diarias": predicciones_diarias
    }
'''
@app.route('/predict', methods=['GET'])
def predictor():
    resultado = predecir_mes_siguiente()
    return jsonify(resultado)


'''

if __name__ == "__main__":
   print("hola")
   print(predecir_mes_siguiente())