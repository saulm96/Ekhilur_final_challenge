import pandas as pd

# Leer los archivos CSV
print("Cargando datos...")
fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

# Filtrar operaciones del 2024
fechas_2024 = dim_fecha[dim_fecha['Ano'] == 2024]['Id_fecha'].unique()

# Filtrar operaciones de entrada (tipo 6) y salida (tipos 2 y 12)
operaciones_2024 = fact_table[
    (fact_table['Id_tipo_operacion'].isin([2, 6, 12])) & 
    (fact_table['Id_fecha'].isin(fechas_2024))
]

# Añadir información de mes a las operaciones
operaciones_con_fecha = operaciones_2024.merge(
    dim_fecha[['Id_fecha', 'Mes']], 
    on='Id_fecha',
    how='left'
)

# Separar entradas y salidas
entradas = operaciones_con_fecha[operaciones_con_fecha['Id_tipo_operacion'] == 6]
salidas = operaciones_con_fecha[operaciones_con_fecha['Id_tipo_operacion'].isin([2, 12])]

# Calcular totales por mes
entradas_por_mes = entradas.groupby('Mes')['Cantidad'].sum().round(2)
salidas_por_mes = salidas.groupby('Mes')['Cantidad'].sum().round(2)

# Crear DataFrame con resultados mensuales
resultados_mensuales = pd.DataFrame({
    'Entradas': entradas_por_mes,
    'Salidas': salidas_por_mes
})

# Calcular totales anuales
total_entradas = entradas['Cantidad'].sum()
total_salidas = salidas['Cantidad'].sum()

# Mostrar resultados
print("\nFlujo de dinero mensual 2024:")
print("=" * 60)
print("Mes    Entradas (€)    Salidas (€)")
print("-" * 60)
for mes in range(1, 13):
    entrada = resultados_mensuales.loc[mes, 'Entradas'] if mes in resultados_mensuales.index else 0
    salida = resultados_mensuales.loc[mes, 'Salidas'] if mes in resultados_mensuales.index else 0
    print(f"{mes:2d}    {entrada:12,.2f}    {salida:10,.2f}")

print("\nTotales anuales:")
print("=" * 60)
print(f"Total Entradas: {total_entradas:,.2f}€")
print(f"Total Salidas:  {total_salidas:,.2f}€")
print(f"Balance Neto:   {(total_entradas - total_salidas):,.2f}€") 