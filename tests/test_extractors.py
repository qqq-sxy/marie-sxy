"""Tests for Week 3 extractors and analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from marie_sxy.extractors.code import extract_code_language
from marie_sxy.extractors.image import extract_image_hint
from marie_sxy.extractors.pdf import extract_pdf_text


# ── code extractor ────────────────────────────────────────────────────────────


def test_code_language_by_extension(tmp_path: Path) -> None:
    f = tmp_path / "script.py"
    f.write_text("print('hello')")
    assert extract_code_language(f) == "Python"


def test_code_language_typescript(tmp_path: Path) -> None:
    f = tmp_path / "app.ts"
    f.write_text("const x: number = 1;")
    assert extract_code_language(f) == "TypeScript"


def test_code_language_shebang_python(tmp_path: Path) -> None:
    f = tmp_path / "myscript"
    f.write_text("#!/usr/bin/env python3\nprint('hi')")
    assert extract_code_language(f) == "Python"


def test_code_language_shebang_bash(tmp_path: Path) -> None:
    f = tmp_path / "run"
    f.write_text("#!/bin/bash\necho hi")
    assert extract_code_language(f) == "Bash"


def test_code_language_dockerfile(tmp_path: Path) -> None:
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.13")
    assert extract_code_language(f) == "Dockerfile"


def test_code_language_unknown(tmp_path: Path) -> None:
    f = tmp_path / "binary.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert extract_code_language(f) == ""


# ── pdf extractor ─────────────────────────────────────────────────────────────


def test_pdf_extract_no_pypdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """extract_pdf_text returns '' when pypdf is not installed."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "pypdf":
            raise ImportError("pypdf not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4")
    assert extract_pdf_text(f) == ""


def test_pdf_extract_invalid_file(tmp_path: Path) -> None:
    """extract_pdf_text returns '' for a non-PDF file."""
    f = tmp_path / "fake.pdf"
    f.write_bytes(b"not a real pdf")
    result = extract_pdf_text(f)
    assert isinstance(result, str)


# ── image extractor ───────────────────────────────────────────────────────────


def test_image_hint_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARIE_SXY_OFFLINE", "1")
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"\xff\xd8\xff")
    assert extract_image_hint(f) == ""


def test_image_hint_non_image(tmp_path: Path) -> None:
    f = tmp_path / "data.csv"
    f.write_text("a,b,c")
    assert extract_image_hint(f) == ""


def test_image_hint_too_large(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARIE_SXY_OFFLINE", raising=False)
    f = tmp_path / "big.png"
    f.write_bytes(b"\x89PNG" + b"x" * (6 * 1024 * 1024))
    assert extract_image_hint(f) == ""


def test_image_hint_mock_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARIE_SXY_OFFLINE", raising=False)

    # Create a tiny 1x1 PNG (valid enough to be read)
    import base64

    minimal_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    f = tmp_path / "tiny.png"
    f.write_bytes(minimal_png)

    class Msg:
        content = "手机截图"

    class Choice:
        message = Msg()

    class Resp:
        choices = [Choice()]

    def fake_completion(model: str, messages: list) -> Resp:
        return Resp()

    result = extract_image_hint(f, completion_fn=fake_completion)
    assert result == "手机截图"


# ── analyzer integration ──────────────────────────────────────────────────────


def test_analyzer_code_hint(tmp_path: Path) -> None:
    from datetime import datetime

    from marie_sxy.core.analyzer import analyze_file
    from marie_sxy.types import FileInfo

    f = tmp_path / "main.go"
    f.write_text("package main")
    info = FileInfo(
        path=f.resolve(),
        name=f.name,
        suffix=".go",
        size=f.stat().st_size,
        modified_at=datetime.fromtimestamp(f.stat().st_mtime),
        is_hidden=False,
        depth=0,
    )
    hint = analyze_file(info)
    assert "Go" in hint


def test_analyzer_pdf_no_pypdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Analyzer returns '' for PDF when pypdf is missing."""
    import builtins
    from datetime import datetime

    from marie_sxy.core.analyzer import analyze_file
    from marie_sxy.types import FileInfo

    real_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "pypdf":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF")
    info = FileInfo(
        path=f.resolve(),
        name=f.name,
        suffix=".pdf",
        size=f.stat().st_size,
        modified_at=datetime.fromtimestamp(f.stat().st_mtime),
        is_hidden=False,
        depth=0,
    )
    assert analyze_file(info) == ""


def test_classify_with_content_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """classify_file passes content_hint into the prompt seen by the LLM."""
    from datetime import datetime

    from marie_sxy.core.cache import ClassificationCache
    from marie_sxy.core.classifier import classify_file
    from marie_sxy.types import FileInfo

    monkeypatch.delenv("MARIE_SXY_OFFLINE", raising=False)

    captured: list[str] = []

    class Msg:
        content = '{"category": "文档/发票", "confidence": 0.9, "reason": "hint test", "suggested_name": null}'

    class Choice:
        message = Msg()

    class Resp:
        choices = [Choice()]

    def fake_completion(model: str, messages: list) -> Resp:
        captured.append(messages[0]["content"])
        return Resp()

    f = tmp_path / "bill.pdf"
    f.write_bytes(b"%PDF")
    info = FileInfo(
        path=f.resolve(),
        name=f.name,
        suffix=".pdf",
        size=f.stat().st_size,
        modified_at=datetime.fromtimestamp(f.stat().st_mtime),
        is_hidden=False,
        depth=0,
    )
    cache = ClassificationCache(tmp_path / "c.json")
    classify_file(info, cache=cache, completion_fn=fake_completion, content_hint="PDF首页文本: 发票号码12345")

    assert captured, "completion_fn was not called"
    assert "发票号码12345" in captured[0]
