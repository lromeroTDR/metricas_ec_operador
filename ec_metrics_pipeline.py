# -*- coding: utf-8 -*-
import requests
import time
from datetime import  timedelta
import polars as pl
from datetime import datetime
import fechas
import logging
from config import headers
from wrapp import retry_api
from config import API_URLS, tags_filtro, behaviorLabels

logger = logging.getLogger(__name__)



############################################
# -----  Calificaciones por operador -------
############################################
@retry_api(max_attempts=3, delay=10)
def extraer_score_operadores(url, headers,  start_time, end_time):
    # Parámetros base que no cambian
    base_params = {
  
        "startTime": start_time,
        "endTime": end_time,

    }

    all_events = []
    has_next_page = True
    cursor = None

    while has_next_page:
        # Copiamos los parámetros base para no ensuciarlos en cada ciclo
        current_params = base_params.copy()
        if cursor:
            current_params["after"] = cursor

        response = requests.get(url, headers=headers, params=current_params, timeout=30)
        response.raise_for_status()

        data = response.json()
        events = data.get("data", [])
        all_events.extend(events)

        # Extraer información de paginación
        pagination = data.get("pagination", {})
        has_next_page = pagination.get("has_next_page", False)
        cursor = pagination.get("endCursor") # O la llave que use tu API

        logger.info(f"Descargados {len(events)} eventos. Total acumulado: {len(all_events)}")

        if has_next_page:
            time.sleep(0.5)

    if all_events:
        logger.info("Proceso De Extraccion finalizado exitosamente")
        return pl.from_dicts(all_events, strict=False)
    else:
        logger.warning("No se encontraron eventos tras recorrer todas las paginas")
        return pl.DataFrame() # Retornar un DF vacío en lugar de None evita errores después
    
def transformacion_operadores_eventos(df):
   
    try:    
        df_base = df.select([
            "driverId", 
            "driverScore", 
            "driveDistanceMeters", 
            "driveTimeMilliseconds"
        ])

    # Procesar Behaviors (count y scoreImpact)
    # Explota, desanida y pivota manteniendo ambas métricas
        df_behaviors_wide = (
            df.select(["driverId", "behaviors"])
            .explode("behaviors")
            .unnest("behaviors")
            .drop_nulls("behaviorType")
            .pivot(
                index="driverId",
                on="behaviorType",
                values=["count", "scoreImpact"],
                aggregate_function="sum"
            )
            .fill_null(0)
        )

    # Procesar Speeding (durationMilliseconds y scoreImpact)
    # Explota, desanida y pivota manteniendo ambas métricas
        df_speeding_wide = (
            df.select(["driverId", "speeding"])
            .explode("speeding")
            .unnest("speeding")
            .drop_nulls("speedingType")
            .filter( pl.col("speedingType") == "maxSpeed")
            .pivot(
                index="driverId",
                on="speedingType",
                values=["durationMilliseconds", "scoreImpact"],
                aggregate_function="sum"
            )
            .fill_null(0)
        )

    # Usamos left join para mantener a todos los conductores de la base
        df_final = (
            df_base
            .join(df_behaviors_wide, on="driverId", how="left")
            .join(df_speeding_wide, on="driverId", how="left")
            .fill_null(0) # Rellenar con 0 si un conductor no tuvo ciertos eventos
        )


        return df_final

    except pl.ColumnNotFoundError as e:
        logger.critical(f"Faltan columnas críticas en el DataFrame base: {e}")
        raise  
    except Exception as e:
        logger.critical(f"Error inesperado en la transformación de operadores: {e}")
        raise

################################################
# -----Extraer eventos de seguridad Coached-----
################################################

