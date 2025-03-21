# ping_cron.py
import os
import asyncio
import logging
from datetime import datetime
import requests

from envs import PING_ENDPOINT, PING_INTERVAL

logger = logging.getLogger(__name__)

def send_ping_sync() -> dict:
    """
    Función síncrona que envía el ping usando requests.
    Puedes ajustar el payload según tus necesidades.
    """
    payload = {"cameras": {}}
    url = f"{PING_ENDPOINT}/ping"
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

async def send_ping() -> None:
    """
    Envía un ping al endpoint configurado usando requests de forma asíncrona,
    delegando la llamada en un hilo con asyncio.to_thread.
    """
    try:
        result = await asyncio.to_thread(send_ping_sync)
        logger.info("Ping enviado a las %s, respuesta: %s", datetime.utcnow().isoformat(), result)
    except Exception as e:
        logger.error("Error enviando ping: %s", e)

async def ping_cron() -> None:
    """
    Tarea asíncrona que envía un ping cada PING_INTERVAL segundos.
    """
    while True:
        await send_ping()
        await asyncio.sleep(PING_INTERVAL)