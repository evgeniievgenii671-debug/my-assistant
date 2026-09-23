from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from services.agent import ask_agent
from services.admin import notify_admin
from services.profile import extract_and_save
from services.memory import get_history
from services.tts import text_to_speech

router = Router()


@router.message(F.text)
async def handle_text(message: Message):
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Проверяем — это первое сообщение?
    history = await get_history(message.from_user.id)
    is_first = len(history) == 0

    # Извлекаем данные в профиль
    await extract_and_save(message.from_user.id, message.text)

    # Генерируем ответ
    answer = await ask_agent(message.from_user.id, message.text)

    # Уведомление вам
    await notify_admin(
        message.bot,
        message.from_user,
        message.text,
        answer,
        is_voice=False,
    )

    # Если первое сообщение — отвечаем голосом + текст
    if is_first:
        await message.bot.send_chat_action(message.chat.id, "record_voice")
        tts_path = await text_to_speech(answer)
        if tts_path:
            voice = FSInputFile(tts_path)
            await message.answer_voice(voice)
            await message.answer(answer)
            from pathlib import Path
            Path(tts_path).unlink(missing_ok=True)
            return

    # Обычный ответ текстом
    await message.answer(answer)
