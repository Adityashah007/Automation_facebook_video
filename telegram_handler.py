import time
from pathlib import Path

import requests

from config import BOT_TOKEN, TELEGRAM_API_BASE


DEFAULT_TIMEOUT = 60


def _ensure_bot_token() -> None:
    """Fail fast when Telegram credentials are missing."""
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured")


def _post_with_retries(endpoint: str, *, retries: int = 2, **kwargs) -> dict:
    """POST to Telegram with retry support and return the JSON response."""
    _ensure_bot_token()
    url = f"{TELEGRAM_API_BASE}/{endpoint}"
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = requests.post(url, timeout=DEFAULT_TIMEOUT, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(payload.get("description", "Telegram API error"))
            return payload
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)

    raise RuntimeError(f"Telegram request failed after retries: {last_error}")


def send_message(chat_id: int | str, text: str) -> dict:
    """Send a text message to a Telegram chat."""
    return _post_with_retries(
        "sendMessage",
        data={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
    )


def send_video(chat_id: int | str, file_path: str | Path) -> dict:
    """Send a local video file to a Telegram chat."""
    _ensure_bot_token()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with path.open("rb") as video_file:
                response = requests.post(
                    f"{TELEGRAM_API_BASE}/sendVideo",
                    data={"chat_id": chat_id},
                    files={"video": (path.name, video_file)},
                    timeout=DEFAULT_TIMEOUT,
                )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(payload.get("description", "Telegram API error"))
            return payload
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)

    raise RuntimeError(f"Telegram video upload failed after retries: {last_error}")
