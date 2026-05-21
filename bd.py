# -*- coding: utf-8 -*-
import logging
import sqlalchemy
import urllib
import sys
from config import DB_CONFIG

def obtener_conexion_sql():
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['pass']};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    params = urllib.parse.quote_plus(connection_string)
    return f"mssql+pyodbc:///?odbc_connect={params}"

def validar_existencia_semanal(fecha_corte_nueva,  table_name = DB_CONFIG['table'], schema = DB_CONFIG["schema"]):
    """
    Verifica si la fecha ya existe en la base de datos
    """
    engine = sqlalchemy.create_engine(obtener_conexion_sql())
    # Usamos el esquema samsara como pediste
    destino = f"{schema}.{table_name}"
    
    query = sqlalchemy.text(f"SELECT COUNT(*) FROM {destino} WHERE fecha_corte = :fecha")
    
    try:
        with engine.connect() as conn:
            existe = conn.execute(query, {"fecha": fecha_corte_nueva}).scalar()
            if existe > 0:
                print(f"LA FECHA {fecha_corte_nueva} YA ESTA EN LA BD. CANCELANDO...")
                sys.exit()
            else:
                print(f"Fecha {fecha_corte_nueva} libre. Procesando...")
    except Exception as e:
        print(f"Error al validar: {e}")

def guardar_en_sql(df, table_name = DB_CONFIG['table'], schema = DB_CONFIG["schema"] ):
    if df.is_empty():
        logging.warning("DataFrame vacio.")
        return

    engine = sqlalchemy.create_engine(obtener_conexion_sql())
    destino = f"{schema}.{table_name}"
    
    try:
        logging.info(f"Cargando en: {destino}")
        with engine.begin() as connection:
            df.write_database(
                table_name=destino, 
                connection=connection,
                if_table_exists="append"
            )
        logging.info("Exito en la carga")
    except Exception as e:
        print(f"ERROR EN LA CARGA: {e}")