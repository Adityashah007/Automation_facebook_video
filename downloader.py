from pathlib import Path
from shutil import which
from uuid import uuid4

import yt_dlp

from config import DOWNLOAD_FOLDER


def download_video(url: str) -> Path:
    """Download a single video with yt-dlp and return the local file path."""
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    video_id = uuid4().hex
    output_template = str(DOWNLOAD_FOLDER / f"{video_id}.%(ext)s")
    has_ffmpeg = _has_ffmpeg()

    options = {
        "outtmpl": output_template,
        "format": _format_selector(has_ffmpeg),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if has_ffmpeg:
        options["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = Path(ydl.prepare_filename(info))
    except Exception:
        _delete_matching_files(video_id)
        raise

    if not file_path.exists() and file_path.suffix != ".mp4":
        merged_path = file_path.with_suffix(".mp4")
        if merged_path.exists():
            file_path = merged_path

    if not file_path.exists():
        candidates = sorted(DOWNLOAD_FOLDER.glob(f"{video_id}.*"))
        if candidates:
            file_path = _prefer_mp4(candidates)

    if not file_path.exists():
        raise FileNotFoundError("Download finished but output file was not found")

    if file_path.suffix.lower() != ".mp4":
        _delete_matching_files(video_id)
        raise RuntimeError(
            "Downloaded file is not MP4. Install FFmpeg and restart the app so yt-dlp can merge or convert to MP4."
        )

    return file_path


def _has_ffmpeg() -> bool:
    """Return True when FFmpeg is available on the system PATH."""
    return bool(which("ffmpeg"))


def _format_selector(has_ffmpeg: bool) -> str:
    """Choose an MP4-friendly yt-dlp format selector."""
    if has_ffmpeg:
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"

    return "best[ext=mp4][vcodec!=none][acodec!=none]/best[ext=mp4]"


def _prefer_mp4(candidates: list[Path]) -> Path:
    """Prefer an MP4 output file when several matching files exist."""
    for candidate in candidates:
        if candidate.suffix.lower() == ".mp4":
            return candidate
    return candidates[0]


def _delete_matching_files(video_id: str) -> None:
    """Remove any partial files created by a failed yt-dlp run."""
    for candidate in DOWNLOAD_FOLDER.glob(f"{video_id}*"):
        try:
            if candidate.is_file():
                candidate.unlink()
        except OSError:
            pass
