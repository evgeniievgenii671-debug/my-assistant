import os
import re
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

SYSTEM_PROMPT = """Ты — вежливый ассистент Евгения Алексеевича.
МЫ ЗАНИМАЕМСЯ: Telegram/WhatsApp-боты, сайты, AI-ассистенты для бизнеса.

ПРАВИЛА:
1. Отвечай 1-2 предложениями. Никаких длинных монологов.
2. Задавай ТОЛЬКО ОДИН вопрос за раз.
3. ИМЯ — НЕ ОБЯЗАТЕЛЬНО! Если клиент не назвал имя с первого раза, больше НЕ СПРАШИВАЙ.
4. НЕ ПОВТОРЯЙ имя в каждом ответе — только когда уместно (1 раз в 3-4 сообщения).
5. Понимай короткие ответы: «Все», «Да», «Ну» = согласие/подтверждение.
6. Если клиент написал «Стоимость» — сначала назови вилку: "Зависит от задачи. Ориентир — от 50 000 тг", потом уточняй.
7. Не пиши обрывки типа "Вахтанг." — только законченные предложения.
8. Если не понял — переспроси коротко: "Уточните, пожалуйста".

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
Клиент: Стоимость
Бот: Зависит от задачи. Ориентир — от 50 000 тг. Что именно нужно?

Клиент: Чат-бот
Бот: Понял! Для какого канала — Telegram или WhatsApp?

Клиент: Оба
Бот: Отлично! Что должен делать бот — продажи, поддержка?

Клиент: Все
Бот: Понял! Оставьте номер — обсудим детали?
"""

# Плохие модели — исключаем
BAD_MODELS = [
    "whisper", "tts", "orpheus", "guard",
    "arabic", "saudi", "allam",
    "llama-3.2-1b", "llama-3.2-3b",
]

PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2",
    "meta-llama/llama-4-maverick",
    "llama-3.1-8b-instant",
]


async def get_good_models() -> list:
    """Запрашивает актуальный список моделей у Groq."""
    try:
        response = await client.models.list()
        all_models = [m.id for m in response.data]
        good = [m for m in all_models if not any(bad in m.lower() for bad in BAD_MODELS)]
        logger.info(f"Подходящих моделей: {good}")
        return good
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        return []


def sort_by_priority(models: list) -> list:
    """Сортирует модели по приоритету."""
    result = []
    for pref in PRIORITY:
        for m in models:
            if pref in m.lower() and m not in result:
                result.append(m)
    for m in models:
        if m not in result:
            result.append(m)
    return result


def extract_phone(text: str):
    """Ищет телефон в тексте."""
    patterns = [
        r"\+7[\s\-\(\)]?\d{3}[\s\-\(\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
        r"8[\s\-\(\)]?\d{3}[\s\-\(\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
        r"\d{10,11}",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)
    return None


async def auto_save_profile(user_id: int, user_text: str):
    """Автоматически сохраняет телефон из сообщения."""
    try:
        from services.memory import update_profile
        phone = extract_phone(user_text)
        if phone:
            await update_profile(user_id, phone=phone)
            logger.info(f"📱 Телефон сохранён для {user_id}: {phone}")
    except Exception as e:
        logger.warning(f"Не удалось сохранить телефон: {e}")


async def ask_agent(user_id, user_text):
    """Главная функция — принимает сообщение, возвращает ответ."""
    if not OPENAI_API_KEY:
        logger.error("API-ключ не задан!")
        return "Ошибка конфигурации."

    # Загружаем историю
    add_message = None
    try:
        from services.memory import get_history, add_message
        history = await get_history(user_id)
        await add_message(user_id, "user", user_text)
        history = history + [{"role": "user", "content": user_text}]
    except Exception as e:
        logger.warning(f"Память недоступна: {e}")
        history = [{"role": "user", "content": user_text}]

    # Автосохранение телефона
    await auto_save_profile(user_id, user_text)

    # Получаем актуальные модели
    models = await get_good_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    models_to_try = sort_by_priority(models)[:5]
    logger.info(f"Порядок попыток: {models_to_try}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

    last_error = None
    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=300,
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"{model}: пустой ответ")
                continue

            # Добавляем точку, если обрыв
            text = text.strip()
            if text and text[-1] not in ".!?…":
                text += "."

            logger.info(f"✅ Ответила: {model}")

            if add_message:
                try:
                    await add_message(user_id, "assistant", text)
                except Exception:
                    pass

            return text

        except Exception as e:
            last_error = str(e)
            logger.warning(f"{model} не сработала: {e}")
            continue

    logger.error(f"Все упали. Последняя: {last_error}")
    return "Извините, сейчас не могу ответить 🙏"
