import logging
import uuid
from pathlib import Path

import edge_tts

from config import TMP_DIR

logger = logging.getLogger(__name__)

# Голос: молодой, нежный, женский
VOICE = "ru-RU-DariyaNeural"


async def text_to_speech(text: str) -> str | None:
    """Превращает текст в голосовое сообщение. Возвращает путь к файлу."""
    try:
        output_path = TMP_DIR / f"tts_{uuid.uuid4().hex}.ogg"
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(str(output_path))
        return str(output_path)
    except Exception:
        logger.exception("Ошибка TTS")
        return None
