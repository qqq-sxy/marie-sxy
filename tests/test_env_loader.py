"""Tests for dotenv loading."""

from __future__ import annotations

import os

import pytest

from marie_sxy.env_loader import load_dotenv_files


def test_explicit_env_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    secret = tmp_path / "my.env"
    secret.write_text("OPENAI_API_KEY=secret-from-file\n", encoding="utf-8")
    monkeypatch.setenv("MARIE_SXY_ENV_FILE", str(secret))

    load_dotenv_files()

    assert os.environ.get("OPENAI_API_KEY") == "secret-from-file"


def test_shell_env_wins_over_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "from-shell")
    secret = tmp_path / "my.env"
    secret.write_text("OPENAI_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("MARIE_SXY_ENV_FILE", str(secret))

    load_dotenv_files()

    assert os.environ.get("OPENAI_API_KEY") == "from-shell"
