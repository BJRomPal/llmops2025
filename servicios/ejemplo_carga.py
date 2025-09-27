import os
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import Table, MetaData

# --- Configuración de la Conexión ---
load_dotenv()
connector = Connector()

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_instance = os.getenv('INSTANCE_CONNECTION_NAME')
db_name = os.getenv('DB_NAME')

def getconn():
    return connector.connect(
        db_instance, "pymysql", user=db_user, password=db_pass, db=db_name
    )

pool = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

# --- Inserción del Registro ---
try:
    with pool.connect() as db_conn:
        metadata = MetaData()

        # 1. Reflejamos la tabla 'invoices' para que SQLAlchemy conozca su estructura
        invoices_table = Table('invoices', metadata, autoload_with=db_conn)

        # 2. Creamos la instrucción de inserción con los valores que queremos añadir
        stmt = invoices_table.insert().values(
            periodo=202511,
            proveedor="BoxFast",
            track_code="BFX42754874321X",
            ambito=2,
            tipo_servicio="24hs",
            name="SDR Rear Bumper Step footstep Trim For Toyota Fortuner 2016 onwards",
            main_category="car & motorbike",
            sub_category="Car Parts",
            category="Car_Parts",
            alto=32.0,
            ancho=18.0,
            largo=69.0,
            peso_aforado=13.25,
            peso_fisico=12.2,
            peso_facturable=13.25,
            tarifa=5600.00
        )
        
        print("Ejecutando la inserción...")
        # 3. Ejecutamos la instrucción y guardamos los cambios (commit)
        result = db_conn.execute(stmt)
        db_conn.commit()

        print(f"✅ ¡Registro insertado con éxito! ID del nuevo registro: {result.inserted_primary_key[0]}")

except Exception as e:
    print(f"❌ Ocurrió un error: {e}")

finally:
    if 'connector' in locals():
        connector.close()
    print("Conexión cerrada.")