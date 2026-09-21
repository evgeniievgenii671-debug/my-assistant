import logging
from aiohttp import web

from services.agent import ask_agent
from services.omdaa import send_whatsapp_message

logger = logging.getLogger(__name__)


async def omdaa_webhook_handler(request: web.Request) -> web.Response:
    """Принимает вебхук от Omdaa (WhatsApp-сообщение) и отвечает."""
    try:
        data = await request.json()
        event = data.get("event")

        # Обрабатываем только новые сообщения
        if event != "message.received":
            return web.json_response({"status": "ignored", "event": event})

        msg = data.get("data", {}).get("message", {})

        # Игнорируем свои исходящие
        if msg.get("fromMe"):
            return web.json_response({"status": "self_ignored"})

        # Игнорируем группы
        if msg.get("isGroup"):
            return web.json_response({"status": "group_ignored"})

        # Текст сообщения
        content = msg.get("content", {}) or {}
        text = content.get("text") or msg.get("text")
        if not text:
            logger.info("Сообщение без текста — игнорируем")
            return web.json_response({"status": "no_text"})

        # Номер отправителя (убираем @s.whatsapp.net)
        remote_jid = msg.get("remoteJid", "")
        phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
        if not phone:
            return web.json_response({"status": "no_phone"})

        logger.info("Сообщение от %s: %s", phone, text)

        # Уникальный числовой ID для истории
        user_id = int(phone) if phone.isdigit() else abs(hash(phone))

        # Ответ AI
        reply = await ask_agent(user_id, text)

        # Отправляем обратно в WhatsApp
        await send_whatsapp_message(phone, reply)

        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception("Ошибка обработки вебхука Omdaa")
        return web.json_response({"status": "error", "message": str(e)}, status=500)
