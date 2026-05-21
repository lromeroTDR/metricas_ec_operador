# -*- coding: utf-8 -*-
import logging
import ec_metrics_pipeline
import os
from dotenv import load_dotenv
import sys
from datetime import timedelta, datetime
# Importamos las funciones de tu archivo bd.py
from bd import validar_existencia_semanal, guardar_en_sql 
from fechas import fecha_z_automatica


logging.basicConfig(
    filename="ec_metrics_coachMetrics.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    load_dotenv()
    logging.info("Iniciando la ejecucion global del sistema")
    
    try:
        # 1. Obtener las fechas
        start_time, end_time = fecha_z_automatica()
        end_time =  datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ') - timedelta(hours=6)
        # 2. VALIDAR: Mandamos SOLO 1 argumento (end_time)
        # La funcion en tu bd.py ya sabe que la tabla es reporte_ec_metricas_operador
        validar_existencia_semanal(end_time)

        # 3. EJECUTAR PIPELINE: Solo llega aqui si la fecha es nueva
        resultado = ec_metrics_pipeline.pipeline()
        
        if resultado is not None and not resultado.is_empty():
            # 4. GUARDAR EN CSV
            resultado.write_csv("reporte_operadores.csv", separator=",")
            
            # 5. GUARDAR EN SQL SERVER
            # Aqui si mandamos el nombre de la tabla porque guardar_en_sql si recibe 2
            guardar_en_sql(resultado, "reporte_ec_metricas_operador")
            
            logging.info(f"Pipeline completado. Registros: {resultado.height}")
            print("Proceso terminado exitosamente.")
        else:
            logging.warning("El pipeline no devolvio datos.")

    except Exception as e:
        logging.error(f"Error critico en el flujo principal: {str(e)}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()