import uuid

from aiogram import Router, F
from aiogram.types import Message

from services.agent import ask_agent
from services.whisper import transcribe
from services.admin import notify_admin
from config import TMP_DIR

router = Router()


@router.message(F.voice)
async def handle_voice(message: Message):
    file = await message.bot.get_file(message.voice.file_id)
    path = TMP_DIR / f"{uuid.uuid4().hex}.ogg"

    try:
        await message.bot.download_file(file.file_path, path)
        await message.bot.send_chat_action(message.chat.id, "typing")

        text = (await transcribe(str(path))).strip()
        if not text:
            await message.answer("Не разобрал голосовое, повторите, пожалуйста.")
            return

        answer = await ask_agent(message.from_user.id, text)

        await notify_admin(message.bot, message.from_user, text, is_voice=True)
        await message.answer(answer)
    finally:
        path.unlink(missing_ok=True)
