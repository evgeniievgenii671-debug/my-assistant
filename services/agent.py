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

# ТОЛЬКО ПРОВЕРЕННЫЕ МОДЕЛИ ДЛЯ РУССКОГО
RELIABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "openai/gpt-oss-120b",
]


async def ask_agent(user_id, user_text):
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

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

    last_error = None
    for model in RELIABLE_MODELS:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=200,
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"Модель {model} вернула пусто")
                continue

            logger.info(f"✅ Ответила модель: {model}")

            if add_message:
                try:
                    await add_message(user_id, "assistant", text)
                except Exception:
                    pass

            return text

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Модель {model} не сработала: {e}")
            continue

    logger.error(f"Все модели упали. Последняя: {last_error}")
    return "Извините, сейчас не могу ответить 🙏"
