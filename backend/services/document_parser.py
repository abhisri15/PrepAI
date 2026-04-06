"""
Resume / document text extraction.
Supports PDF, DOCX, and plain-text uploads with size and type validation.
"""
from io import BytesIO
from pathlib import Path

from config import Config


def extract_text_from_upload(file_storage, max_bytes: int = Config.MAX_UPLOAD_BYTES) -> str:
    """
    Extract plain text from an uploaded resume file.

    Args:
        file_storage: A Flask/Werkzeug FileStorage object.
        max_bytes: Maximum allowed file size in bytes (default from Config).

    Returns:
        Extracted plain text string.

    Raises:
        ValueError: If the file type is unsupported or the file exceeds *max_bytes*.
    """
    filename = (file_storage.filename or "resume.txt").lower()
    ext = Path(filename).suffix.lstrip(".").lower()

    if ext not in Config.ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '.{ext}'. Allowed: {allowed}")

    file_storage.stream.seek(0)
    raw = file_storage.read()
    file_storage.stream.seek(0)

    if len(raw) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise ValueError(f"File exceeds the {limit_mb} MB size limit")

    return _parse_bytes(ext, raw)


def _parse_bytes(ext: str, raw: bytes) -> str:
    """Dispatch to the appropriate parser based on file extension."""
    if ext in {"txt", "md", "rtf"}:
        return raw.decode("utf-8", errors="replace").strip()

    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if ext == "docx":
        from docx import Document
        document = Document(BytesIO(raw))
        return "\n".join(p.text for p in document.paragraphs).strip()

    # Fallback for any allowed extension not yet handled explicitly
    return raw.decode("utf-8", errors="replace").strip()
