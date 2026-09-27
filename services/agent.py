import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

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


def get_available_models():
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=10
        )
        return [m["id"] for m in r.json().get("data", [])]
    except Exception as e:
        logging.error(f"Ошибка списка моделей: {e}")
        return []


def pick_best_model(models):
    priorities = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b", "mixtral-8x7b"]
    for pref in priorities:
        for m in models:
            if pref in m:
                return m
    return models[0] if models else None


def ask_groq(history):
    if not GROQ_API_KEY:
        return "Ошибка конфигурации."

    models = get_available_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    best = pick_best_model(models)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in [best] + [m for m in models if m != best][:4]:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
            "temperature": 0.3
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            data = r.json()
            if "choices" in data:
                logging.info(f"✅ Ответила модель: {model}")
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Ошибка {model}: {e}")

    return "Извините, сейчас не могу ответить 🙏"
