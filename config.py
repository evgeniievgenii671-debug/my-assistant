import os
from pathlib import Path
from dotenv import load_dotenv

PORT = int(os.environ.get("PORT", 8080))
load_dotenv()

# === КЛЮЧИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# === OMDAA (WhatsApp) ===
OMDAA_API_KEY = os.environ.get("OMDAA_API_KEY", "")
OMDAA_SESSION_ID = os.environ.get("OMDAA_SESSION_ID", "")

# === Модели Groq ===
MODEL_MAIN = "openai/gpt-oss-120b"
MODEL_BACKUP = "openai/gpt-oss-20b"
MODEL_WHISPER = "whisper-large-v3"

# === Пути ===
DB_PATH = Path("bot.db")
TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)
