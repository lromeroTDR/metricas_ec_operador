# -*- coding: utf-8 -*-
import logging
import ec_metrics_pipeline
import os
from dotenv import load_dotenv
import sys
from datetime import timedelta, datetime
# Importamos las funciones de tu archivo bd.py
from bd import validar_existencia_semanal, guardar_en_sql 
from fechas import fecha_z_manual


logging.basicConfig(
    filename="ec_metrics_coachMetrics.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f):
    load_dotenv()
    logging.info("Iniciando la ejecucion global del sistema")
    
    try:
        # 1. Obtener las fechas
        start_time, end_time = fecha_z_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f)
        end_time =  datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ') - timedelta(hours=6)
        # 2. VALIDAR: Mandamos SOLO 1 argumento (end_time)
        # La funcion en tu bd.py ya sabe que la tabla es reporte_ec_metricas_operador
        validar_existencia_semanal(end_time)

        # 3. EJECUTAR PIPELINE: Solo llega aqui si la fecha es nueva
        resultado = ec_metrics_pipeline.pipeline_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f)
        
        if resultado is not None and not resultado.is_empty():
            # 4. GUARDAR EN CSV
           
            
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
    # sys.argv[0] es siempre el nombre del archivo
    # Verificamos que se pasen los 6 argumentos necesarios
    if len(sys.argv) == 7:
        try:
            # Convertimos a entero cada argumento recibido
            d_i = int(sys.argv[1])
            m_i = int(sys.argv[2])
            a_i = int(sys.argv[3])
            d_f = int(sys.argv[4])
            m_f = int(sys.argv[5])
            a_f = int(sys.argv[6])
            
            main(d_i, m_i, a_i, d_f, m_f, a_f)
        except ValueError:
            print("Error: Todos los argumentos deben ser numeros enteros.")
    else:
        print("Uso correcto: python main.py <dia_i> <mes_i> <ano_i> <dia_f> <mes_f> <ano_f>")
        print("Ejemplo: python main.py 01 05 2026 07 05 2026")