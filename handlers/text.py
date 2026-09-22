from aiogram import Router, F
from aiogram.types import Message

from services.agent import ask_agent
from services.admin import notify_admin

router = Router()


@router.message(F.text)
async def handle_text(message: Message):
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await ask_agent(message.from_user.id, message.text)

    await notify_admin(
        message.bot,
        message.from_user,
        message.text,
        answer,
        is_voice=False,
    )
    await message.answer(answer)
