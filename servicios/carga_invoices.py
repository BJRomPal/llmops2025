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
    Text,
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
        metadata = MetaData()

        # Definimos la tabla "invoices"
        invoices_table = Table(
            "invoices",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("periodo", Integer, nullable=False),
            Column("proveedor", String(255), nullable=False),
            Column("track_code", String(255), nullable=False),
            Column("ambito", Integer),
            Column("tipo_servicio", String(100)),
            Column("name", Text), # Usamos Text para descripciones largas
            Column("main_category", String(255)),
            Column("sub_category", String(255)),
            Column("category", String(255)),
            Column("alto", Numeric(10, 2)),
            Column("ancho", Numeric(10, 2)),
            Column("largo", Numeric(10, 2)),
            Column("peso_aforado", Numeric(10, 2)),
            Column("peso_fisico", Numeric(10, 2)),
            Column("peso_facturable", Numeric(10, 2)),
            Column("tarifa", Numeric(10, 2), nullable=False),
        )

        print("Creando la tabla 'invoices' si no existe...")
        # Crea la tabla en la base de datos (si no existe ya)
        metadata.create_all(db_conn, checkfirst=True)
        print("¡Tabla creada con éxito!")

        # --- Carga de Datos desde el CSV ---
        print("Insertando datos desde invoices.csv...")
        with open('files/Invoices_202507-10.csv', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            clean_rows = []
            # Iteramos fila por fila para un mejor control de errores
            for row_num, row in enumerate(reader, 1):
                clean_row = {}
                for k, v in row.items():
                    # ¡IMPORTANTE! Ignoramos columnas sin nombre (causa del error)
                    if k is None:
                        print(f"⚠️ Advertencia: Se encontró una columna extra sin nombre en la fila {row_num}. Se ignorará.")
                        continue
                    clean_row[k.lower()] = v
                clean_rows.append(clean_row)

            # Ejecutamos la inserción de todos los datos
            if clean_rows:
                db_conn.execute(invoices_table.insert(), clean_rows)
                db_conn.commit()
                print(f"✅ ¡Se han insertado {len(clean_rows)} registros en la tabla!")
            else:
                print("No se encontraron datos en el CSV.")

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    if 'connector' in locals():
        connector.close()
    print("Conexión cerrada.")
