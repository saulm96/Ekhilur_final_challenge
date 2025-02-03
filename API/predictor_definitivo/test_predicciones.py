import subprocess
import json
import socket
from pprint import pprint
from datetime import datetime
import pandas as pd
import requests
import numpy as np
import sys
import os

# Añadir el directorio padre al path para poder importar el módulo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_server(host="localhost", port=5000):
    """
    Verifica si el servidor está escuchando en el puerto especificado
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def get_predictions(endpoint):
    """
    Obtiene predicciones del endpoint especificado
    """
    url = f'http://localhost:5000/predict/{endpoint}'
    print(f"\nConsultando: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al hacer la petición: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print("❌ Error al decodificar JSON:")
        print(f"Respuesta raw: {response.text}")
        print(f"Error: {str(e)}")
        return None

def analyze_operation_predictions(pred_db, pred_csv):
    """
    Analiza las predicciones por tipo de operación
    """
    print("\n=== ANÁLISIS POR TIPO DE OPERACIÓN ===")
    
    # Debug: Mostrar estructura de datos completa
    print("\nEstructura de datos recibida:")
    print("pred_db:", pred_db)
    print("\nEstructura de datos históricos:")
    hist_data = pred_db.get('datos_historicos', {})
    print("hist_data:", hist_data)
    print("\nEstructura de predicciones:")
    pred_data = pred_db.get('predicciones', {})
    print("pred_data:", pred_data)
    
    # Obtener período
    print("\nPeríodo analizado:")
    hist_periodo = hist_data.get('periodo', {})
    pred_periodo = pred_data.get('periodo', {})
    
    print("Histórico:", hist_periodo.get('mes_analizado', 'N/A'))
    print("Predicción:", pred_periodo.get('mes_prediccion', 'N/A'))
    
    # Obtener totales
    print("\nResumen general:")
    hist_total = hist_data.get('resumen_general', {}).get('ingreso_total', 0)
    pred_total = pred_data.get('resumen_general', {}).get('ingreso_total_predicho', 0)
    
    print(f"Total histórico (2024): {hist_total:>8.2f}€")
    print(f"Total predicho (2025):  {pred_total:>8.2f}€")
    
    if hist_total > 0:
        variacion = ((pred_total - hist_total) / hist_total) * 100
        print(f"Variación: {variacion:>+.1f}%")
    
    # Analizar predicciones por operación
    print("\nAnálisis por operación:")
    ops_pred = pred_data.get('predicciones_por_operacion', {})
    if ops_pred:
        print("Operaciones encontradas:", list(ops_pred.keys()))
        
        print("\nDetalle por operación:")
        print("=" * 100)
        print(f"{'Tipo de Operación':<25} {'Total':<12} {'Promedio/Op':<12} {'Ops/día':<8} {'% del Total':<10}")
        print("-" * 100)
        
        for op, datos in sorted(ops_pred.items(), key=lambda x: x[1].get('total', 0), reverse=True):
            total = datos.get('total', 0)
            promedio = datos.get('promedio', 0)
            num_ops = datos.get('num_operaciones', 0)
            ops_dia = num_ops / 31 if num_ops > 0 else 0
            pct_total = (total / pred_total * 100) if pred_total > 0 else 0
            
            print(f"{op:<25} {total:>8.2f}€ {promedio:>8.2f}€ {ops_dia:>8.1f} {pct_total:>8.1f}%")
    else:
        print("No se encontraron predicciones por operación")
    
    # Analizar predicciones por usuario
    print("\nAnálisis por usuario:")
    users_pred = pred_data.get('predicciones_por_usuario', {})
    if users_pred:
        print("Usuarios encontrados:", list(users_pred.keys()))
        
        print("\nDetalle por usuario:")
        print("=" * 100)
        print(f"{'Tipo de Usuario':<25} {'Total':<12} {'Promedio/Op':<12} {'Ops/día':<8} {'% del Total':<10}")
        print("-" * 100)
        
        for user, datos in sorted(users_pred.items(), key=lambda x: x[1].get('total', 0), reverse=True):
            total = datos.get('total', 0)
            promedio = datos.get('promedio', 0)
            num_ops = datos.get('num_operaciones', 0)
            ops_dia = num_ops / 31 if num_ops > 0 else 0
            pct_total = (total / pred_total * 100) if pred_total > 0 else 0
            
            print(f"{user:<25} {total:>8.2f}€ {promedio:>8.2f}€ {ops_dia:>8.1f} {pct_total:>8.1f}%")
    else:
        print("No se encontraron predicciones por usuario")

def test_endpoints():
    """
    Prueba ambos endpoints y compara resultados
    """
    print("\n=== PROBANDO ENDPOINTS DE PREDICCIÓN ===")
    
    # Verificar si el servidor está corriendo
    if not check_server(port=5000):
        print("❌ Error: El servidor no está accesible en el puerto 5000")
        return
    
    try:
        # Probar endpoint principal
        print("\nProbando endpoint principal:")
        url = 'http://localhost:5000/predict'
        try:
            response = requests.get(url)
            response.raise_for_status()
            pred_main = response.json()
            print("Estructura de datos del endpoint principal:")
            pprint(pred_main)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al hacer la petición: {str(e)}")
            return
        
        # Obtener predicciones de ambas fuentes
        pred_db = get_predictions('db')
        pred_csv = get_predictions('csv')
        
        if pred_db and pred_csv:
            analyze_operation_predictions(pred_db, pred_csv)
            
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        print(traceback.format_exc())

def probar_predicciones():
    """Prueba las predicciones usando CSV"""
    print("=== PROBANDO PREDICCIONES ===")
    
    # Obtener predicciones usando CSV
    print("Ejecutando predicciones...")
    from predictor_definitivo.predictor_ingresos import predecir_mes_siguiente_csv
    informe = predecir_mes_siguiente_csv()
    
    # Verificar si hay errores
    if 'error' in informe:
        print("\nError en predicciones:", informe['error'])
        return
    
    # Mostrar datos históricos
    print("\nDatos Históricos:")
    print("-" * 50)
    hist_data = informe['datos_historicos']
    print(f"Mes analizado: {hist_data['periodo']['mes_analizado']}")
    hist_resumen = hist_data['resumen_general']
    print(f"Total histórico: {hist_resumen['ingreso_total']:,.2f}€")
    print(f"Promedio diario histórico: {hist_resumen['ingreso_diario_promedio']:,.2f}€")
    
    # Mostrar predicciones
    print("\nPredicciones:")
    print("-" * 50)
    pred_data = informe['predicciones']
    print(f"Período: {pred_data['periodo']['inicio']} - {pred_data['periodo']['fin']}")
    pred_resumen = pred_data['resumen_general']
    print(f"Total predicho: {pred_resumen['ingreso_total_predicho']:,.2f}€")
    print(f"Promedio diario predicho: {pred_resumen['ingreso_diario_promedio']:,.2f}€")
    
    # Calcular variación
    variacion = ((pred_resumen['ingreso_total_predicho'] - hist_resumen['ingreso_total']) / 
                hist_resumen['ingreso_total'] * 100)
    print(f"\nVariación respecto al año anterior: {variacion:+.1f}%")
    
    print("\nFuente de datos:", informe['fuente_datos'])

if __name__ == "__main__":
    probar_predicciones() 