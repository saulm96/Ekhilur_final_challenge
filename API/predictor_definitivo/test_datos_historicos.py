from predictor_ingresos import obtener_datos_historicos
import pandas as pd

def test_datos_historicos():
    """
    Prueba la función obtener_datos_historicos() y analiza los resultados
    """
    print("\n=== PRUEBA DE OBTENCIÓN DE DATOS HISTÓRICOS ===")
    
    # Obtener datos
    print("\nObteniendo datos de la base de datos...")
    df = obtener_datos_historicos()
    
    if df is None:
        print("❌ Error: No se pudieron obtener los datos históricos")
        return
    
    if not isinstance(df, pd.DataFrame):
        print("❌ Error: Los datos obtenidos no son un DataFrame")
        return
    
    # Analizar resultados
    print("\n✅ Datos obtenidos exitosamente!")
    print(f"\nInformación del DataFrame:")
    print(f"Total de registros: {len(df)}")
    print(f"Columnas disponibles: {', '.join(df.columns)}")
    
    # Análisis temporal
    print(f"\nRango de fechas:")
    print(f"Desde: {df['Fecha'].min()}")
    print(f"Hasta: {df['Fecha'].max()}")
    
    # Análisis por tipo de operación
    print(f"\nRegistros por tipo de operación:")
    print(df['Operacion'].value_counts())
    
    # Análisis por tipo de usuario
    print(f"\nRegistros por tipo de usuario:")
    print(df['Tipo_usuario'].value_counts())
    
    # Análisis de cantidades
    print(f"\nEstadísticas de cantidades:")
    print(f"Total: {df['Cantidad'].sum():.2f} €")
    print(f"Promedio: {df['Cantidad'].mean():.2f} €")
    print(f"Mínimo: {df['Cantidad'].min():.2f} €")
    print(f"Máximo: {df['Cantidad'].max():.2f} €")

if __name__ == "__main__":
    test_datos_historicos() 