# -*- coding: utf-8 -*-
import zoneinfo
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

def fecha_z_automatica():
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
    # Convertir a UTC
    inicio_lunes_utc = inicio_lunes_local.astimezone(timezone.utc)
    final_domingo_utc = final_domingo_local.astimezone(timezone.utc)

    # retornamos y convertimos a milisegundos

    start_time = inicio_lunes_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    end_time = final_domingo_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    logger.info("Parametros de fecha generados correctamente")

    return start_time, end_time

  except zoneinfo.ZoneInfoNotFoundError:
    logger.error("No se encontro la zona horaria Mexico")
    return None

def fecha_z_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f):
    try:
        # Definir zona horaria Mexico
        tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
        
        # Crear objetos datetime basados en tus argumentos (asumiendo hora local)
        # Inicio a las 00:00:00 y fin a las 23:59:59 para cubrir el día completo
        inicio_local = datetime(ano_i, mes_i, dia_i, 0, 0, 0, tzinfo=tz_local)
        final_local = datetime(ano_f, mes_f, dia_f, 23, 59, 59, tzinfo=tz_local)
        
        # Convertir a UTC
        inicio_utc = inicio_local.astimezone(timezone.utc)
        final_utc = final_local.astimezone(timezone.utc)

        # Retornamos y convertimos a formato con milisegundos y Z
        start_time = inicio_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        end_time = final_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        logger.info(f"Parametros de fecha manuales generados: {start_time} - {end_time}")

        return start_time, end_time

    except Exception as e:
        logger.error(f"Error al generar fechas manuales: {e}")
        return None