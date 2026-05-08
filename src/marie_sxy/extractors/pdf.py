"""Extract text from the first page of a PDF file."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum characters to extract (keeps prompt size reasonable)
_MAX_CHARS = 800


def extract_pdf_text(path: Path) -> str:
    """Return up to _MAX_CHARS of text from the first PDF page.

    Returns an empty string if pypdf is not installed or extraction fails.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.debug("pypdf not installed; skipping PDF text extraction")
        return ""

    try:
        reader = PdfReader(str(path), strict=False)
        if not reader.pages:
            return ""
        text = reader.pages[0].extract_text() or ""
        return text[:_MAX_CHARS].strip()
    except Exception as exc:
        logger.debug("PDF extraction failed for %s: %s", path, exc)
        return ""