@retry_api(max_attempts=3, delay=10)
def extraer_eventos_seguridad(start_time_rfc, end_time_rfc, headers, url, queryByTimeField, behaviorLabels = behaviorLabels, eventStates = "coached"):

    # Parámetros iniciales
    params_data_Z = {
        "startTime": start_time_rfc,
        "endTime": end_time_rfc,
        "queryByTimeField": queryByTimeField,
        "behaviorLabels": behaviorLabels,
        "eventStates": eventStates
    }

    all_events = []
    has_next_page = True
    cursor = ""

    print(f"Iniciando descarga desde: {start_time_rfc} hasta : {end_time_rfc}")

    # --- Bucle de Paginación ---
    while has_next_page:
        current_params = params_data_Z.copy()
        if cursor:
              current_params["after"] = cursor

        response = requests.get(url, headers=headers, params=current_params, timeout=30)

        response.raise_for_status()
        data = response.json()
        events = data.get('data', [])
        all_events.extend(events)

        # Extraer info de paginación de la respuesta
        pagination = data.get('pagination', {})
        has_next_page = pagination.get('hasNextPage', False)
        cursor = pagination.get('endCursor', "")

        print(f"Descargados {len(events)} eventos. Total acumulado: {len(all_events)}")
        logger.info(f"Descargados {len(events)} eventos. Total acumulado: {len(all_events)}")
        # Pausa breve para evitar saturar la API
        if has_next_page:
            time.sleep(0.2)
  # --- Creación del DataFrame ---
    if all_events:
      df_final = pl.DataFrame(all_events)

      return df_final
    else:
      print("\n No se encontraron eventos en el período seleccionado.")
      logger.warning("No se encontraron eventos en el periodo seleccionado")
      raise ValueError

def transformar_eventos_seguridad(df):
    try:
        df_final = (
            df
            .drop("id")
            # 1. Desanidamos asset y driver y renombramos
            .unnest("asset").rename({"id": "vehicleId"})
            .unnest("driver").rename({"id": "driverId"})
            
            # 2. Desanidamos los comportamientos (behaviorLabels)
            # Primero explotamos la lista y luego desanidamos el struct interno
            .explode("behaviorLabels")
            .unnest("behaviorLabels")
            
            # 3. Pivotamos para pasar a formato ancho
            # El pivot agrupa automáticamente por el index y cuenta las ocurrencias
            .with_columns(
              (pl.col("label") + "_coached").alias("label")
            )       
            .pivot(
                on="label",           # La columna que tiene el tipo de evento (ej. MobileUsage)
                index=["driverId"], 
                values="label",       # Usamos la misma columna para contar
                aggregate_function="len" # 'len' cuenta cuántas veces aparece cada evento
            )
            
            # 4. Limpieza final: rellenar nulos con 0
            .fill_null(0)
        )
        
        return df_final

    except pl.ColumnNotFoundError as e:
        logger.critical(f"Faltan columnas críticas o esperadas en el DataFrame: {e}")
        raise
        
    except Exception as e:
        logger.critical(f"Error inesperado en la transformación de eventos Seguridad: {e}")
        raise

def unir_metricas_operadores(operadores, reporte_metricas):
    try:
        df_consolidado = (
            operadores.join(
            reporte_metricas, 
            on=["driverId"], 
            how="left"
        )
        # Llenamos con 0 todos los nulos (los que no tuvieron coaching)
        .fill_null(0)
        )
        return df_consolidado
    except pl.ColumnNotFoundError as e:
        logger.critical(f"Faltan columnas críticas o esperadas en el DataFrame: {e}")
        raise
        
    except Exception as e:
        logger.critical(f"Error inesperado en la Union de metricas con operadores: {e}")
        raise
###############################
# ---- Extraer Operadores ----
###############################

