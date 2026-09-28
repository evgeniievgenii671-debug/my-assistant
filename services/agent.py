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

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Отвечай МАКСИМУМ 1 предложением.
2. Никогда не пиши больше 20 слов.
3. Задавай ТОЛЬКО ОДИН вопрос.
4. ЗАПРЕЩЕНЫ вступления ("Привет", "Конечно", "Отлично").
5. ЗАПРЕЩЕНО перечислять варианты.
6. Не пиши "Бот:" или "Ассистент:".
7. Если клиент назвал имя — используй. Не назвал — спроси один раз. Не хочет — иди дальше.
8. Цены не называй. Только: "Зависит от задачи".
9. Пиши грамотно.
"""

# Плохие модели: арабские, голосовые, слабые
BAD_MODELS = [
    "allam", "whisper", "tts", "guard",
    "gemma2-9b", "gemma-7b",
    "llama-3.2-1b", "llama-3.2-3b",
    "qwen", "mixtral-8x7b",
    "llama-3.1-70b-versatile",  # decommissioned
]


async def get_good_models() -> list:
    """Запрашивает у Groq список моделей и фильтрует плохие."""
    try:
        response = await client.models.list()
        all_models = [m.id for m in response.data]
        logger.info(f"Всего моделей у Groq: {len(all_models)}")

        good = [m for m in all_models if not any(bad in m.lower() for bad in BAD_MODELS)]
        logger.info(f"Подходящих моделей: {good}")
        return good
    except Exception as e:
        logger.error(f"Не удалось получить список моделей: {e}")
        return []


def pick_priority_model(models: list):
    """Выбирает лучшую по приоритету."""
    priorities = [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b",
        "llama-3.1-8b-instant",
        "llama-3.1-8b",
        "llama3-70b",
        "llama3-8b",
    ]
    for pref in priorities:
        for m in models:
            if pref in m.lower():
                return m
    return models[0] if models else None


async def ask_agent(user_id, user_text):
    if not OPENAI_API_KEY:
        logger.error("API-ключ не задан!")
        return "Ошибка конфигурации: не задан API-ключ."

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

    # Получаем список рабочих моделей
    models = await get_good_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    best = pick_priority_model(models)
    logger.info(f"Выбрана модель: {best}")

    # Лучшая — первая, потом остальные
    models_to_try = [best] + [m for m in models if m != best]
    models_to_try = models_to_try[:5]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

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
                logger.warning(f"Модель {model} вернула пусто, пробуем следующую")
                continue

            logger.info(f"✅ Ответила модель: {model}")

            if add_message:
                try:
                    await add_message(user_id, "assistant", text)
                except Exception:
                    pass

            return text

        except Exception as e:
            logger.warning(f"Модель {model} не сработала: {e}")
            continue

    return "Извините, сейчас не могу ответить, попробуйте позже 🙏"
