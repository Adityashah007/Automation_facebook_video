import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BASE_URL = os.getenv("BASE_URL", "").strip().rstrip("/")
DOWNLOAD_FOLDER = Path(os.getenv("DOWNLOAD_FOLDER", "downloads")).resolve()

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""

