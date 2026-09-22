from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.memory import reset_history

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Здравствуйте! Я AI-ассистент.\n\n"
        "Помогаю бизнесу с автоматизацией, разработкой ботов "
        "и сайтов. Могу показать пример работы прямо здесь.\n\n"
        "Скажите — какой у вас бизнес? Или что хотите автоматизировать?"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я AI-ассистент. Помогаю с разработкой ботов, сайтов, "
        "автоматизацией и AI-решениями для бизнеса.\n\n"
        "Просто напишите мне — и я подскажу, чем мы можем помочь."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    await reset_history(message.from_user.id)
    await message.answer("История диалога очищена.")
