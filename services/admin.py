import logging

from config import ADMIN_ID
from services.memory import get_profile

logger = logging.getLogger(__name__)


async def notify_admin(
    bot,
    user,
    user_text: str,
    bot_answer: str,
    is_voice: bool = False,
):
    """Отправляет админу полный диалог с источником."""
    if not ADMIN_ID:
        return

    # Загружаем профиль для источника и города
    profile = await get_profile(user.id) or {}

    prefix = "🎤 Голосовое" if is_voice else "📩 Текст"

    lines = [f"<b>{prefix}</b>", ""]

    if profile.get("source"):
        lines.append(f"📍 Источник: <b>{profile['source']}</b>")
    if profile.get("city"):
        lines.append(f"🏙 Город: {profile['city']}")
    if profile.get("business"):
        lines.append(f"💼 Бизнес: {profile['business']}")

    if len(lines) > 2:
        lines.append("")

    lines.append(f"👤 {user.full_name}")
    lines.append(f"🔗 @{user.username or '—'}")
    lines.append(f"🆔 <code>{user.id}</code>")
    lines.append("")
    lines.append(f"👤 <b>Клиент:</b> {user_text}")
    lines.append("")
    lines.append(f"🤖 <b>Бот:</b> {bot_answer}")

    message = "\n".join(lines)

    try:
        await bot.send_message(ADMIN_ID, message, parse_mode="HTML")
    except Exception:
        logger.exception("Ошибка отправки админу")
