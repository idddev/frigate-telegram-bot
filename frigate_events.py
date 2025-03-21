from datetime import datetime
import logging
from typing import Any, Coroutine, Optional, TypeVar
import asyncio

from telegram import Bot, InputFile, Update
from telegram.ext import CallbackContext
from pytapo import Tapo

from envs import TELEGRAM_CHAT_ID
import frigate_api

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T], timeout: float = 10) -> T:
    """
    Ejecuta una coroutine en el event loop principal desde un contexto sincrónico
    y devuelve su resultado, esperando hasta `timeout` segundos.
    """
    loop = get_main_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)


logger: logging.Logger = logging.getLogger(__name__)

# Variables globales internas (inicialmente None)
_bot: Optional[Bot] = None
_main_loop: Optional[asyncio.AbstractEventLoop] = None
_tapo_cam: Optional[Tapo] = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def get_main_loop() -> asyncio.AbstractEventLoop:
    if _main_loop is None:
        raise ValueError("El event loop principal no ha sido asignado.")
    return _main_loop


def set_bot(bot_obj: Bot) -> None:
    global _bot
    _bot = bot_obj


def get_bot() -> Bot:
    if _bot is None:
        raise ValueError("El bot no ha sido inicializado.")
    return _bot


def set_tapo_cam(ip: str, user: str, password: str) -> None:
    global _tapo_cam
    _tapo_cam = Tapo(ip, user, password)


def get_tapo_cam() -> Tapo:
    if _tapo_cam is None:
        raise ValueError("La cámara Tapo no ha sido inicializada.")
    return _tapo_cam


# === Funciones para procesar eventos MQTT ===
def process_frigate_event(data: dict[str, Any]) -> None:
    try:
        event_data = data.get("after", {})
        logger.info("Procesando evento de Frigate: %s", event_data)
        
        event_id = event_data.get("id")
        camera = event_data.get("camera")
        label = event_data.get("label")
        details = event_data.get("details", "Sin detalles adicionales")
        stationary = event_data.get("stationary", False)
        
        # Ignoramos eventos estacionarios
        if stationary:
            logger.info("Evento estacionario detectado, ignorando.")
            return

        if event_id:
            caption = (
                f"Evento detectado:\n"
                f"Cámara: {camera}\n"
                f"Etiqueta: {label}\n"
                f"ID: {event_id}\n"
                f"Detalles: {details}"
            )
            logger.info("Enviando notificación de evento: %s", caption)

            # Obtenemos la url de la instantánea
            snapshot = frigate_api.get_event_snapshot(event_id)

            if snapshot:
                result = run_async(
                    get_bot().send_photo(
                        chat_id=TELEGRAM_CHAT_ID, photo=snapshot, caption=caption
                    )
                )
            else:
                result = run_async(
                    get_bot().send_message(chat_id=TELEGRAM_CHAT_ID, text=caption)
                )
            
            logger.info(
                f"Se envió notificación de evento ({'snapshot' if snapshot else 'texto'}): {event_id} -> {result}"
            )
    except Exception as e:
        logger.error("Error procesando evento de Frigate: %s", e)

def process_frigate_review(data: dict[str, Any]) -> None:
    try:
        review_data = data.get("after", {})
        logger.info("Procesando revisión de Frigate: %s", review_data)
        
        review_id = review_data.get("id")
        camera = review_data.get("camera")
        start_time = review_data.get("start_time")
        
        # Convertir start_time a formato amigable si existe
        friendly_time = "Desconocido"
        if start_time:
            friendly_time = datetime.fromtimestamp(start_time).strftime("%d/%m/%Y %H:%M:%S")
        
        # Obtener los objetos detectados desde la clave 'data'
        review_details = review_data.get("data", {})
        objects_detected: list[str] = review_details.get("objects", [])
        objects_str = ", ".join(objects_detected) if objects_detected else "Ninguno"
        
        if review_id:
            caption = (
                f"Revisión detectada:\n"
                f"Cámara: {camera}\n"
                f"ID: {review_id}\n"
                f"Inicio: {friendly_time}\n"
                f"Objetos detectados: {objects_str}"
            )
            logger.info("Enviando notificación de revisión: %s", caption)
            
            review_preview = frigate_api.get_review_preview(review_id)
            if review_preview:
                animation = InputFile(review_preview, filename=f"review_{review_id}.gif")
                result = run_async(
                    get_bot().send_animation(
                        chat_id=TELEGRAM_CHAT_ID, 
                        animation=animation, 
                        caption=caption
                    )
                )
            else:
                result = run_async(
                    get_bot().send_message(
                        chat_id=TELEGRAM_CHAT_ID, 
                        text=caption)
                )            
            logger.info("Se envió notificación de revisión: %s -> %s", review_id, result)
    except Exception as e:
        logger.error("Error procesando revisión de Frigate: %s", e)


# === Handlers para el bot de Telegram ===
async def start(update: Update, context: CallbackContext) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "nubi.casa - Bot de notificaciones\n"
        "Usa /get <snapshot_id> para ver detalles o /move <preset> para mover la cámara."
    )

async def move_camera(update: Update, context: CallbackContext) -> None:
    if not update.message:
        return
    if context.args:
        preset = context.args[0]
        try:
            result = await asyncio.to_thread(get_tapo_cam().setPreset, preset)
            await update.message.reply_text(
                f"Moviendo cámara al preset {preset}."
            )
        except Exception as e:
            await update.message.reply_text(f"Error al mover la cámara: {e}")
    else:
        await update.message.reply_text("Uso correcto: /move <preset>")

async def watch_camera(update: Update, context: CallbackContext) -> None:
    if not update.message:
        return
    if context.args:
        camera_id = context.args[0]
        try:
            snapshot = frigate_api.get_camera_snapshot(camera_id)
            if snapshot:
                await update.message.reply_photo(
                    photo=snapshot,
                    caption=f"Snapshot de la cámara *{camera_id}*."
                )
            else:
                await update.message.reply_text(f"No se pudo obtener snapshot de la cámara {camera_id}.")
        except Exception as e:
            await update.message.reply_text(f"Error al obtener camara: {e}")
    else:
        await update.message.reply_text("Uso correcto: /watch <camera_id>")