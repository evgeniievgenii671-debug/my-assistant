import logging
from aiogram import Router, types

from services.agent import ask_agent

logger = logging.getLogger(__name__)
router = Router()


@router.message()
async def handle_text(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return

    try:
        answer = await ask_agent(message.from_user.id, message.text)
    except Exception as e:
        logger.error(f"Ошибка ask_agent: {e}")
        answer = None

    if not answer or not str(answer).strip():
        answer = "Извините, не могу ответить. Попробуйте ещё раз 🙏"

    try:
        await message.answer(str(answer))
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
