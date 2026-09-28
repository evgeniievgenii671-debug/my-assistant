import logging
from aiogram import Router, types
from aiogram.filters import Command

from services.agent import ask_agent

logger = logging.getLogger(__name__)
router = Router()


@router.message()
async def handle_text(message: types.Message):
    """Обработка всех текстовых сообщений."""
    if not message.text:
        return

    # Игнорируем команды (их обрабатывают другие хендлеры)
    if message.text.startswith("/"):
        return

    try:
        answer = await ask_agent(message.from_user.id, message.text)

        # Защита: если ответ пустой — подставляем fallback
        if not answer or not str(answer).strip():
            logger.warning("ask_agent вернул пустой ответ, отправляем fallback")
            answer = "Извините, не могу ответить. Попробуйте ещё раз 🙏"

        await message.answer(answer)

    except Exception as e:
        logger.error(f"Ошибка в handle_text: {e}")
        try:
            await message.answer("Извините, произошла ошибка. Попробуйте позже 🙏")
        except Exception:
            pass
