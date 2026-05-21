# -*- coding: utf-8 -*-
import logging
from dotenv import load_dotenv
from bd import validar_existencia_semanal, guardar_en_sql 
from ec_metrics_pipeline import pipeline
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
        
        _, end_time = fecha_z_automatica(utc=False)
        validar_existencia_semanal(end_time)
        resultado = pipeline()
        
        if resultado is not None and not resultado.is_empty():
           
            guardar_en_sql(resultado)
            
            logging.info(f"Pipeline completado. Registros: {resultado.height}")
            print("Proceso terminado exitosamente.")
        else:
            logging.warning("El pipeline no devolvio datos.")

    except Exception as e:
        logging.error(f"Error critico en el flujo principal: {str(e)}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()