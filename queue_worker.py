import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Queue

from downloader import download_video
from telegram_handler import send_message, send_video
from utils import normalize_url


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadJob:
    """A queued Telegram video download request."""

    chat_id: int | str
    url: str


download_queue: Queue[DownloadJob] = Queue()
processed_urls: set[str] = set()
state_lock = threading.Lock()
worker_thread: threading.Thread | None = None
worker_busy = False


def start_worker() -> None:
    """Start the single background worker thread once."""
    global worker_thread

    with state_lock:
        if worker_thread and worker_thread.is_alive():
            return

        worker_thread = threading.Thread(
            target=_worker_loop,
            name="telegram-video-downloader-worker",
            daemon=True,
        )
        worker_thread.start()


def add_download_job(chat_id: int | str, url: str) -> bool:
    """Add a URL to the FIFO queue unless it was already seen."""
    normalized_url = normalize_url(url)

    with state_lock:
        if normalized_url in processed_urls:
            return False
        processed_urls.add(normalized_url)

    download_queue.put(DownloadJob(chat_id=chat_id, url=normalized_url))
    return True


def get_queue_status() -> dict:
    """Return queue size and whether the worker is currently processing."""
    with state_lock:
        busy = worker_busy

    return {
        "queue_size": download_queue.qsize(),
        "worker_status": "busy" if busy else "idle",
        "worker_busy": busy,
    }


def _set_worker_busy(value: bool) -> None:
    """Update worker busy state in a thread-safe way."""
    global worker_busy
    with state_lock:
        worker_busy = value


def _worker_loop() -> None:
    """Continuously process queued jobs in strict FIFO order."""
    while True:
        job = download_queue.get()
        _set_worker_busy(True)
        file_path: Path | None = None

        try:
            send_message(job.chat_id, "Download started")
            file_path = download_video(job.url)
            send_video(job.chat_id, file_path)
            send_message(job.chat_id, "Download completed")
        except Exception as exc:
            logger.exception("Failed to process download job for %s", job.url)
            try:
                send_message(job.chat_id, f"Download failed: {exc}")
            except Exception:
                logger.exception("Failed to notify user about download failure")
        finally:
            if file_path:
                _delete_file(file_path)
            _set_worker_busy(False)
            download_queue.task_done()


def _delete_file(file_path: Path) -> None:
    """Delete a downloaded video file after it has been sent or failed."""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        logger.exception("Failed to delete downloaded file: %s", file_path)

