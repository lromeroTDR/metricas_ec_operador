# -*- coding: utf-8 -*-
import requests
import time
import logging
import functools

logger = logging.getLogger(__name__)

def retry_api(max_attempts=3, delay=15):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    logger.info(f"Iniciando intento {attempts + 1} para: {func.__name__}")
                    return func(*args, **kwargs)

                except requests.exceptions.HTTPError as e:
                    attempts += 1
                    status = e.response.status_code
                    # Guardamos el error en el log en lugar de solo imprimirlo
                    logger.warning(f"Fallo en {func.__name__} | Status: {status} | Intento: {attempts}")

                    if attempts < max_attempts:
                        time.sleep(delay)
                    else:
                        logger.error(f"CRÍTICO: Se agotaron reintentos en {func.__name__}")
                        raise e

                except Exception as e:
                    attempts += 1
                    logger.error(f"Error inesperado en {func.__name__}: {str(e)}")
                    if attempts < max_attempts:
                        time.sleep(delay)
                    else:
                        raise e
            return None
        return wrapper
    return decorator