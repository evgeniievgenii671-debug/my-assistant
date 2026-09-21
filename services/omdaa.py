import logging
import aiohttp
from config import OMDAA_API_KEY, OMDAA_SESSION_ID

logger = logging.getLogger(__name__)


async def send_whatsapp_message(to: str, text: str):
    """Отправляет сообщение в WhatsApp через API Omdaa."""
    if not OMDAA_API_KEY or not OMDAA_SESSION_ID:
        logger.warning("Omdaa не настроен")
        return

    url = "https://omdaa.com/api/v1/messages/send"
    headers = {
        "Authorization": f"Bearer {OMDAA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "sessionId": OMDAA_SESSION_ID,
        "to": to,
        "message": text,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                body = await resp.text()
                if resp.status != 200:
                    logger.error("Ошибка Omdaa %s: %s", resp.status, body)
                else:
                    logger.info("Сообщение отправлено в WhatsApp %s", to)
    except Exception:
        logger.exception("Не удалось отправить в WhatsApp")
