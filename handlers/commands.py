from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.memory import reset_history

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я личный AI-ассистент Евгения. 🤖\n\n"
        "Могу ответить на вопросы, помочь с информацией, "
        "передать срочное сообщение.\n\n"
        "Чем могу помочь?"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я отвечаю на сообщения в WhatsApp и Telegram. "
        "Если я не смогу ответить — передам сообщение Евгению."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    await reset_history(message.from_user.id)
    await message.answer("История диалога очищена.")
