import os
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
1. Отвечай МАКСИМУМ 1-2 предложениями.
2. Задавай ТОЛЬКО ОДИН вопрос.
3. ЗАПРЕЩЕНЫ вступления ("Привет", "Конечно", "Отлично").
4. Не пиши "Бот:" или "Ассистент:".
5. Если клиент назвал имя — используй. Не хочет — не настаивай.
6. Цены не называй: "Зависит от задачи".
7. Пиши грамотно по-русски.
"""

# Что исключаем: TTS, арабские, whisper, слабые
BAD_MODELS = [
    "whisper", "tts", "orpheus", "guard",
    "arabic", "saudi", "allam",
    "llama-3.2-1b", "llama-3.2-3b",
]

# Приоритет моделей (сначала самые умные для русского)
PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2",
    "meta-llama/llama-4-maverick",
    "meta-llama/llama-4-scout",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
    "openai/gpt-oss-20b",  # последний вариант
]


async def get_good_models() -> list:
    """Запрашивает у Groq актуальный список моделей."""
    try:
        response = await client.models.list()
        all_models = [m.id for m in response.data]
        logger.info(f"Всего моделей: {len(all_models)}")

        good = [m for m in all_models if not any(bad in m.lower() for bad in BAD_MODELS)]
        logger.info(f"Подходящих: {good}")
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
    # Добавляем оставшиеся
    for m in models:
        if m not in result:
            result.append(m)
    return result


async def ask_agent(user_id, user_text):
    if not OPENAI_API_KEY:
        logger.error("API-ключ не задан!")
        return "Ошибка конфигурации."

    # История
    add_message = None
    try:
        from services.memory import get_history, add_message
        history = await get_history(user_id)
        await add_message(user_id, "user", user_text)
        history = history + [{"role": "user", "content": user_text}]
    except Exception as e:
        logger.warning(f"Память недоступна: {e}")
        history = [{"role": "user", "content": user_text}]

    # Получаем актуальные модели
    models = await get_good_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    # Сортируем по приоритету
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
                max_tokens=200,
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"{model}: пустой ответ")
                continue

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
