from config_db import DatabaseConnection, Queries, Visualizations, set_plot_style
import pandas as pd

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("Probando conexión a la base de datos...")
    conn = DatabaseConnection.get_connection()
    if conn is not None:
        print("✓ Conexión exitosa")
        conn.close()
    else:
        print("✗ Error en la conexión")

def test_table_structure():
    """Prueba la estructura de las tablas"""
    print("\nProbando estructura de las tablas...")
    
    # Consulta para ver la estructura de fact_table
    query_fact = """
    DESCRIBE fact_table;
    """
    
    # Consulta para ver la estructura de dim_operaciones
    query_dim = """
    DESCRIBE dim_operaciones;
    """
    
    print("\nEstructura de fact_table:")
    result = DatabaseConnection.ejecutar_query(query_fact)
    if result is not None:
        print(result)
    else:
        print("✗ No se pudo obtener la estructura de fact_table")
    
    print("\nEstructura de dim_operaciones:")
    result = DatabaseConnection.ejecutar_query(query_dim)
    if result is not None:
        print(result)
    else:
        print("✗ No se pudo obtener la estructura de dim_operaciones")

def test_sample_data():
    """Prueba la obtención de datos de muestra"""
    print("\nProbando consulta de datos de muestra...")
    
    # Consulta simple para ver algunos registros
    query = """
    SELECT * FROM dim_operaciones LIMIT 5;
    """
    
    result = DatabaseConnection.ejecutar_query(query)
    if result is not None:
        print("\nPrimeros 5 registros de dim_operaciones:")
        print(result)
    else:
        print("✗ No se pudieron obtener datos de muestra")

if __name__ == "__main__":
    print("=== Iniciando pruebas de config_db.py ===\n")
    
    # Probar conexión
    test_database_connection()
    
    # Probar estructura de tablas
    test_table_structure()
    
    # Probar datos de muestra
    test_sample_data()
    
    print("\n=== Fin de las pruebas ===") 