"""Helpers for extracting text from uploaded files."""

from io import BytesIO
from typing import Optional

from docx import Document


def extract_text_from_upload(raw_bytes: bytes, extension: str) -> str:
    """Extract plain text from supported uploads (txt, docx).

    Args:
        raw_bytes: Raw file content.
        extension: Lowercase file extension starting with a dot (e.g., ".txt").

    Raises:
        ValueError: If the file cannot be parsed or extension is unsupported.
    """
    ext = extension.lower()
    if ext == ".txt":
        return raw_bytes.decode("utf-8", errors="ignore")
    if ext == ".docx":
        document = Document(BytesIO(raw_bytes))
        return "\n".join(p.text for p in document.paragraphs)

    raise ValueError(f"Unsupported extension: {extension}")
