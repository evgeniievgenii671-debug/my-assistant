import logging
from aiohttp import web

from services.agent import ask_agent
from services.omdaa import send_whatsapp_message

logger = logging.getLogger(__name__)


async def omdaa_webhook_handler(request):
    """Принимает вебхук от Omdaa (WhatsApp-сообщения)."""
    try:
        data = await request.json()
        event = data.get("event")

        # Обрабатываем только новые сообщения
        if event != "message.received":
            return web.json_response({"status": "ignored"})

        msg = data.get("data", {}).get("message", {})
        sender = data.get("data", {}).get("from")  # номер отправителя
        text = msg.get("text", {}).get("body") or msg.get("body", "")

        if not sender or not text:
            logger.warning(f"Пустое сообщение от Omdaa: {data}")
            return web.json_response({"status": "empty"})

        logger.info(f"📱 WhatsApp от {sender}: {text}")

        # Генерируем ответ через AI
        answer = await ask_agent(sender, text)

        if not answer or not answer.strip():
            answer = "Извините, не могу ответить. Попробуйте позже 🙏"

        # Отправляем ответ обратно в WhatsApp
        await send_whatsapp_message(sender, answer)

        return web.json_response({"status": "ok"})

    except Exception as e:
        logger.exception(f"Ошибка в omdaa_webhook_handler: {e}")
        return web.json_response({"status": "error"}, status=500)
