import subprocess
import json
import socket
from pprint import pprint

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
    cmd = ['curl', '-s', f'http://localhost:5000/predict/{endpoint}']
    print(f"\nEjecutando: {' '.join(cmd)}")
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    
    if resultado.returncode != 0:
        print(f"❌ Error al ejecutar curl: {resultado.stderr}")
        return None
        
    try:
        return json.loads(resultado.stdout)
    except json.JSONDecodeError as e:
        print("❌ Error al decodificar JSON:")
        print(f"Respuesta raw: {resultado.stdout}")
        print(f"Error: {str(e)}")
        return None

def compare_predictions(pred_db, pred_csv):
    """
    Compara las predicciones de ambas fuentes
    """
    print("\n=== COMPARACIÓN DE PREDICCIONES ===")
    
    # Comparar fuentes de datos
    print("\nFuentes de datos:")
    print(f"DB: {pred_db.get('fuente_datos', 'No especificada')}")
    print(f"CSV: {pred_csv.get('fuente_datos', 'No especificada')}")
    
    # Comparar datos históricos
    print("\nDatos históricos:")
    hist_db = pred_db.get('datos_historicos', {}).get('resumen_general', {})
    hist_csv = pred_csv.get('datos_historicos', {}).get('resumen_general', {})
    
    print(f"DB - Total: {hist_db.get('ingreso_total', 'N/A')}€")
    print(f"CSV - Total: {hist_csv.get('ingreso_total', 'N/A')}€")
    
    # Comparar predicciones
    print("\nPredicciones:")
    pred_db_total = pred_db.get('predicciones', {}).get('resumen_general', {}).get('ingreso_total_predicho', 'N/A')
    pred_csv_total = pred_csv.get('predicciones', {}).get('resumen_general', {}).get('ingreso_total_predicho', 'N/A')
    
    print(f"DB - Total predicho: {pred_db_total}€")
    print(f"CSV - Total predicho: {pred_csv_total}€")
    
    # Calcular diferencia si es posible
    if isinstance(pred_db_total, (int, float)) and isinstance(pred_csv_total, (int, float)):
        diff = abs(pred_db_total - pred_csv_total)
        print(f"\nDiferencia absoluta: {diff:.2f}€")
        if pred_db_total > 0:
            diff_percent = (diff / pred_db_total) * 100
            print(f"Diferencia porcentual: {diff_percent:.2f}%")

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
        # Obtener predicciones de ambas fuentes
        pred_db = get_predictions('db')
        pred_csv = get_predictions('csv')
        
        if pred_db and pred_csv:
            compare_predictions(pred_db, pred_csv)
            
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")

if __name__ == "__main__":
    test_endpoints() 