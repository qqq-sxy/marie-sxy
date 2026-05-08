"""Classifier + cache tests (offline mode, no API keys)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from marie_sxy.core.cache import ClassificationCache, cache_key_for_file
from marie_sxy.core.classifier import _classify_offline, classify_file
from marie_sxy.types import FileClassification, FileInfo


def _file_info(path: Path) -> FileInfo:
    st = path.stat()
    return FileInfo(
        path=path.resolve(),
        name=path.name,
        suffix=path.suffix.lower(),
        size=st.st_size,
        modified_at=datetime.fromtimestamp(st.st_mtime),
        is_hidden=path.name.startswith("."),
        depth=0,
    )


def test_offline_invoice_filename(tmp_path: Path) -> None:
    f = tmp_path / "invoice_march_2024.pdf"
    f.write_bytes(b"x")
    clf = _classify_offline(f.name, ".pdf")
    assert "发票" in clf.category


def test_cache_hit_skips_duplicate_logic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARIE_SXY_OFFLINE", "1")
    cache_path = tmp_path / "cache.json"
    cache = ClassificationCache(cache_path)

    f = tmp_path / "a.py"
    f.write_text("print(1)")
    info = _file_info(f)

    c1 = classify_file(info, cache=cache)
    c2 = classify_file(info, cache=cache)
    assert c1 == c2
    assert cache_path.exists()


def test_cache_key_changes_when_size_changes(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("a")
    info1 = _file_info(f)
    k1 = cache_key_for_file(info1)

    f.write_text("bbbb")
    info2 = _file_info(f)
    k2 = cache_key_for_file(info2)

    assert k1 != k2


def test_llm_path_uses_mock_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARIE_SXY_OFFLINE", raising=False)

    class Msg:
        content: str

        def __init__(self, content: str) -> None:
            self.content = content

    class Choice:
        message: Msg

        def __init__(self, content: str) -> None:
            self.message = Msg(content)

    class Resp:
        choices: list[Choice]

        def __init__(self, content: str) -> None:
            self.choices = [Choice(content)]

    def fake_completion(model: str, messages: list[dict[str, str]]) -> Resp:
        _ = model, messages
        payload = (
            '{"category": "测试/演示", "confidence": 0.99, '
            '"reason": "mock", "suggested_name": null}'
        )
        return Resp(payload)

    cache_path = tmp_path / "c.json"
    cache = ClassificationCache(cache_path)

    f = tmp_path / "whatever.bin"
    f.write_bytes(b"\0")
    info = _file_info(f)

    out = classify_file(info, cache=cache, completion_fn=fake_completion)
    assert isinstance(out, FileClassification)
    assert out.category == "测试/演示"
    assert out.confidence == pytest.approx(0.99)
