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
    ForeignKey
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

        # Leemos la estructura de la tabla 'invoices' que ya existe en la BD
        print("Reflejando la tabla 'invoices' desde la base de datos...")
        invoices_table = Table('invoices', metadata, autoload_with=db_conn)
        print("Tabla 'invoices' reflejada con éxito.")

        # Definimos la tabla "invoices"
        invoices_table = Table(
            "scales",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("invoice_id", Integer, ForeignKey("invoices.id"), nullable=False),
            Column("alto", Numeric(10, 2)),
            Column("ancho", Numeric(10, 2)),
            Column("largo", Numeric(10, 2)),
            Column("peso_aforado", Numeric(10, 2)),
            Column("peso_fisico", Numeric(10, 2)),
            Column("peso_facturable", Numeric(10, 2)),
            Column("tarifa_real", Numeric(10, 2), nullable=False),
        )

        print("Creando la tabla 'scales' si no existe...")
        # Crea la tabla en la base de datos (si no existe ya)
        metadata.create_all(db_conn, checkfirst=True)
        print("¡Tabla creada con éxito!")


except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    if 'connector' in locals():
        connector.close()
    print("Conexión cerrada.")
