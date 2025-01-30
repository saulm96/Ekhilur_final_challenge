import pandas as pd

# Leer los archivos CSV
print("Cargando datos...")
fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')
dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

# Filtrar usuarios tipo 'usuario'
usuarios_filtrados = dim_usuarios[dim_usuarios['Tipo_usuario'] == 'usuario']['Id_usuario'].unique()

# Filtrar operaciones del 2024
fechas_2024 = dim_fecha[dim_fecha['Ano'] == 2024]['Id_fecha'].unique()

# Filtrar la tabla de hechos
operaciones_2024 = fact_table[
    (fact_table['Id_tipo_operacion'].isin([1, 7])) & 
    (fact_table['Usuario_emisor'].isin(usuarios_filtrados)) &
    (fact_table['Id_fecha'].isin(fechas_2024))
]

# Añadir información de mes a las operaciones
operaciones_con_fecha = operaciones_2024.merge(
    dim_fecha[['Id_fecha', 'Mes']], 
    on='Id_fecha',
    how='left'
)

# Calcular gasto por usuario y mes
gasto_mensual = operaciones_con_fecha.groupby(['Usuario_emisor', 'Mes'])['Cantidad'].sum().round(2)

# Calcular media mensual por usuario
gasto_medio_mensual = gasto_mensual.groupby('Usuario_emisor').mean()

# Calcular y mostrar la media general
print(f"Gasto medio mensual por usuario: {gasto_medio_mensual.mean():.2f}€") 