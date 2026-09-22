import logging
import re
import uuid
from pathlib import Path

import edge_tts

from config import TMP_DIR

logger = logging.getLogger(__name__)

# Голос: женский, тёплый (единственный доступный русский женский в edge-tts)
VOICE = "ru-RU-SvetlanaNeural"


def _clean_text(text: str) -> str:
    """Убирает эмодзи и лишние символы, чтобы TTS не падал."""
    # Удаляем эмодзи и пиктограммы
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # смайлы
        "\U0001F300-\U0001F5FF"  # символы
        "\U0001F680-\U0001F6FF"  # транспорт
        "\U0001F700-\U0001F77F"  # алхимия
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002600-\U000027BF"  # разные символы
        "\U0001F1E0-\U0001F1FF"  # флаги
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)
    # Убираем лишние пробелы
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def text_to_speech(text: str) -> str | None:
    """Превращает текст в голосовое сообщение. Возвращает путь к файлу."""
    try:
        clean = _clean_text(text)
        if not clean:
            logger.warning("После очистки текста нечего озвучивать")
            return None

        output_path = TMP_DIR / f"tts_{uuid.uuid4().hex}.ogg"
        communicate = edge_tts.Communicate(clean, VOICE)
        await communicate.save(str(output_path))
        return str(output_path)
    except Exception:
        logger.exception("Ошибка TTS")
        return None
