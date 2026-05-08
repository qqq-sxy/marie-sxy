"""Describe image files using a multimodal LLM (Week 3).

Only called when the caller explicitly passes a completion function or the
MARIE_SXY_OFFLINE env-var is NOT set and an API key is available.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})

# Prompt asking the model to distinguish screenshot / meme / photo etc.
_SYSTEM_PROMPT = (
    "你是一个图片分类助手。请用一句话（不超过30字）描述这张图片最可能是什么类型，"
    "例如：手机截图、表情包/梗图、人物照片、风景照片、产品图、图表/信息图、二维码、其他。"
    "只需回答类型描述，不要解释。"
)


def _encode_image(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for the image."""
    suffix = path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return data, media_type


def extract_image_hint(
    path: Path,
    *,
    completion_fn: Any | None = None,
    model: str | None = None,
) -> str:
    """Return a short natural-language description of the image type.

    Returns an empty string if offline mode is set, the image is too large,
    or an error occurs.
    """
    if path.suffix.lower() not in _IMAGE_SUFFIXES:
        return ""

    if os.environ.get("MARIE_SXY_OFFLINE", "").lower() in {"1", "true", "yes"}:
        return ""

    # Skip very large images to avoid huge API payloads (> 5 MB)
    try:
        size = path.stat().st_size
    except OSError:
        return ""
    if size > 5 * 1024 * 1024:
        logger.debug("Skipping large image %s (%d bytes)", path, size)
        return ""

    resolved_model = model or os.environ.get("MARIE_SXY_MODEL", "gpt-4o-mini")

    try:
        data, media_type = _encode_image(path)
    except OSError as exc:
        logger.debug("Cannot read image %s: %s", path, exc)
        return ""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _SYSTEM_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{data}"},
                },
            ],
        }
    ]

    fn = completion_fn or _default_completion
    try:
        resp = fn(resolved_model, messages)
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.debug("Image description failed for %s: %s", path, exc)
        return ""


def _default_completion(model: str, messages: list) -> Any:
    from litellm import completion

    return completion(model=model, messages=messages, temperature=0.2, max_tokens=60)
