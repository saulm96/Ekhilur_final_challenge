import os
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt

# Cargar variables de entorno
load_dotenv()

class DatabaseConnection:
    @staticmethod
    def get_connection():
        """Establece la conexión con la base de datos"""
        try:
            connection = mysql.connector.connect(
                host='localhost',
                port=3308,
                user='user',
                password='userpassword',
                database='ekhilur'
            )
            return connection
        except mysql.connector.Error as err:
            print(f"Error de conexión: {err}")
            return None

    @staticmethod
    def ejecutar_query(query):
        """Ejecuta una query SQL y devuelve los resultados como DataFrame"""
        conn = DatabaseConnection.get_connection()
        if conn is not None:
            try:
                return pd.read_sql_query(query, conn)
            except Exception as e:
                print(f"Error ejecutando query: {e}")
                return None
            finally:
                conn.close()
        return None

class Queries:
    """Clase que contiene todas las queries SQL necesarias para el análisis"""
    
    @staticmethod
    def get_operaciones_summary():
        return """
        SELECT 
            o.Operacion,
            COUNT(*) as total_operaciones,
            SUM(f.Cantidad) as suma_total,
            AVG(f.Cantidad) as promedio_importe
        FROM fact_table f
        JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        GROUP BY o.Operacion
        ORDER BY suma_total DESC;
        """
    
    @staticmethod
    def get_temporal_analysis():
        return """
        SELECT 
            f.Id_fecha as fecha,
            o.Operacion,
            SUM(f.Cantidad) as suma_diaria
        FROM fact_table f
        JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        GROUP BY fecha, o.Operacion
        ORDER BY fecha;
        """
    
    @staticmethod
    def get_user_patterns():
        return """
        SELECT 
            f.Usuario_emisor as Id_usuario,
            o.Operacion,
            COUNT(*) as num_operaciones,
            SUM(f.Cantidad) as suma_total
        FROM fact_table f
        JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        GROUP BY f.Usuario_emisor, o.Operacion
        HAVING Id_usuario IS NOT NULL;
        """
    
    @staticmethod
    def get_flow_analysis():
        return """
        SELECT 
            o.Operacion,
            f.Usuario_emisor,
            f.Usuario_receptor,
            f.Cantidad,
            f.Hora_transaccion
        FROM fact_table f
        JOIN dim_operaciones o ON f.Id_tipo_operacion = o.Id_tipo_operacion
        WHERE f.Usuario_emisor IS NOT NULL 
        AND f.Usuario_receptor IS NOT NULL
        LIMIT 1000;
        """

class Visualizations:
    """Clase para manejar las visualizaciones de datos"""
    
    @staticmethod
    def plot_operaciones_summary(df):
        """Crea un gráfico de barras para el resumen de operaciones"""
        fig = go.Figure(data=[
            go.Bar(
                name='Suma Total',
                x=df['Operacion'],
                y=df['suma_total'],
                text=df['suma_total'].round(2),
                textposition='auto',
            )
        ])

        fig.update_layout(
            title='Volumen Total por Tipo de Operación',
            xaxis_title='Tipo de Operación',
            yaxis_title='Suma Total (€)',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def plot_temporal_analysis(df):
        """Crea un gráfico de líneas para el análisis temporal"""
        fig = px.line(
            df,
            x='fecha',
            y='suma_diaria',
            color='Operacion',
            title='Evolución Temporal de Transacciones por Tipo'
        )
        
        fig.update_layout(
            xaxis_title='Fecha',
            yaxis_title='Importe Diario (€)',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def plot_user_patterns(df):
        """Crea un heatmap de patrones de usuario"""
        pivot_table = df.pivot_table(
            values='num_operaciones',
            index='Id_usuario',
            columns='Operacion',
            fill_value=0
        )
        
        plt.figure(figsize=(15, 8))
        sns.heatmap(pivot_table.head(10), annot=True, fmt='g', cmap='YlOrRd')
        plt.title('Frecuencia de Operaciones por Usuario (Top 10)')
        plt.tight_layout()
        return plt.gcf()

# Configuración de estilo para las visualizaciones
def set_plot_style():
    """Configura el estilo de las visualizaciones"""
    plt.style.use('seaborn')
    sns.set_palette('husl')
    plt.rcParams['figure.figsize'] = [12, 6]
    plt.rcParams['font.size'] = 12 