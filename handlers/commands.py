import json
from pathlib import Path

import aiosqlite

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from services.memory import reset_history, update_profile
from config import DB_PATH, ADMIN_ID, START_SOURCES

router = Router()

DEMO_PATH = Path(__file__).parent.parent / "data" / "demo.json"


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
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
        "ботов, сайтов, автоматизацией и AI-решениями."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    await reset_history(message.from_user.id)
    await message.answer("История диалога очищена.")


@router.message(Command("reset_all"))
async def cmd_reset_all(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM history")
        await db.execute("DELETE FROM profiles")
        await db.commit()
    await message.answer("Все профили и история очищены. ✅")


@router.message(Command("demo_check"))
async def cmd_demo_check(message: Message):
    """Проверка demo.json."""
    if message.from_user.id != ADMIN_ID:
        return

    if not DEMO_PATH.exists():
        await message.answer(
            f"❌ Файл НЕ найден по пути:\n{DEMO_PATH}\n\n"
            f"Проверьте на GitHub: data/demo.json"
        )
        return

    try:
        data = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        photos = data.get("photo", [])
        videos = data.get("video", [])
        await message.answer(
            f"✅ demo.json найден\n\n"
            f"Фото: {len(photos)}\n"
            f"Видео: {len(videos)}\n\n"
            f"Путь: {DEMO_PATH}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения:\n{e}")


@router.message(Command("demo_send"))
async def cmd_demo_send(message: Message):
    """Тестовая отправка демо вам."""
    if message.from_user.id != ADMIN_ID:
        return

    if not DEMO_PATH.exists():
        await message.answer("❌ demo.json не найден")
        return

    try:
        data = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        photos = data.get("photo", [])
        videos = data.get("video", [])

        from aiogram.types import InputMediaPhoto

        if photos:
            media = [InputMediaPhoto(media=pid) for pid in photos[:10]]
            await message.answer_media_group(media)
            await message.answer(f"✅ Отправлено фото: {len(photos[:10])}")

        for vid in videos[:2]:
            await message.answer_video(vid)
            await message.answer("✅ Отправлено видео")
    except Exception as e:
        await message.answer(f"❌ Ошибка:\n{type(e).__name__}: {e}")
