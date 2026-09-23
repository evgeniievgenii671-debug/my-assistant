import logging
import re

from services.memory import update_profile, get_profile

logger = logging.getLogger(__name__)

# Телефон: +7/8 + минимум 10 цифр, с разделителями
PHONE_RE = re.compile(r"(\+?\d[\d\s\-\(\)]{9,}\d)")

# Имя: строго после "меня зовут", "моё имя", "зовите меня"
NAME_RE = re.compile(
    r"(?:меня зовут|мо[её] имя|зовите меня|можно просто)\s+"
    r"([А-ЯЁ][а-яё]{1,20}|[A-Z][a-z]{1,20})",
    re.IGNORECASE,
)

# Бизнес: "у меня салон", "занимаюсь продажами"
BUSINESS_RE = re.compile(
    r"(?:у меня|мы делаем|занимаемся|мой бизнес|владелец)\s+"
    r"([а-яёa-z\s]{3,40})",
    re.IGNORECASE,
)

# Стоп-слова — если они рядом с триггером, не сохраняем
STOP_WORDS = {
    "помните", "знаете", "помнишь", "думаете", "хотите",
    "можете", "звать", "спросил", "говорил",
}

CITIES = [
    "алматы", "астана", "нур-султан", "шымкент", "караганда",
    "актобе", "тараз", "павлодар", "усть-каменогорск",
    "семей", "атырау", "костанай", "кызылорда", "уральск",
    "петропавловск", "актау", "темиртау", "туркестан",
]


def _valid_name(name: str) -> bool:
    """Проверяет, что это реально имя, а не случайное слово."""
    if not name:
        return False
    if len(name) < 2 or len(name) > 30:
        return False
    if name.lower() in STOP_WORDS:
        return False
    return True


async def extract_and_save(user_id: int, text: str) -> None:
    """Извлекает данные из сообщения и сохраняет в профиль."""
    if not text:
        return

    # Загружаем текущий профиль
    profile = await get_profile(user_id) or {}
    fields = {}
    lower = text.lower()

    # --- ТЕЛЕФОН ---
    # Сохраняем только если в профиле ещё нет
    if not profile.get("phone"):
        phone_match = PHONE_RE.search(text)
        if phone_match:
            phone = phone_match.group(1).strip()
            digits = re.sub(r"\D", "", phone)
            if 10 <= len(digits) <= 13:
                fields["phone"] = phone

    # --- ИМЯ ---
    # Сохраняем только если нет или если нашли новое валидное
    name_match = NAME_RE.search(text)
    if name_match:
        name = name_match.group(1).strip().capitalize()
        if _valid_name(name) and name != profile.get("name"):
            fields["name"] = name

    # --- БИЗНЕС ---
    if not profile.get("business"):
        business_match = BUSINESS_RE.search(text)
        if business_match:
            biz = business_match.group(1).strip()
            biz = re.split(r"[.,!?]", biz)[0].strip()
            if 3 <= len(biz) <= 40:
                fields["business"] = biz

    # --- ГОРОД ---
    if not profile.get("city"):
        for city in CITIES:
            if city in lower:
                fields["city"] = city.capitalize()
                break

    if fields:
        try:
            await update_profile(user_id, **fields)
            logger.info("Профиль %s обновлён: %s", user_id, fields)
        except Exception:
            logger.exception("Ошибка сохранения профиля")
