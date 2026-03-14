"""Helpers for extracting text from uploaded resume files."""
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text_from_upload(file_storage) -> str:
    """Extract text from txt, pdf, and docx uploads."""
    filename = (file_storage.filename or "resume.txt").lower()
    suffix = Path(filename).suffix
    file_storage.stream.seek(0)
    raw = file_storage.read()
    file_storage.stream.seek(0)

    if suffix in {".txt", ".md", ".rtf"}:
        return raw.decode("utf-8", errors="replace").strip()

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if suffix == ".docx":
        document = Document(BytesIO(raw))
        return "\n".join(p.text for p in document.paragraphs).strip()

    return raw.decode("utf-8", errors="replace").strip()