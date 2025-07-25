from sqlalchemy import create_engine, text
import os
import pandas as pd
import dotenv
dotenv.load_dotenv()

def run_query(query):
    query_text = text(query)
    engine = create_engine(os.getenv("IQ_DB_AUTH"))
    connection = engine.connect()
    df = pd.read_sql_query(query_text, connection)
    connection.close()
    return df

def execute_query(query):
    """Execute INSERT, UPDATE, DELETE queries that don't return rows"""
    query_text = text(query)
    engine = create_engine(os.getenv("IQ_DB_AUTH"))
    connection = engine.connect()
    result = connection.execute(query_text)
    connection.commit()
    connection.close()
    return result

