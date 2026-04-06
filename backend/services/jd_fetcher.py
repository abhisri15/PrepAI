"""
Job description fetching and company name extraction.
Handles URL fetching, HTML stripping, and heuristic company name inference.
"""
import re
from urllib.parse import urlparse

import requests

# Known domain → canonical company name for common job boards and tech companies
_DOMAIN_TO_COMPANY: dict[str, str | None] = {
    "intuit.com": "Intuit",
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "amazon.com": "Amazon",
    "meta.com": "Meta",
    "facebook.com": "Meta",
    "apple.com": "Apple",
    "netflix.com": "Netflix",
    # Boards that don't own the company — must extract from path/text
    "linkedin.com": None,
    "greenhouse.io": None,
    "lever.co": None,
    "workday.com": None,
    "jobs.lever.co": None,
    "boards.greenhouse.io": None,
}


def extract_company_name_from_url(jd_url: str) -> str:
    """
    Derive a readable company name from a job description URL.

    Returns "Company" as a safe fallback if nothing useful can be extracted.
    """
    if not jd_url or not isinstance(jd_url, str):
        return "Company"
    try:
        parsed = urlparse(jd_url.strip())
        host = (parsed.netloc or "").lower().replace("www.", "")
        if not host:
            return "Company"

        # Strip common job-board subdomains
        for prefix in ("jobs.", "careers.", "recruiting.", "jobs2."):
            if host.startswith(prefix):
                host = host[len(prefix):]
                break

        # Direct mapping
        for domain, name in _DOMAIN_TO_COMPANY.items():
            if name and (host == domain or host.endswith("." + domain)):
                return name

        # LinkedIn company pages: linkedin.com/company/foo → "Foo"
        if "linkedin.com" in host and parsed.path:
            match = re.search(r"/company/([^/?]+)", parsed.path, re.IGNORECASE)
            if match:
                return match.group(1).replace("-", " ").title()

        # Generic: take the first part of the hostname
        main = host.split(".")[0] if "." in host else host
        if main in ("com", "io", "co", "org"):
            return "Company"
        return main.replace("-", " ").title()

    except Exception:  # noqa: BLE001
        return "Company"


def extract_company_name_from_jd_text(jd_text: str, max_chars: int = 1500) -> str:
    """
    Infer company name from the opening section of JD text using common patterns.

    Tries, in order:
    1. "At Intuit we…" or "At Google, we…"
    2. "Company: Foo" / "Company Name: Foo"
    3. "Foo is hiring…" at line start

    Returns "Company" if nothing matches.
    """
    if not jd_text or not isinstance(jd_text, str):
        return "Company"
    text = jd_text[:max_chars].strip()

    match = re.search(r"\bAt\s+([A-Z][A-Za-z0-9\s&.\-]+?)(?:\s+we|\s*,|\s+our|\s*\.)", text)
    if match:
        return match.group(1).strip()

    match = re.search(r"(?:Company|Organization)(?:\s+Name)?\s*[:\-]\s*([A-Za-z0-9\s&.\-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"^([A-Z][A-Za-z0-9\s&.\-]+?)\s+is\s+(?:hiring|looking)", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return "Company"


def _strip_html(html: str) -> str:
    """Minimal HTML-to-text conversion without external dependencies."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def fetch_job_description(url: str, max_chars: int = 15_000) -> str:
    """
    Fetch a job description page and return its plain-text content.

    Raises:
        ValueError: If *url* is malformed.
        requests.RequestException: On network or HTTP errors.
    """
    if not _is_valid_url(url):
        raise ValueError(f"Invalid URL: {url!r}")
    response = requests.get(url, timeout=15, headers={"User-Agent": "PrepAI/1.0"})
    response.raise_for_status()
    return _strip_html(response.text)[:max_chars]
