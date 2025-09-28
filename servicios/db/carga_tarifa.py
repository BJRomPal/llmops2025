import os
import csv
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import (
    Table,
    Column,
    String,
    Date,
    Integer,
    Numeric,
    MetaData,
)

# initialize Connector object
connector = Connector()

load_dotenv()

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_instance = os.getenv('INSTANCE_CONNECTION_NAME')
db_name = os.getenv('DB_NAME')

# function to return the database connection object
def getconn():
    conn = connector.connect(
        db_instance,
        "pymysql",
        user=db_user,
        password=db_pass,
        db=db_name
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

try:
    with pool.connect() as db_conn:
        # El objeto MetaData contiene la definición de todas nuestras tablas
        metadata = MetaData()

        # Definimos la tabla "tarifario"
        tarifario_table = Table(
            "tarifario",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("proveedor", String(255), nullable=False),
            Column("fecha_inicio", Date, nullable=False),
            Column("fecha_fin", Date, nullable=False),
            Column("ambito", String(255), nullable=False),
            Column("tipo_de_servicio", String(255), nullable=False),
            Column("rango_desde", Integer, nullable=False),
            Column("rango_hasta", Integer, nullable=False),
            Column("tarifa", Numeric(10, 2), nullable=False), # Ideal para dinero (ej: 12345678.99)
        )

        print("Creando la tabla 'tarifario' si no existe...")
        # Crea la tabla en la base de datos (si no existe ya)
        metadata.create_all(db_conn, checkfirst=True)
        print("¡Tabla creada con éxito!")

        # --- Carga de Datos desde el CSV ---
        print("Insertando datos desde tarifario.csv...")
        clean_rows = []
        with open('files/Tarifario_2025H2.csv', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
    
            for row in reader:
                clean_row = {}
                for key, value in row.items():
                    # Limpiamos el nombre de la columna: minúsculas, sin espacios y sin acentos
                    clean_key = key.lower().replace(' ', '_').replace('á', 'a')
                    clean_row[clean_key] = value

                clean_rows.append(clean_row)

        # Verificamos que al menos una fila fue procesada antes de insertar
        if clean_rows:
            # Ejecutamos la inserción de todos los datos
            db_conn.execute(tarifario_table.insert(), clean_rows)
            db_conn.commit()
            print(f"¡Se han insertado {len(clean_rows)} registros en la tabla!")
        else:
            print("No se encontraron filas para insertar en el CSV.")

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    connector.close()
    print("Conexión cerrada.")
