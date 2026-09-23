import aiosqlite

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from services.memory import reset_history, update_profile
from config import DB_PATH, ADMIN_ID, START_SOURCES

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    # Обрабатываем UTM-метку (например, t.me/bot?start=tiktok)
    if command.args:
        source_key = command.args.lower().strip()
        source_label = START_SOURCES.get(source_key)
        if source_label:
            await update_profile(message.from_user.id, source=source_label)

    await message.answer(
        "👋 Здравствуйте! Я Ассистент Евгения Алексеевича.\n\n"
        "Разрабатываем Telegram и WhatsApp-ботов, сайты, "
        "AI-ассистентов для бизнеса.\n\n"
        "Кстати, как мне к вам обращаться?"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я Ассистент Евгения Алексеевича. Помогаю с разработкой "
        "ботов, сайтов, автоматизацией и AI-решениями.\n\n"
        "Просто напишите мне — и я подскажу, чем можем помочь."
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
