import logging

from services.groq_client import groq
from services.memory import get_history, add_message
from config import MODEL_MAIN, MODEL_BACKUP

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — личный AI-ассистент Евгения. Отвечаешь в его WhatsApp и Telegram.

ТВОЯ РОЛЬ:
- Отвечать на входящие сообщения вежливо и по делу.
- Если спрашивают про Евгения лично — говори, что он занят и ответит позже, спроси что передать.
- Если вопрос рабочий (по магазину, товарам, услугам) — помоги, чем можешь.
- Если не знаешь ответа — скажи: "Уточню у Евгения и вернусь с ответом".

КАК ОБЩАТЬСЯ:
- Дружелюбно, но не панибратски.
- Коротко — 1-3 предложения.
- На русском языке (или на языке собеседника, если он пишет не по-русски).
- Не выдумывай факты. Если не знаешь — скажи честно.

ЧЕГО НЕ ДЕЛАТЬ:
- Не называй конкретных цен без подтверждения.
- Не обещай того, что не можешь выполнить.
- Не рассказывай лишнего о Евгении.
"""


async def ask_agent(user_id: int, text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += await get_history(user_id)
    messages.append({"role": "user", "content": text})

    answer = None
    for model in (MODEL_MAIN, MODEL_BACKUP):
        try:
            response = await groq.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=400,
            )
            answer = response.choices[0].message.content.strip()
            break
        except Exception:
            logger.exception("Groq error on model %s", model)
            continue

    if not answer:
        answer = "Секунду, уточню и вернусь с ответом."

    await add_message(user_id, "user", text)
    await add_message(user_id, "assistant", answer)
    return answer
