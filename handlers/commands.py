import json
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID

router = Router()

DEMO_PATH = Path(__file__).parent.parent / "data" / "demo.json"


@router.message(Command("demo_check"))
async def cmd_demo_check(message: Message):
    """Проверка — есть ли demo.json."""
    if message.from_user.id != ADMIN_ID:
        return

    if not DEMO_PATH.exists():
        await message.answer(
            f"❌ Файл не найден: {DEMO_PATH}\n"
            f"Проверьте, есть ли он на GitHub в папке data/"
        )
        return

    try:
        data = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        photos = len(data.get("photo", []))
        videos = len(data.get("video", []))
        await message.answer(
            f"✅ demo.json найден!\n"
            f"Фото: {photos}\n"
            f"Видео: {videos}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения: {e}")
