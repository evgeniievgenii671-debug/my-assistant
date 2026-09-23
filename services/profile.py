import logging
import re

from services.memory import update_profile

logger = logging.getLogger(__name__)

# Телефон: +7..., 8..., с пробелами, скобками, дефисами
PHONE_RE = re.compile(
    r"(\+?\d[\d\s\-\(\)]{9,}\d)"
)

# Имя: "меня зовут X", "я X", "это X" — одна или два слова
NAME_RE = re.compile(
    r"(?:меня зовут|моё имя|мое имя|я)\s+([А-ЯЁA-Z][а-яёa-z]+)",
    re.IGNORECASE,
)

# Бизнес: "у меня X", "я владелец X", "занимаюсь X"
BUSINESS_RE = re.compile(
    r"(?:у меня|мы делаем|занимаюсь|владелец|мой бизнес)\s+"
    r"([а-яёa-z\s]{3,40})",
    re.IGNORECASE,
)

# Города Казахстана
CITIES = [
    "алматы", "астана", "нур-султан", "шымкент", "караганда",
    "актобе", "тараз", "павлодар", "усть-каменогорск",
    "семей", "атырау", "костанай", "кызылорда", "уральск",
    "петропавловск", "актау", "темиртау", "туркестан",
]


async def extract_and_save(user_id: int, text: str) -> None:
    """Извлекает данные из сообщения и сохраняет в профиль."""
    if not text:
        return

    fields = {}
    lower = text.lower()

    # Телефон
    phone_match = PHONE_RE.search(text)
    if phone_match:
        phone = phone_match.group(1).strip()
        # Минимум 10 цифр
        if len(re.sub(r"\D", "", phone)) >= 10:
            fields["phone"] = phone

    # Имя
    name_match = NAME_RE.search(text)
    if name_match:
        fields["name"] = name_match.group(1).strip().capitalize()

    # Бизнес
    business_match = BUSINESS_RE.search(text)
    if business_match:
        biz = business_match.group(1).strip()
        # Убираем слова после запятой/точки
        biz = re.split(r"[.,!?]", biz)[0].strip()
        if 3 <= len(biz) <= 40:
            fields["business"] = biz

    # Город
    for city in CITIES:
        if city in lower:
            fields["city"] = city.capitalize()
            break

    if fields:
        try:
            await update_profile(user_id, **fields)
            logger.info("Профиль обновлён для %s: %s", user_id, fields)
        except Exception:
            logger.exception("Ошибка сохранения профиля")
