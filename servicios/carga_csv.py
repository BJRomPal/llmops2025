import os
import csv
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Numeric,
    MetaData,
    Text,
)

def carga_invoices(csv_path):
    """Función para cargar datos desde un CSV a la tabla 'invoices' en Cloud SQL."""

    # initialize Connector object
    connector = Connector()

    load_dotenv()

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

            invoices_table = Table('invoices', metadata, autoload_with=db_conn)

            # Definimos la tabla "invoices"
            # --- Carga de Datos desde el CSV ---
            print("Insertando datos desde invoices.csv...")
            with open(csv_path, mode='r', encoding='utf-8-sig') as csvfile:
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
