import mysql.connector

def test_db():
    try:
        print("\n=== PRUEBA DE CONEXIÓN A LA BASE DE DATOS ===")
        conn = mysql.connector.connect(
            host='data_ekhilur_final_challenge_db',
            user='user',
            password='userpassword',
            database='ekhilur',
            port=3306  # Puerto interno en la red de Docker
        )
        
        if conn.is_connected():
            print('✅ Conexión exitosa a la base de datos!')
            cursor = conn.cursor()
            
            # Probar versión
            cursor.execute('SELECT VERSION()')
            version = cursor.fetchone()
            print(f'Versión MySQL: {version[0]}')
            
            # Probar consulta de datos
            print("\nProbando consulta de datos...")
            cursor.execute("""
                SELECT COUNT(*) as total_registros,
                       MIN(df.Fecha) as fecha_inicial,
                       MAX(df.Fecha) as fecha_final
                FROM fact_table f
                JOIN dim_fecha df ON f.Id_fecha = df.Id_fecha
                WHERE f.Id_tipo_operacion IN (
                    SELECT Id_tipo_operacion 
                    FROM dim_operaciones 
                    WHERE Operacion IN (
                        'Cuota mensual de socio',
                        'Cuota variable',
                        'Comisión por retirada',
                        'Cuota de socio'
                    )
                )
            """)
            result = cursor.fetchone()
            print(f"Total de registros relevantes: {result[0]}")
            print(f"Rango de fechas: {result[1]} a {result[2]}")
            
            cursor.close()
            conn.close()
            print("\n✅ Pruebas completadas exitosamente")
            
    except mysql.connector.Error as err:
        print(f"\n❌ Error de MySQL: {err}")
        if err.errno == 2003:
            print("\nPosible problema: No se puede conectar al servidor de base de datos")
            print("Soluciones:")
            print("1. Verificar que el contenedor de la base de datos esté corriendo")
            print("2. Comprobar que el nombre del host sea correcto")
            print("3. Verificar que el puerto sea accesible")
            print("\nDetalles de la conexión intentada:")
            print("Host: data_ekhilur_final_challenge_db")
            print("Puerto: 3306")
            print("Base de datos: ekhilur")
        elif err.errno == 1045:
            print("\nPosible problema: Acceso denegado con las credenciales proporcionadas")
            print("Soluciones:")
            print("1. Verificar el usuario y contraseña")
            print("2. Confirmar que el usuario tenga permisos en la base de datos")
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")

if __name__ == "__main__":
    test_db() 