"""Unified LLM credential mapping."""

from __future__ import annotations

import os

import pytest

from marie_sxy.llm_config import (
    apply_marie_sxy_unified_credentials,
    infer_litellm_provider,
)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gpt-4o-mini", "openai"),
        ("deepseek/deepseek-chat", "deepseek"),
        ("anthropic/claude-3-5-sonnet-20241022", "anthropic"),
        ("claude-3-opus-20240229", "anthropic"),
    ],
)
def test_infer_provider(model: str, expected: str) -> None:
    assert infer_litellm_provider(model) == expected


def test_unified_key_maps_to_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("MARIE_SXY_API_KEY", "unified-secret")
    monkeypatch.setenv("MARIE_SXY_MODEL", "deepseek/deepseek-chat")

    apply_marie_sxy_unified_credentials()

    assert os.environ.get("DEEPSEEK_API_KEY") == "unified-secret"


def test_unified_key_maps_to_openai_for_gpt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MARIE_SXY_API_KEY", "sk-unified")
    monkeypatch.setenv("MARIE_SXY_MODEL", "gpt-4o-mini")

    apply_marie_sxy_unified_credentials()

    assert os.environ.get("OPENAI_API_KEY") == "sk-unified"


def test_no_unified_key_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARIE_SXY_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "keep-me")

    apply_marie_sxy_unified_credentials()

    assert os.environ.get("OPENAI_API_KEY") == "keep-me"
