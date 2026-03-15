"""Utilities for fetching and normalizing job description content."""
from urllib.parse import urlparse
import re

import requests

# Known domain -> company name for common job boards and companies
DOMAIN_TO_COMPANY = {
    "intuit.com": "Intuit",
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "amazon.com": "Amazon",
    "meta.com": "Meta",
    "facebook.com": "Meta",
    "apple.com": "Apple",
    "netflix.com": "Netflix",
    "linkedin.com": None,  # Extract from path if possible
    "greenhouse.io": None,
    "lever.co": None,
    "workday.com": None,
    "jobs.lever.co": None,
    "boards.greenhouse.io": None,
}


def extract_company_name_from_url(jd_url: str) -> str:
    """Derive a readable company name from a job description URL."""
    if not (jd_url or isinstance(jd_url, str)):
        return "Company"
    jd_url = jd_url.strip()
    try:
        parsed = urlparse(jd_url)
        host = (parsed.netloc or "").lower().replace("www.", "")
        if not host:
            return "Company"
        # jobs.company.com or careers.company.com -> company
        for prefix in ("jobs.", "careers.", "recruiting.", "jobs2."):
            if host.startswith(prefix):
                host = host[len(prefix) :]
                break
        # known mapping
        for domain, name in DOMAIN_TO_COMPANY.items():
            if name and (host == domain or host.endswith("." + domain)):
                return name
        # linkedin.com/company/foo -> Foo
        if "linkedin.com" in host and parsed.path:
            m = re.search(r"/company/([^/?]+)", parsed.path, re.I)
            if m:
                return m.group(1).replace("-", " ").title()
        # Take first part of host (e.g. intuit from intuit.com) and title-case
        main = host.split(".")[0] if "." in host else host
        if main in ("com", "io", "co", "org"):
            return "Company"
        return main.replace("-", " ").title()
    except Exception:
        return "Company"


def extract_company_name_from_jd_text(jd_text: str, max_chars: int = 1500) -> str:
    """Try to infer company name from the first part of JD text (e.g. 'At X we...', 'X is hiring')."""
    if not (jd_text or isinstance(jd_text, str)):
        return "Company"
    text = (jd_text or "")[:max_chars].strip()
    # "At Intuit we..." or "At Google, we..."
    m = re.search(r"\bAt\s+([A-Z][A-Za-z0-9\s&.-]+?)(?:\s+we|\s*,|\s+our|\s*\.)", text)
    if m:
        return m.group(1).strip()
    # "Company: X" or "Company Name: X"
    m = re.search(r"(?:Company|Organization)(?:\s+Name)?\s*[:\-]\s*([A-Za-z0-9\s&.-]+)", text, re.I)
    if m:
        return m.group(1).strip()
    # "X is hiring" at start
    m = re.search(r"^([A-Z][A-Za-z0-9\s&.-]+?)\s+is\s+(?:hiring|looking)", text, re.M | re.I)
    if m:
        return m.group(1).strip()
    return "Company"


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