@retry_api(max_attempts=3, delay=10)
def extraer_operadores(headers, url_operadores):
    """
    Obtiene y limpia la lista de operadores desde la API de Samsara
    usando Polars y manejo de paginación robusto.
    """
    todos_los_operadores = []
    params = {}

    # 1. Fase de Extracción (Ingesta de datos)
    while True:
        response = requests.get(url_operadores, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        operadores_list = data.get('data', [])

        if operadores_list:
            todos_los_operadores.extend(operadores_list)

        # Lógica de paginación de Samsara
        pagination = data.get('pagination', {})
        if pagination.get('hasNextPage') and pagination.get('endCursor'):
            params['after'] = pagination.get('endCursor')
        else:
            break

    # 2. Fase de Transformación con Polars
    if not todos_los_operadores:
        logger.warning("La lista de operadores está vacía.")
        return pl.DataFrame()

    # Convertimos a DataFrame de Polars
    df_drivers = pl.DataFrame(todos_los_operadores)

    # Aplicamos transformaciones usando encadenamiento (más eficiente y elegante)
    df_drivers = (
        df_drivers
        .rename({'id': 'driverId', 'name': 'driverName'})
       # .filter(pl.col("driverActivationStatus") == "active")
       # .select(["driverId", "driverName", "driverActivationStatus", "tags", "staticAssignedVehicle"]) # Opcional: seleccionar solo lo necesario
    )

    logger.info(f"Éxito: Se obtuvieron {df_drivers.height} registros activos.")
    return df_drivers

def transformacion_operadores(df_operadores):
    """
    Normaliza 'tags' y 'staticAssignedVehicle' usando expresiones nativas de Polars.
    """
    if df_operadores.is_empty():
        logger.warning("La lista de operadores está vacía.")
        return df_operadores

    df_Operadores_transf = (
        df_operadores
        # Filtramos los Operadores activos
        .filter(pl.col("driverActivationStatus") == "active")
        # Seleccionamos las columnas Necesarias
        .select(["driverId", "driverName", "driverActivationStatus", "tags"])
        .with_columns([
            pl.col("tags").list.get(0).struct.field("id").alias("tagId"),
            pl.col("tags").list.get(0).struct.field("name").alias("tagName"),
            pl.col("tags").list.get(0).struct.field("parentTagId").alias("parentTagId"),
        ])
        # 3. Limpieza de columnas y casteo masivo a String
        .drop(["tags", "driverActivationStatus"])
        .with_columns([
            pl.col(['driverId', 'tagId', 'parentTagId'])
            .cast(pl.Utf8)
        ])

    )
    print(f"Éxito: Vehículos transformados. Columnas: {df_Operadores_transf.columns}")
    logger.info(f"Iniciando intento {df_Operadores_transf.columns}")
    return df_Operadores_transf

######################################
# ---- EXTRAER TAGS DE LA ORGANIZACION
######################################
@retry_api(max_attempts=3, delay=10)
def extraer_tags_samsara(headers, url):
    """
    Obtiene la lista de tags de la organización usando el motor de Polars.
    """
  
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json().get('data', [])

    if not data:
        logger.warning("Advertencia: No se encontraron Tags")
        print("Advertencia: No se encontraron tags.")
        return pl.DataFrame()

    # 2. Creación del DataFrame y Transformación
    # Polars infiere el esquema automáticamente de la lista de diccionarios
    df_tags = (
        pl.DataFrame(data)
        .rename({
            'id': 'tagId',
            'name': 'tagName',
            'parentTagId': 'parentTagId'
        })
        .with_columns([
            pl.col(['tagId', 'parentTagId']).cast(pl.Utf8)
        ])
    )
    print(f"Éxito: Se obtuvieron {df_tags.height} tags.")
    logger.info(f"Éxito: Se obtuvieron {df_tags.height} tags.")
    return df_tags

def transformacion_tags(df_tags, tags_filtro):
    """
    Selecciona las columnas del tag padre.
    """
    try:
        df_tags_transformado = (
            df_tags
            .select(["tagId", "tagName", "parentTag"])
            .unnest("parentTag")
            .rename({"name": "parentTagName", "id":"parentTagId"})   
            .filter(pl.col("tagName").is_in(tags_filtro))
        )
        logger.info(f"Éxito: Se obtuvieron {df_tags_transformado.height} tags.")
        return df_tags_transformado
    except Exception as e:
        logger.error(f"Error en la transformación de tags: {e}")
        return None
    except pl.ColumnNotFoundError as e:
        logger.critical(f"Faltan columnas críticas o esperadas en el DataFrame: {e}")
        raise
    
def unir_tags_operadores(df_operadores, df_tags, tags_filtro):
    """
    Une el nombre del tag padre al DataFrame maestro usando el ID del padre.
    """
    try: 

        # Limpieza y preparación de la tabla de referencia
        # Usamos unique() para quitar duplicados, es extremadamente rápido en Polars.
        df_ref_tags = (
            df_tags
            .select(["tagId", "tagName"])
            .rename({"tagName": "parentTagName", "tagId" : "parentTagId"})
            .unique()
        )

        # Unión (Join) y Limpieza en un solo flujo (Method Chaining)
        df_unificado = (
            df_operadores
            # Aseguramos tipos consistentes para el join
            .with_columns([
                pl.col("parentTagId").cast(pl.Utf8)
            ])
            .join(
                df_ref_tags.with_columns(pl.col("parentTagId").cast(pl.Utf8)),
                left_on="parentTagId",
                right_on="parentTagId",
                how="left"
            )
            # Renombrado y eliminación de nulos residuales
        
            .with_columns(
                pl.col("parentTagName").fill_null("Sin Parent Tag"), # Opcional: manejar nulos
                pl.col("tagName").fill_null("Sin tagName")
            ).filter( pl.col("parentTagName").is_in(tags_filtro))
        )

        logger.info(f"Éxito: Columna agregada correctamente.")
        return df_unificado
    except pl.ColumnNotFoundError as e:
        logger.critical(f"Faltan columnas críticas o esperadas en el DataFrame: {e}")
        raise
        
    except Exception as e:
        logger.critical(f"Error inesperado en la union de los tags con nombre operador: {e}")
        raise

##############################################################    
# ----- Unir tags, operadores, metricas, metricas coach -----
#############################################################
def unir_metricasCoach(df, metricas, end_time):
    try:

        fecha_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        metricasCoach = (
            df.join(metricas, on="driverId", how="left")
            .with_columns(
                fecha_corte = pl.lit(fecha_dt) - timedelta(hours=6)
            )
        )
        
        return metricasCoach

    except ValueError as e:
        logger.critical(f"Error en el formato de la fecha 'end_time' ({end_time}): {e}")
        raise

    except pl.ColumnNotFoundError as e:
        logger.critical(f"Falta la columna 'driverId' en alguno de los DataFrames: {e}")
        raise
        
    except Exception as e:
        logger.critical(f"Error inesperado al unir métricas de Coach: {e}")
        raise


def ejecutar_pipeline_core(start_time, end_time):
    try:
        url = API_URLS["scores"]
        scores_operadores = extraer_score_operadores(url, headers, start_time, end_time)
        scores_operadores_transformado = transformacion_operadores_eventos(scores_operadores)
        
        url_eventos = API_URLS["events"]
        df_eventos_created = extraer_eventos_seguridad(start_time, end_time, headers, url_eventos, "createdAtTime")
        df_reporte = transformar_eventos_seguridad(df_eventos_created)
        
        df_consolidado = unir_metricas_operadores(scores_operadores_transformado, df_reporte)
        
        url_metadata = API_URLS["drivers"]
        df_drivers = extraer_operadores(headers=headers, url_operadores=url_metadata)
        df_drivers_transformado = transformacion_operadores(df_operadores=df_drivers)
        
        url = API_URLS["tags"]
        tags = extraer_tags_samsara(headers, url)
        filtro = tags_filtro
        tags_transformado = transformacion_tags(df_tags=tags, tags_filtro=filtro)
        
        df_operadores_tags = unir_tags_operadores(df_operadores=df_drivers_transformado, df_tags=tags_transformado, tags_filtro=tags_filtro)
        
        df_metricas_final = unir_metricasCoach(df_consolidado, df_operadores_tags, end_time=end_time)
        return df_metricas_final

    except Exception as e:
        logger.critical(f"Fallo catastrófico en la ejecución del pipeline: {e}")
        raise


def pipeline():
    start_time, end_time = fechas.fecha_z_automatica()
    return ejecutar_pipeline_core(start_time, end_time)


def pipeline_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f):
    start_time, end_time = fechas.fecha_z_manual(dia_i, mes_i, ano_i, dia_f, mes_f, ano_f)
    return ejecutar_pipeline_core(start_time, end_time)