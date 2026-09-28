import logging
from aiogram import Router, types
from config import MANAGER_CHAT_ID
from services.agent import ask_agent

logger = logging.getLogger(__name__)
router = Router()


@router.message()
async def handle_text(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return

    user_id = message.from_user.id
    user_text = message.text
    username = message.from_user.username or "—"
    full_name = message.from_user.full_name

    # Генерируем ответ
    try:
        answer = await ask_agent(user_id, user_text)
    except Exception as e:
        logger.error(f"Ошибка ask_agent: {e}")
        answer = None

    if not answer or not str(answer).strip():
        answer = "Извините, не могу ответить. Попробуйте ещё раз 🙏"

    # Отправляем клиенту
    try:
        await message.answer(str(answer))
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")

    # Уведомление менеджеру — ПОСЛЕ ответа, с полным диалогом
    if MANAGER_CHAT_ID:
        try:
            await message.bot.send_message(
                MANAGER_CHAT_ID,
                f"🔔 <b>Новый диалог</b>\n\n"
                f"👤 Клиент: {full_name}\n"
                f"📱 @{username}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                f"💬 <b>Написал:</b> {user_text}\n\n"
                f"🤖 <b>Бот ответил:</b> {answer}"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")
