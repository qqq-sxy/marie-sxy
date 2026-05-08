"""Content analyzer: enriches FileInfo with a human-readable content hint."""

from __future__ import annotations

import logging
from typing import Any

from marie_sxy.extractors.code import extract_code_language
from marie_sxy.extractors.image import extract_image_hint
from marie_sxy.extractors.pdf import extract_pdf_text
from marie_sxy.types import FileInfo

logger = logging.getLogger(__name__)

_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})
_CODE_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
        ".rs", ".go", ".java", ".kt", ".kts", ".swift", ".c", ".h",
        ".cpp", ".cc", ".cxx", ".hpp", ".cs", ".rb", ".php", ".r",
        ".lua", ".pl", ".sh", ".bash", ".zsh", ".fish", ".ps1",
        ".scala", ".clj", ".ex", ".exs", ".erl", ".hs", ".ml", ".mli",
        ".dart", ".vue", ".svelte", ".tf", ".sql", ".html", ".htm",
        ".css", ".scss", ".sass", ".less", ".ipynb",
    }
)


def analyze_file(
    info: FileInfo,
    *,
    image_completion_fn: Any | None = None,
    image_model: str | None = None,
) -> str:
    """Return a content hint string for use in the LLM classification prompt.

    For PDFs: first-page text snippet.
    For images: multimodal description.
    For code files: detected language name.
    For everything else: empty string.
    """
    suffix = info.suffix.lower()

    if suffix == ".pdf":
        text = extract_pdf_text(info.path)
        if text:
            return f"PDF首页文本片段: {text}"
        return ""

    if suffix in _IMAGE_SUFFIXES:
        hint = extract_image_hint(
            info.path,
            completion_fn=image_completion_fn,
            model=image_model,
        )
        if hint:
            return f"图片描述: {hint}"
        return ""

    if suffix in _CODE_SUFFIXES or info.path.name in {"Dockerfile", "Containerfile"}:
        lang = extract_code_language(info.path)
        if lang:
            return f"代码语言: {lang}"
        return ""

    return ""
