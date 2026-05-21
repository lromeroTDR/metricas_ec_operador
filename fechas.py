# -*- coding: utf-8 -*-
import zoneinfo
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

def fecha_z_automatica(utc = True):
  try:
    # Definir zona horaria Mexico
    tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
    # Obtener el ahora reginal
    ahora_local = datetime.now(tz_local)
    # Calcular el lunes a las 00:00:00 De esta semana
    dias_al_lunes = ahora_local.weekday()
    inicio_lunes_local = ahora_local -timedelta(days=dias_al_lunes) -timedelta(days=7)
    inicio_lunes_local = inicio_lunes_local.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    final_domingo_local = inicio_lunes_local + timedelta(days=7) - timedelta(seconds=1)

    if utc:
        inicio_lunes = inicio_lunes_local.astimezone(timezone.utc)
        final_domingo = final_domingo_local.astimezone(timezone.utc)
    else:
        inicio_lunes = inicio_lunes_local
        final_domingo = final_domingo_local
    

    start_time = inicio_lunes.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    end_time = final_domingo.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    logger.info("Parametros de fecha generados correctamente")

    return start_time, end_time

  except zoneinfo.ZoneInfoNotFoundError:
    logger.error("No se encontro la zona horaria Mexico")
    return None

def fecha_z_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f, utc = True):
    try:
        # Definir zona horaria Mexico
        tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
        
        # Crear objetos datetime basados en tus argumentos (asumiendo hora local)
        # Inicio a las 00:00:00 y fin a las 23:59:59 para cubrir el d�a completo
        inicio_local = datetime(ano_i, mes_i, dia_i, 0, 0, 0, tzinfo=tz_local)
        final_local = datetime(ano_f, mes_f, dia_f, 23, 59, 59, tzinfo=tz_local)
        
        if utc:
            # Convertir a UTC
            inicio = inicio_local.astimezone(timezone.utc)
            final = final_local.astimezone(timezone.utc)
        else:
            # Mantener en la zona horaria local
            inicio = inicio_local
            final = final_local

        # Retornamos y convertimos a formato con milisegundos y Z
        start_time = inicio.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        end_time = final.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        logger.info(f"Parametros de fecha manuales generados: {start_time} - {end_time}")

        return start_time, end_time

    except Exception as e:
        logger.error(f"Error al generar fechas manuales: {e}")
        return None