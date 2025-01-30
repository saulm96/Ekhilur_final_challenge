import pandas as pd

# Read the CSV files
dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')

# Convert Id_fecha_alta to datetime
dim_usuarios['fecha_alta'] = pd.to_datetime(dim_usuarios['Id_fecha_alta'], format='%Y%m%d')

# Create a new column for grouped categories
dim_usuarios['Categoria_Agrupada'] = dim_usuarios['Tipo_usuario'].map(
    lambda x: 'Empresas' if x in ['autonomo', 'Empresa'] else x
)

# Calculate total users up to November 2024 (including November)
nov_2024_mask = dim_usuarios['fecha_alta'] <= '2024-11-30'
nov_data = dim_usuarios[nov_2024_mask]
nov_totals = nov_data['Categoria_Agrupada'].value_counts()

# Calculate total users up to December 2024 (including December)
dec_2024_mask = dim_usuarios['fecha_alta'] <= '2024-12-31'
dec_data = dim_usuarios[dec_2024_mask]
dec_totals = dec_data['Categoria_Agrupada'].value_counts()

# Calculate differences and percentages
results = []

for category in ['usuario', 'Empresas']:
    nov_count = nov_totals.get(category, 0)
    dec_count = dec_totals.get(category, 0)
    
    difference = dec_count - nov_count
    if nov_count > 0:
        percentage = (difference / nov_count) * 100
    else:
        percentage = float('inf') if dec_count > 0 else 0
        
    results.append({
        'Categoria': category,
        'Total_Noviembre_2024': nov_count,
        'Total_Diciembre_2024': dec_count,
        'Incremento_Absoluto': difference,
        'Incremento_Porcentual': f"{percentage:.1f}%" if percentage != float('inf') else "N/A"
    })

# Convert to DataFrame and display results
results_df = pd.DataFrame(results)

# Print detailed information
print("\nAnálisis del total acumulado de usuarios y empresas hasta cada mes:")
print("=" * 100)
print(results_df.to_string(index=False))

# Additional verification
print("\nVerificación de totales por tipo original:")
print("Noviembre:", nov_data['Tipo_usuario'].value_counts().to_dict())
print("Diciembre:", dec_data['Tipo_usuario'].value_counts().to_dict()) 