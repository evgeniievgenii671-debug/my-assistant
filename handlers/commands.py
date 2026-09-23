import aiosqlite

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.memory import reset_history
from config import DB_PATH, ADMIN_ID

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Здравствуйте! Я Ассистент Евгения Алексеевича.\n\n"
        "Помогаю бизнесу с автоматизацией, разработкой ботов "
        "и сайтов. Могу показать пример работы прямо здесь.\n\n"
        "Скажите — какой у вас бизнес? Или что хотите автоматизировать?"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я Ассистент Евгения Алексеевича. Помогаю с разработкой "
        "ботов, сайтов, автоматизацией и AI-решениями для бизнеса.\n\n"
        "Просто напишите мне — и я подскажу, чем мы можем помочь."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    await reset_history(message.from_user.id)
    await message.answer("История диалога очищена.")


@router.message(Command("reset_all"))
async def cmd_reset_all(message: Message):
    """Только для админа — очищает все профили и историю."""
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM history")
        await db.execute("DELETE FROM profiles")
        await db.commit()
    await message.answer("Все профили и история очищены. ✅")
