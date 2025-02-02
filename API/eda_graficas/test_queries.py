from config_db import DatabaseConnection, Queries

def test_queries():
    """Prueba todas las queries definidas"""
    print("=== Probando queries actualizadas ===\n")
    
    # Probar get_operaciones_summary
    print("1. Probando get_operaciones_summary:")
    result = DatabaseConnection.ejecutar_query(Queries.get_operaciones_summary())
    if result is not None:
        print("✓ Query ejecutada correctamente")
        print("\nPrimeras filas del resultado:")
        print(result.head())
    else:
        print("✗ Error en la query")
    
    # Probar get_temporal_analysis
    print("\n2. Probando get_temporal_analysis:")
    result = DatabaseConnection.ejecutar_query(Queries.get_temporal_analysis())
    if result is not None:
        print("✓ Query ejecutada correctamente")
        print("\nPrimeras filas del resultado:")
        print(result.head())
    else:
        print("✗ Error en la query")
    
    # Probar get_user_patterns
    print("\n3. Probando get_user_patterns:")
    result = DatabaseConnection.ejecutar_query(Queries.get_user_patterns())
    if result is not None:
        print("✓ Query ejecutada correctamente")
        print("\nPrimeras filas del resultado:")
        print(result.head())
    else:
        print("✗ Error en la query")
    
    # Probar get_flow_analysis
    print("\n4. Probando get_flow_analysis:")
    result = DatabaseConnection.ejecutar_query(Queries.get_flow_analysis())
    if result is not None:
        print("✓ Query ejecutada correctamente")
        print("\nPrimeras filas del resultado:")
        print(result.head())
    else:
        print("✗ Error en la query")

if __name__ == "__main__":
    test_queries() 