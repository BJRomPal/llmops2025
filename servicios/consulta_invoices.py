import os
from dotenv import load_dotenv
import pandas as pd
from google.cloud.sql.connector import Connector
import sqlalchemy

# initialize Connector object
connector = Connector()

load_dotenv()

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_instance = os.getenv('INSTANCE_CONNECTION_NAME')
db_name = os.getenv('DB_NAME')

def trae_invoices(periodo):

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

    with pool.connect() as db_conn:
    
        # query and fetch invoices table
        result = db_conn.execute(sqlalchemy.text(f"SELECT * FROM invoices WHERE periodo = {periodo}"))
        columns = result.keys()
        # 2. Unpack all rows of data
        rows = result.fetchall()
    
    # 3. Create the DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
    connector.close()
    return df

