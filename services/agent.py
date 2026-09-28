import os
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

SYSTEM_PROMPT = """Ты — вежливый ассистент Евгения Алексеевича.
МЫ ЗАНИМАЕМСЯ: Telegram/WhatsApp-боты, сайты, AI-ассистенты для бизнеса.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Отвечай МАКСИМУМ 1 предложением. Это НЕ рекомендация, а ЗАКОН.
2. Никогда не пиши больше 20 слов. Считай слова!
3. Задавай ТОЛЬКО ОДИН вопрос.
4. ЗАПРЕЩЕНЫ любые вступления ("Привет", "Конечно", "Отлично", "Мы рады"). Сразу вопрос или ответ.
5. ЗАПРЕЩЕНО перечислять варианты. Только суть.
6. Не пиши "Бот:" или "Ассистент:".
7. Если клиент назвал имя — используй. Не назвал — спроси один раз. Не хочет — иди дальше.
8. Цены не называй. Только: "Зависит от задачи".
9. Пиши грамотно.
"""


async def get_available_models() -> list:
    try:
        response = await client.models.list()
        models = [m.id for m in response.data]
        logger.info(f"Доступные модели: {models}")
        return models
    except Exception as e:
        logger.error(f"Не удалось получить список моделей: {e}")
        return []


def pick_best_model(models: list):
    BAD_MODELS = ["allam", "whisper", "tts", "guard", "gemma2-9b", "llama-3.2-1b", "llama-3.2-3b"]
    good_models = [m for m in models if not any(bad in m.lower() for bad in BAD_MODELS)]
    if not good_models:
        good_models = models

    priorities = [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b",
        "llama-3.1-70b-versatile",
        "llama3-70b",
        "llama-3.1-8b-instant",
        "llama3-8b",
    ]
    for pref in priorities:
        for m in good_models:
            if pref in m.lower():
                return m
    return good_models[0] if good_models else None


async def ask_agent(user_id, user_text):
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY / GROQ_API_KEY не задан!")
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

    models = await get_available_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    best = pick_best_model(models)
    logger.info(f"Выбрана модель: {best}")

    models_to_try = [best] + [m for m in models if m != best]
    models_to_try = models_to_try[:5]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=150,
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"Модель {model} вернула пустой ответ")
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
