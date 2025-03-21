import json
import logging
import threading
import asyncio
import paho.mqtt.client as mqtt
from telegram.ext import ApplicationBuilder, CommandHandler
from envs import CAMERA_IP, CAMERA_PASSWORD, CAMERA_USER, MQTT_BROKER, MQTT_PORT, MQTT_TOPICS, TELEGRAM_TOKEN
from ping_cron import ping_cron

# Configurar logging para mostrar en terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicializar la aplicación de Telegram
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Importar funciones y variables de frigate_events
import frigate_events
frigate_events.set_bot(app.bot)
frigate_events.set_tapo_cam(CAMERA_IP, CAMERA_USER, CAMERA_PASSWORD)

# Registrar handlers de comandos
app.add_handler(CommandHandler("start", frigate_events.start))
app.add_handler(CommandHandler("watch", frigate_events.watch_camera))
app.add_handler(CommandHandler("move", frigate_events.move_camera))

# Configurar el cliente MQTT
def on_connect(client, userdata, flags, rc):
    logger.info("Conectado al broker MQTT con código %s", rc)
    for topic in MQTT_TOPICS:
        client.subscribe(topic)
        logger.info("Suscrito al tópico: %s", topic)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        topic = msg.topic
        logger.info("Mensaje recibido en el tópico: %s", topic)
        if topic == "frigate/events":
            frigate_events.process_frigate_event(data)
        elif topic == "frigate/reviews":
            frigate_events.process_frigate_review(data)
        else:
            logger.info("Tópico no manejado: %s", topic)
    except Exception as e:
        logger.error("Error procesando mensaje MQTT: %s", e)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Iniciar el loop MQTT en un hilo separado
threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()

# Antes de iniciar el bot, asignamos el event loop que esté en uso.
# Esto permite que el módulo frigate_events use el mismo loop para enviar notificaciones.
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)

# Iniciamos el cron de ping en el loop principal
main_loop.create_task(ping_cron())

frigate_events.set_main_loop(main_loop)

# Ejecutar el bot con run_polling (método sincrónico que bloquea)
try:    
    # Si el bot falla, run_polling() saldrá y se cerrará el loop.
    # De esta forma, todo se detiene.
    app.run_polling()  # Se usa el close_loop por defecto (True)
except Exception as e:
    logger.error("Error ejecutando el bot: %s", e)
