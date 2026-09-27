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
Отвечай ТОЛЬКО на русском, грамотно, дружелюбно.

МЫ ЗАНИМАЕМСЯ:
- Разработкой Telegram и WhatsApp-ботов
- Созданием сайтов
- AI-ассистентами для бизнеса

ПРАВИЛА:
1. Будь вежливым и приветливым. Помогай клиенту.
2. Отвечай 1-2 предложениями. ОДИН вопрос за раз.
3. Не пиши в начале "Бот:" или "Ассистент:". Сразу текст.
4. Если клиент назвал имя — используй его. Если не назвал — спроси один раз.
5. Если клиент отказывается называть имя — не настаивай. Скажи "Хорошо, без проблем!" и продолжай.
6. Расскажи про наши услуги, помоги выбрать подходящее решение.
7. Точные цены не называй — говори: "Стоимость зависит от задачи, давайте обсудим детали".
8. Пиши грамотно, без ошибок.

ПРИМЕРЫ:
Клиент: Здравствуйте, хочу бота для магазина
Бот: Здравствуйте! Отлично, мы как раз этим занимаемся. Подскажите, как я могу к вам обращаться? 😊

Клиент: Зачем вам имя? Просто скажите цену.
Бот: Хорошо, без проблем! Тогда уточните, для какого бизнеса нужен бот? 🏪
"""


async def get_available_models() -> list:
    """Запрашивает у Groq список доступных моделей."""
    try:
        response = await client.models.list()
        models = [m.id for m in response.data]
        logger.info(f"Доступные модели: {models}")
        return models
    except Exception as e:
        logger.error(f"Не удалось получить список моделей: {e}")
        return []


def pick_best_model(models: list):
    """Выбирает лучшую модель из доступных."""
    priorities = [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b",
        "llama-3.1-70b-versatile",
        "llama3-70b",
        "llama-3.1-8b-instant",
        "llama3-8b",
        "llama",
        "gemma",
        "mixtral",
    ]
    for pref in priorities:
        for m in models:
            if pref in m.lower():
                return m
    return models[0] if models else None


async def ask_agent(user_id, user_text):
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY / GROQ_API_KEY не задан!")
        return "Ошибка конфигурации: не задан API-ключ."

    # Загружаем историю
    try:
        from services.memory import get_history, add_message
        history = await get_history(user_id)
        await add_message(user_id, "user", user_text)
        history = history + [{"role": "user", "content": user_text}]
    except Exception as e:
        logger.warning(f"Память недоступна: {e}")
        add_message = None
        history = [{"role": "user", "content": user_text}]

    # Получаем список моделей Groq
    models = await get_available_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    best = pick_best_model(models)
    logger.info(f"Выбрана модель: {best}")

    # Пробуем сначала лучшую, потом остальные
    models_to_try = [best] + [m for m in models if m != best]
    # Ограничиваем попытки — не больше 5 моделей
    models_to_try = models_to_try[:5]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=400,
            )
            text = response.choices[0].message.content
            logger.info(f"✅ Ответила модель: {model}")

            # Сохраняем в память
            if add_message:
                try:
                    await add_message(user_id, "assistant", text)
                except Exception:
                    pass

            return text
        except Exception as e:
            logger.warning(f"Модель {model} не сработала: {e}")

    return "Извините, сейчас не могу ответить, попробуйте позже 🙏"
