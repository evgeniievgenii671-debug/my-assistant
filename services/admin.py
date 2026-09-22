import logging
from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def notify_admin(bot, user, user_text: str, bot_answer: str, is_voice: bool = False):
    """Отправляет админу полный диалог: клиент + ответ бота."""
    if not ADMIN_ID:
        return
    prefix = "🎤 Голосовое" if is_voice else "📩 Текст"
    message = (
        f"<b>{prefix}</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🔗 @{user.username or '—'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"👤 <b>Клиент:</b> {user_text}\n\n"
        f"🤖 <b>Бот:</b> {bot_answer}"
    )
    try:
        await bot.send_message(ADMIN_ID, message, parse_mode="HTML")
    except Exception:
        logger.exception("Ошибка отправки админу")
