import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# Obtener el token de la variable de entorno
token = os.getenv("SAMSARA_TOKEN")

# Headers actualizados
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {token}"
}

#BD Config

# -*- coding: utf-8 -*-
DB_CONFIG = {
    "server": "10.3.11.10",   
    "database": "IntegracionesBI",
    "schema": "samsara",
    "table": "reporte_ec_metricas_operador",
    "user": "lromero",
    "pass": "5G?Y72K>gofh"
}
