from flask import Flask, jsonify
import pandas as pd
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_users():
    dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')
    dim_usuarios['fecha_alta'] = pd.to_datetime(dim_usuarios['Id_fecha_alta'], format='%Y%m%d')
    dim_usuarios['Categoria_Agrupada'] = dim_usuarios['Tipo_usuario'].map(
        lambda x: 'Empresas' if x in ['autonomo', 'Empresa'] else x
    )

    nov_2024_mask = dim_usuarios['fecha_alta'] <= '2024-11-30'
    dec_2024_mask = dim_usuarios['fecha_alta'] <= '2024-12-31'
    
    nov_data = dim_usuarios[nov_2024_mask]
    dec_data = dim_usuarios[dec_2024_mask]
    
    nov_totals = nov_data['Categoria_Agrupada'].value_counts()
    dec_totals = dec_data['Categoria_Agrupada'].value_counts()

    results = []
    for category in ['usuario', 'Empresas']:
        nov_count = nov_totals.get(category, 0)
        dec_count = dec_totals.get(category, 0)
        difference = dec_count - nov_count
        percentage = (difference / nov_count) * 100 if nov_count > 0 else float('inf')
        
        results.append({
            'Categoria': category,
            'Total_Noviembre_2024': int(nov_count),
            'Total_Diciembre_2024': int(dec_count),
            'Incremento_Absoluto': int(difference),
            'Incremento_Porcentual': f"{percentage:.1f}%" if percentage != float('inf') else "N/A"
        })
    
    return results

def analyze_monthly_average():
    fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
    dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')
    dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

    usuarios_filtrados = dim_usuarios[dim_usuarios['Tipo_usuario'] == 'usuario']['Id_usuario'].unique()
    fechas_2024 = dim_fecha[dim_fecha['Ano'] == 2024]['Id_fecha'].unique()

    operaciones_2024 = fact_table[
        (fact_table['Id_tipo_operacion'].isin([1, 7])) & 
        (fact_table['Usuario_emisor'].isin(usuarios_filtrados)) &
        (fact_table['Id_fecha'].isin(fechas_2024))
    ]

    operaciones_con_fecha = operaciones_2024.merge(
        dim_fecha[['Id_fecha', 'Mes']], 
        on='Id_fecha',
        how='left'
    )

    gasto_mensual = operaciones_con_fecha.groupby(['Usuario_emisor', 'Mes'])['Cantidad'].sum().round(2)
    gasto_medio_mensual = gasto_mensual.groupby('Usuario_emisor').mean()
    
    return {'gasto_medio_mensual': float(gasto_medio_mensual.mean())}

def analyze_monthly_savings():
    fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
    dim_usuarios = pd.read_csv('csv_base_datos/dim_usuarios.csv', sep=';')
    dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

    usuarios_filtrados = dim_usuarios[dim_usuarios['Tipo_usuario'] == 'usuario']['Id_usuario'].unique()
    fechas_2024 = dim_fecha[dim_fecha['Ano'] == 2024]['Id_fecha'].unique()

    operaciones_2024 = fact_table[
        (fact_table['Id_tipo_operacion'].isin([0, 4])) & 
        (fact_table['Usuario_receptor'].isin(usuarios_filtrados)) &
        (fact_table['Id_fecha'].isin(fechas_2024))
    ]

    operaciones_con_fecha = operaciones_2024.merge(
        dim_fecha[['Id_fecha', 'Mes']], 
        on='Id_fecha',
        how='left'
    )

    ahorro_mensual = operaciones_con_fecha.groupby(['Usuario_receptor', 'Mes'])['Cantidad'].sum().round(2)
    ahorro_medio_mensual = ahorro_mensual.groupby('Usuario_receptor').mean()
    
    return {'ahorro_medio_mensual': float(ahorro_medio_mensual.mean())}

def analyze_total_simple():
    fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
    dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

    ultimo_mes = dim_fecha[
        (dim_fecha['Ano'] == 2024) & 
        (dim_fecha['Mes'] == 12)
    ]['Id_fecha'].unique()

    operaciones_filtradas = fact_table[
        (fact_table['Id_tipo_operacion'].isin([1, 7])) & 
        (fact_table['Id_fecha'].isin(ultimo_mes))
    ]

    return {
        'numero_total_operaciones': len(operaciones_filtradas),
        'importe_total': float(operaciones_filtradas['Cantidad'].sum())
    }

def analyze_cash_flow():
    fact_table = pd.read_csv('csv_base_datos/fact_table.csv', sep=';')
    dim_fecha = pd.read_csv('csv_base_datos/dim_fecha.csv', sep=';')

    fechas_2024 = dim_fecha[dim_fecha['Ano'] == 2024]['Id_fecha'].unique()

    operaciones_2024 = fact_table[
        (fact_table['Id_tipo_operacion'].isin([2, 6, 12])) & 
        (fact_table['Id_fecha'].isin(fechas_2024))
    ]

    operaciones_con_fecha = operaciones_2024.merge(
        dim_fecha[['Id_fecha', 'Mes']], 
        on='Id_fecha',
        how='left'
    )

    entradas = operaciones_con_fecha[operaciones_con_fecha['Id_tipo_operacion'] == 6]
    salidas = operaciones_con_fecha[operaciones_con_fecha['Id_tipo_operacion'].isin([2, 12])]

    entradas_por_mes = entradas.groupby('Mes')['Cantidad'].sum().round(2)
    salidas_por_mes = salidas.groupby('Mes')['Cantidad'].sum().round(2)

    resultados_mensuales = []
    for mes in range(1, 13):
        entrada = float(entradas_por_mes.get(mes, 0))
        salida = float(salidas_por_mes.get(mes, 0))
        resultados_mensuales.append({
            'mes': mes,
            'entradas': entrada,
            'salidas': salida
        })

    return {
        'flujo_mensual': resultados_mensuales,
        'total_entradas': float(entradas['Cantidad'].sum()),
        'total_salidas': float(salidas['Cantidad'].sum())
    }

@app.route('/analisis', methods=['GET'])
def get_analysis():
    try:
        logger.info("Iniciando análisis...")
        
        logger.debug("Ejecutando analyze_users()...")
        users_result = analyze_users()
        
        logger.debug("Ejecutando analyze_monthly_average()...")
        average_result = analyze_monthly_average()
        
        logger.debug("Ejecutando analyze_monthly_savings()...")
        savings_result = analyze_monthly_savings()
        
        logger.debug("Ejecutando analyze_total_simple()...")
        total_result = analyze_total_simple()
        
        logger.debug("Ejecutando analyze_cash_flow()...")
        cash_flow_result = analyze_cash_flow()
        
        results = {
            'analisis_usuarios': users_result,
            'promedio_mensual': average_result,
            'ahorro_mensual': savings_result,
            'total_diciembre': total_result,
            'flujo_efectivo': cash_flow_result,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Guardando resultados en JSON...")
        try:
            with open('resultados_analisis.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as file_error:
            logger.error(f"Error al guardar el archivo JSON: {str(file_error)}")
            # Continuamos aunque falle el guardado del archivo
        
        logger.info("Análisis completado exitosamente")
        return jsonify(results)
    
    except Exception as e:
        error_msg = f"Error durante el análisis: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'error': error_msg,
            'tipo_error': type(e).__name__,
            'detalles': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'mensaje': 'API de análisis funcionando',
        'endpoints': {
            '/analisis': 'Obtener todos los análisis',
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
