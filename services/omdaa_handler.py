import logging
from aiohttp import web

from services.agent import ask_agent
from services.omdaa import send_whatsapp_message

logger = logging.getLogger(__name__)


async def omdaa_webhook_handler(request: web.Request) -> web.Response:
    """Принимает вебхук от Omdaa (WhatsApp-сообщение) и отвечает."""
    try:
        data = await request.json()
        logger.info("Omdaa webhook: %s", data)

        # Извлекаем данные сообщения
        message = data.get("message", {}) or data
        from_number = message.get("from") or data.get("from")
        text = (
            message.get("text", {}).get("body")
            or message.get("body")
            or data.get("text")
        )

        if not from_number or not text:
            return web.json_response({"status": "ignored"})

        # Проверяем — не групповое ли сообщение
        if "@g.us" in str(from_number):
            logger.info("Групповое сообщение — игнорируем")
            return web.json_response({"status": "group_ignored"})

        # Получаем ответ от AI
        reply = await ask_agent(int(from_number) if str(from_number).isdigit() else hash(from_number), text)

        # Отправляем ответ в WhatsApp
        await send_whatsapp_message(from_number, reply)

        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception("Ошибка обработки вебхука Omdaa")
        return web.json_response({"status": "error", "message": str(e)}, status=500)
