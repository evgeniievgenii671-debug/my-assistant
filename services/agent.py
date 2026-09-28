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

СТРОГИЕ ПРАВИЛА:
1. Пиши ТОЛЬКО законченными предложениями. Никаких обрывков.
2. Отвечай 1-2 предложениями. Максимум 25 слов.
3. Задавай ТОЛЬКО ОДИН вопрос.
4. ЗАПРЕЩЕНЫ вступления ("Привет", "Конечно", "Отлично").
5. ЗАПРЕЩЕНО выдумывать услуги, которых нет. Мы НЕ делаем видеосвязь, звонки, консультации по телефону.
6. Не пиши "Бот:" или "Ассистент:".
7. Если клиент назвал имя — используй его. Не хочет — не настаивай.
8. Цены не называй: "Зависит от задачи".
9. Пиши грамотно по-русски.

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
Клиент: Евгений
Бот: Приятно познакомиться! Какая из услуг вас интересует?

Клиент: Сайт для салона
Бот: Отлично! Какой именно салон — красоты, барбершоп?

Клиент: Как вы работаете?
Бот: Мы общаемся в чате — пишем вам и отвечаем на вопросы.
"""

# ТОЛЬКО ХОРОШИЕ МОДЕЛИ (без TTS, арабских, слабых)
BAD_MODELS = ["whisper", "tts", "orpheus", "guard", "arabic", "saudi", "allam",
              "llama-3.2-1b", "llama-3.2-3b", "qwen", "gpt-oss-20b"]

PRIORITY = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2",
    "meta-llama/llama-4-maverick",
    "llama-3.1-8b-instant",
]


async def get_good_models() -> list:
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
    result = []
    for pref in PRIORITY:
        for m in models:
            if pref in m.lower() and m not in result:
                result.append(m)
    for m in models:
        if m not in result:
            result.append(m)
    return result


async def ask_agent(user_id, user_text):
    if not OPENAI_API_KEY:
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

    # Модели
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
                max_tokens=300,  # Увеличили: чтобы не обрывался
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"{model}: пустой ответ")
                continue

            # Проверка на обрыв (заканчивается ли точкой/!/?)
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
