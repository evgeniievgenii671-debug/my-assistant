import json
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto

from services.agent import ask_agent
from services.admin import notify_admin
from services.profile import extract_and_save
from services.memory import get_history
from services.tts import text_to_speech

router = Router()

DEMO_PATH = Path(__file__).parent.parent / "data" / "demo.json"

# Загружаем demo.json
_demo = {"photo": [], "video": []}
try:
    if DEMO_PATH.exists():
        _demo = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
except Exception:
    pass


def _is_demo_request(text: str) -> bool:
    """Проверяет, просит ли клиент показать демо."""
    if not text:
        return False
    lower = text.lower()
    triggers = [
        "покажи демо", "покажи пример", "как работает",
        "хочу посмотреть", "есть примеры", "покажи как",
        "покажите", "скинь пример", "продемонстрируй",
    ]
    return any(t in lower for t in triggers)


async def _send_demo(message: Message) -> None:
    """Отправляет фото-альбом и видео."""
    photos = _demo.get("photo", [])
    videos = _demo.get("video", [])

    # Отправляем фото альбомом (макс 10 в альбоме)
    if photos:
        media = [InputMediaPhoto(media=pid) for pid in photos[:10]]
        try:
            await message.answer_media_group(media)
        except Exception:
            # Если альбом не прошёл — по одному
            for pid in photos[:10]:
                try:
                    await message.answer_photo(pid)
                except Exception:
                    pass

    # Отправляем видео
    for vid in videos[:2]:
        try:
            await message.answer_video(vid)
        except Exception:
            pass


@router.message(F.text)
async def handle_text(message: Message):
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Проверка: первое сообщение?
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
            from aiogram.types import FSInputFile
            voice = FSInputFile(tts_path)
            await message.answer_voice(voice)
            await message.answer(answer)
            Path(tts_path).unlink(missing_ok=True)
        else:
            await message.answer(answer)
    else:
        await message.answer(answer)

    # Если клиент просит демо — отправляем материалы
    if _is_demo_request(message.text):
        await _send_demo(message)
