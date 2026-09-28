import logging
from aiogram import Router, types
from config import ADMIN_ID
from services.agent import ask_agent

logger = logging.getLogger(__name__)
router = Router()

# Логируем ADMIN_ID при импорте
logger.info(f"🔔 ADMIN_ID загружен: {ADMIN_ID} (тип: {type(ADMIN_ID).__name__})")


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

    # Уведомление админу
    logger.info(f"🔔 Пробуем отправить уведомление на ADMIN_ID={ADMIN_ID}")
    if ADMIN_ID and ADMIN_ID != 0:
        try:
            sent = await message.bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Новый диалог</b>\n\n"
                f"👤 Клиент: {full_name}\n"
                f"📱 @{username}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                f"💬 <b>Написал:</b> {user_text}\n\n"
                f"🤖 <b>Бот ответил:</b> {answer}"
            )
            logger.info(f"✅ Уведомление отправлено! message_id={sent.message_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления: {e}")
    else:
        logger.warning(f"⚠️ ADMIN_ID = {ADMIN_ID} — уведомление не отправлено")
