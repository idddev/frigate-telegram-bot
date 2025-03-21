import os

def get_env(name: str) -> str:
    """Obtiene la variable de entorno 'name' y lanza un error si no existe."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"La variable de entorno {name} no está definida.")
    return value

# Obtener constantes del .env con tipado asegurado
MQTT_BROKER: str = get_env("MQTT_BROKER")
MQTT_PORT: int = int(get_env("MQTT_PORT"))
MQTT_TOPICS: list[str] = get_env("MQTT_TOPICS").split(",")
TELEGRAM_TOKEN: str = get_env("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID: str = get_env("TELEGRAM_CHAT_ID")
CAMERA_IP: str = get_env("CAMERA_IP")
CAMERA_USER: str = get_env("CAMERA_USER")
CAMERA_PASSWORD: str = get_env("CAMERA_PASSWORD")
FRIGATE_API_URL: str = get_env("FRIGATE_API_URL").rstrip("/")
PING_ENDPOINT: str = get_env("PING_ENDPOINT")
PING_INTERVAL: int = int(get_env("PING_INTERVAL"))