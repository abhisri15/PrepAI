"""Utilities for fetching and normalizing job description content."""
from urllib.parse import urlparse
import re

import requests


def extract_text_from_html(html: str) -> str:
    """Simple HTML-to-text extraction without BeautifulSoup."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def fetch_job_description(url: str, max_chars: int = 15000) -> str:
    """Fetch and normalize job description text from a URL."""
    if not validate_url(url):
        raise ValueError("Invalid URL")

    response = requests.get(url, timeout=15, headers={"User-Agent": "PrepAI/1.0"})
    response.raise_for_status()
    return extract_text_from_html(response.text)[:max_chars]