import re
from urllib.parse import urlparse


URL_PATTERN = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    """Extract HTTP and HTTPS URLs from a Telegram message."""
    if not text:
        return []

    urls = URL_PATTERN.findall(text)
    return [url.rstrip(".,;:!?)]}") for url in urls]


def is_valid_url(url: str) -> bool:
    """Return True when the URL has a valid HTTP(S) scheme and host."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_url(url: str) -> str:
    """Normalize URL text enough to detect simple duplicates."""
    return url.strip().rstrip("/")

