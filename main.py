import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request

from config import BOT_TOKEN, DOWNLOAD_FOLDER
from queue_worker import add_download_job, get_queue_status, start_worker
from telegram_handler import send_message
from utils import extract_urls, is_valid_url


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare local folders and start the single FIFO worker."""
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    start_worker()
    yield


app = FastAPI(title="Telegram Video Downloader Agent", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, Any]:
    """Return server health and queue size."""
    status = get_queue_status()
    return {"status": "running", "queue_size": status["queue_size"]}


@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """Receive Telegram webhook updates, validate URLs, and enqueue jobs."""
    update = await request.json()
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text") or message.get("caption") or ""

    if not chat_id:
        return {"status": "ignored"}

    if text.strip() == "/status":
        queue_status = get_queue_status()
        send_message(
            chat_id,
            (
                f"Queue size: {queue_status['queue_size']}\n"
                f"Worker: {queue_status['worker_status']}"
            ),
        )
        return {"status": "ok"}

    urls = extract_urls(text)
    if not urls:
        send_message(chat_id, "Invalid URL. Please send a valid video link.")
        return {"status": "ok"}

    accepted = 0
    for url in urls:
        if not is_valid_url(url):
            send_message(chat_id, f"Invalid URL: {url}")
            continue

        if add_download_job(chat_id, url):
            accepted += 1
            send_message(chat_id, "Added to queue")
        else:
            send_message(chat_id, "Already processed")

    logger.info("Accepted %s URL(s) from chat %s", accepted, chat_id)
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Return a small service descriptor."""
    return {
        "name": "Telegram Video Downloader Agent",
        "webhook": "/webhook",
        "health": "/health",
        "bot_configured": str(bool(BOT_TOKEN)).lower(),
    }

