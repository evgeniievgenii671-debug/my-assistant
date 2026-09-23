import json
import logging
from pathlib import Path

import aiosqlite

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile

from services.memory import reset_history, update_profile
from config import DB_PATH, ADMIN_ID, START_SOURCES

logger = logging.getLogger(__name__)
router = Router()

DEMO_PATH = Path("demo.json")

# Буфер в памяти
_demo_buffer = {"photo": [], "video": []}


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
        "ботов, сайтов, автоматизацией и AI-решениями.\n\n"
        "Просто напишите мне — и я подскажу, чем можем помочь."
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


# === ЗАГРУЗКА ДЕМО ===

@router.message(Command("demo_start"))
async def cmd_demo_start(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    _demo_buffer["photo"] = []
    _demo_buffer["video"] = []
    await message.answer("Готово! Отправляйте фото и видео по одному. Потом /demo_save")


@router.message(Command("demo_save"))
async def cmd_demo_save(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not _demo_buffer["photo"] and not _demo_buffer["video"]:
        await message.answer("Пусто. Сначала /demo_start и загрузите файлы.")
        return

    with open(DEMO_PATH, "w", encoding="utf-8") as f:
        json.dump(_demo_buffer, f, ensure_ascii=False, indent=2)

    await message.answer(
        f"Сохранено!\n"
        f"Фото: {len(_demo_buffer['photo'])}\n"
        f"Видео: {len(_demo_buffer['video'])}"
    )


@router.message(Command("demo_show"))
async def cmd_demo_show(message: Message):
    """Показывает содержимое demo.json"""
    if message.from_user.id != ADMIN_ID:
        return
    if not DEMO_PATH.exists():
        await message.answer("demo.json не найден. Сначала /demo_save.")
        return

    content = DEMO_PATH.read_text(encoding="utf-8")
    # Отправляем как файл
    file = FSInputFile(str(DEMO_PATH))
    await message.answer_document(file, caption="Вот demo.json")
    # И текстом — чтобы скопировать
    await message.answer(f"<pre>{content}</pre>", parse_mode="HTML")


@router.message(Command("demo_load"))
async def cmd_demo_load(message: Message):
    """Загружает demo.json с диска в буфер (на случай перезапуска)"""
    if message.from_user.id != ADMIN_ID:
        return
    if not DEMO_PATH.exists():
        await message.answer("demo.json не найден.")
        return
    data = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    _demo_buffer["photo"] = data.get("photo", [])
    _demo_buffer["video"] = data.get("video", [])
    await message.answer(
        f"Загружено из файла: Фото {len(_demo_buffer['photo'])}, "
        f"Видео {len(_demo_buffer['video'])}"
    )


@router.message(lambda m: m.photo and m.from_user.id == ADMIN_ID)
async def catch_photo(message: Message):
    file_id = message.photo[-1].file_id
    _demo_buffer["photo"].append(file_id)
    await message.answer(f"✅ Фото сохранено ({len(_demo_buffer['photo'])})")


@router.message(lambda m: (m.video or m.document) and m.from_user.id == ADMIN_ID)
async def catch_video(message: Message):
    if message.video:
        file_id = message.video.file_id
    else:
        file_id = message.document.file_id
    _demo_buffer["video"].append(file_id)
    await message.answer(f"✅ Видео сохранено ({len(_demo_buffer['video'])})")
