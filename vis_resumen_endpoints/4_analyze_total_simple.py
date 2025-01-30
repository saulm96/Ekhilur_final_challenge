import pandas as pd

# Leer los archivos CSV
print("Cargando datos...")
fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

# Filtrar el último mes (diciembre 2024)
ultimo_mes = dim_fecha[
    (dim_fecha['Ano'] == 2024) & 
    (dim_fecha['Mes'] == 12)
]['Id_fecha'].unique()

# Filtrar operaciones tipo 1 y 7 del último mes
operaciones_filtradas = fact_table[
    (fact_table['Id_tipo_operacion'].isin([1, 7])) & 
    (fact_table['Id_fecha'].isin(ultimo_mes))
]

# Calcular y mostrar totales
print(f"Número total de operaciones: {len(operaciones_filtradas):,}")
print(f"Importe total: {operaciones_filtradas['Cantidad'].sum():,.2f}€") 