import os
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import Table, MetaData
import pandas as pd

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def insert_scales_data(df: pd.DataFrame) -> bool:
    """
    Inserta datos de un DataFrame en la tabla 'scales' de Cloud SQL.

    Esta función se conecta a la base de datos, filtra el DataFrame para 
    quedarse solo con las columnas necesarias para la tabla 'scales', y
    realiza una inserción masiva de todos los registros.

    Args:
        df (pd.DataFrame): El DataFrame que contiene los datos del análisis.
                           Debe incluir las columnas requeridas para la tabla 'scales'.

    Returns:
        bool: True si la inserción fue exitosa, False en caso de error.
    """
    connector = Connector()
    
    # --- Configuración de la Conexión ---
    db_instance = os.getenv('INSTANCE_CONNECTION_NAME')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')

    # Función para obtener la conexión que SQLAlchemy usará
    def getconn():
        return connector.connect(
            db_instance, "pymysql", user=db_user, password=db_pass, db=db_name
        )

    # Crear el pool de conexiones de SQLAlchemy
    pool = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

    # --- Preparación de los Datos ---
    # Columnas que necesita la tabla 'scales'
    columns_to_insert = [
        'invoice_id', 'alto', 'ancho', 'largo', 
        'peso_aforado', 'peso_fisico', 'peso_facturable', 'tarifa_real'
    ]

    try:
        # 1. Filtrar el DataFrame para obtener solo las columnas necesarias
        df_for_insert = df[columns_to_insert]
    except KeyError as e:
        print(f"❌ Error: El DataFrame de entrada no contiene la columna requerida: {e}")
        connector.close()
        return False

    # 2. Convertir el DataFrame a una lista de diccionarios, formato ideal para la inserción masiva
    data_to_insert = df_for_insert.to_dict(orient='records')
    
    if not data_to_insert:
        print("ℹ️ No hay datos nuevos para insertar en la tabla 'scales'.")
        connector.close()
        return True

    # --- Lógica de Inserción ---
    try:
        with pool.connect() as db_conn:
            metadata = MetaData()
            # Reflejar la tabla 'scales' para que SQLAlchemy conozca su estructura
            scales_table = Table('scales', metadata, autoload_with=db_conn)
            
            print(f"Iniciando la inserción de {len(data_to_insert)} registros en la tabla 'scales'...")
            
            # 3. Ejecutar la inserción masiva
            db_conn.execute(scales_table.insert(), data_to_insert)
            db_conn.commit()
            
            print(f"✅ ¡{len(data_to_insert)} registros insertados con éxito en la tabla 'scales'!")
            return True

    except Exception as e:
        print(f"❌ Ocurrió un error durante la inserción en la base de datos: {e}")
        return False
    
    finally:
        # Asegurarse de cerrar el conector principal
        connector.close()
        print("Conexión con la base de datos cerrada.")