# -*- coding: utf-8 -*-
import logging
import sys
from ec_metrics_pipeline import pipeline_manual
from dotenv import load_dotenv
from bd import validar_existencia_semanal, guardar_en_sql 
from fechas import fecha_z_manual


logging.basicConfig(
    filename="ec_metrics_historico.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f):
    load_dotenv()
    logging.info("Iniciando la ejecucion global del sistema")
    
    try:
        
        _, end_time = fecha_z_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f, utc=False)
  
     
        validar_existencia_semanal(end_time)

       
        resultado = pipeline_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f)
        
        if resultado is not None and not resultado.is_empty():
            
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
        print("Uso correcto: python historial.py <dia_i> <mes_i> <ano_i> <dia_f> <mes_f> <ano_f>")
        print("Ejemplo: python historial.py 01 05 2026 07 05 2026")