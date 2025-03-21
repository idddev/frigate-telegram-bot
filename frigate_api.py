"""
Módulo Frigate API

Obtiene la URL base de la API de Frigate desde la variable de entorno FRIGATE_API_URL 
y provee métodos genéricos para realizar peticiones GET y POST a dicha API.
Si la API requiere autorización, se utiliza el token definido en FRIGATE_API_TOKEN.
"""

from io import BytesIO
from typing import Optional, Dict, Any
import requests
from envs import FRIGATE_API_URL

def get(endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10) -> Dict[str, Any]:
    """
    Realiza una petición GET a la API de Frigate.

    :param endpoint: El endpoint de la API (se concatenará con FRIGATE_API_URL).
    :param params: Parámetros de consulta para la petición GET.
    :param timeout: Tiempo máximo de espera en segundos.
    :return: La respuesta JSON convertida en diccionario.
    :raises: requests.HTTPError en caso de error en la petición.
    """
    url = f"{FRIGATE_API_URL}/{endpoint.lstrip('/')}"
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()

def post(endpoint: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, timeout: float = 10) -> Dict[str, Any]:
    """
    Realiza una petición POST a la API de Frigate.

    :param endpoint: El endpoint de la API (se concatenará con FRIGATE_API_URL).
    :param data: Datos a enviar en la petición como form-data.
    :param json_data: Datos a enviar en formato JSON.
    :param timeout: Tiempo máximo de espera en segundos.
    :return: La respuesta JSON convertida en diccionario.
    :raises: requests.HTTPError en caso de error en la petición.
    """
    url = f"{FRIGATE_API_URL}/{endpoint.lstrip('/')}"
    response = requests.post(url, data=data, json=json_data, timeout=timeout)
    response.raise_for_status()
    return response.json()

def get_event_snapshot(event_id: str):
    """
    Obtiene snapshot de un evento.

    :param event_id: El ID del evento.
    :return: Snapshot
    """
    url = f"{FRIGATE_API_URL}/events/{event_id}/snapshot.jpg"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    
    return None

def get_camera_snapshot(camera_id: str):
    """
    Obtiene snapshot de una cámara.

    :param camera_id: El ID de la cámara.
    :return: Snapshot
    """
    url = f"{FRIGATE_API_URL}/{camera_id}/latest.jpg"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    
    return None
    
def get_review_preview(review_id):
    """
    Obtiene preview de una revisión.

    :param review_id: El ID de la revisión.
    :return: Preview
    """
    url = f"{FRIGATE_API_URL}/review/{review_id}/preview"
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    
    return None