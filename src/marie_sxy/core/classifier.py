"""Filename-driven classification via LiteLLM (Week 2) with offline fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from marie_sxy.core.cache import ClassificationCache, cache_key_for_file
from marie_sxy.llm_config import DEFAULT_MODEL
from marie_sxy.types import FileClassification, FileInfo

logger = logging.getLogger(__name__)

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    m = _JSON_FENCE.search(text)
    if m:
        return m.group(1).strip()
    return text


def _classify_offline(name: str, suffix: str) -> FileClassification:
    """Rule-based guess when LLM is unavailable (tests / no API key)."""
    lower = name.lower()
    ext = suffix.lower()

    if "invoice" in lower or "发票" in name:
        return FileClassification(
            category="文档/发票",
            confidence=0.55,
            reason="offline: invoice-like filename",
            suggested_name=None,
        )
    if "resume" in lower or "cv_" in lower or "简历" in name:
        return FileClassification(
            category="文档/简历",
            confidence=0.55,
            reason="offline: resume-like filename",
            suggested_name=None,
        )
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
        return FileClassification(
            category="图片/其他",
            confidence=0.45,
            reason="offline: image extension",
            suggested_name=None,
        )
    if ext in {".py", ".rs", ".go", ".ts", ".js"}:
        return FileClassification(
            category=f"代码/{ext.removeprefix('.')}",
            confidence=0.5,
            reason="offline: code extension",
            suggested_name=None,
        )
    if ext == ".pdf":
        return FileClassification(
            category="文档/PDF",
            confidence=0.45,
            reason="offline: PDF extension",
            suggested_name=None,
        )
    if ext in {".md", ".txt"}:
        return FileClassification(
            category="文档/文本",
            confidence=0.45,
            reason="offline: text extension",
            suggested_name=None,
        )
    return FileClassification(
        category="其他/未分类",
        confidence=0.3,
        reason="offline: no strong signal",
        suggested_name=None,
    )


def _completion_sync(model: str, messages: list[dict[str, str]]) -> Any:
    from litellm import completion

    return completion(model=model, messages=messages, temperature=0.2)


def classify_file(
    info: FileInfo,
    *,
    cache: ClassificationCache | None = None,
    completion_fn: Any | None = None,
) -> FileClassification:
    """Classify a single file (filename + suffix only in the Week 2 prompt)."""
    cache = cache or ClassificationCache.default()
    key = cache_key_for_file(info)
    hit = cache.get(key)
    if hit is not None:
        return hit

    if os.environ.get("MARIE_SXY_OFFLINE", "").lower() in {"1", "true", "yes"}:
        result = _classify_offline(info.name, info.suffix)
        cache.set(key, result)
        return result

    model = os.environ.get("MARIE_SXY_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    fn = completion_fn or _completion_sync
    prompt = (
        "你是文件整理助手. 仅根据文件名和扩展名, 给出最合适的分类路径"
        '(用 "/" 分隔层级, 如 文档/发票, 图片/截图, 代码/Python).\n'
        "返回严格 JSON, 不要 Markdown, 不要解释:\n"
        '{"category": "<路径>", "confidence": <0到1的小数>, '
        '"reason": "<一句理由>", "suggested_name": null }\n\n'
        f"文件名: {info.name}\n"
        f"扩展名: {info.suffix or '(无)'}\n"
    )

    try:
        resp = fn(model, [{"role": "user", "content": prompt}])
        text = resp.choices[0].message.content or ""
        payload = json.loads(_strip_json_fence(text))
        result = FileClassification.model_validate(payload)
    except Exception as exc:
        logger.info("LLM classification failed (%s), using offline rules", exc)
        result = _classify_offline(info.name, info.suffix)

    cache.set(key, result)
    return result
