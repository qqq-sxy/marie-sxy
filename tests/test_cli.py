"""CLI smoke tests using Typer's built-in test runner."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from marie_sxy import __version__
from marie_sxy.cli import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "marie_sxy" in result.stdout.lower()


def test_scan_on_empty_dir(tmp_path: Path) -> None:
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "No files found" in result.stdout


def test_scan_on_populated_dir(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.md").write_text("# hi")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("print('hi')")

    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "Found 3 files" in result.stdout


def test_scan_missing_dir_exits_with_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    result = runner.invoke(app, ["scan", str(missing)])
    assert result.exit_code != 0


def test_organize_dry_run_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARIE_SXY_OFFLINE", "1")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache_root"))

    (tmp_path / "invoice_april.pdf").write_bytes(b"x")
    (tmp_path / "photo.jpg").write_bytes(b"y")

    result = runner.invoke(app, ["organize", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "Suggested layout" in result.stdout or "Suggested" in result.stdout
    assert "invoice_april.pdf" in result.stdout


def test_organize_apply_not_implemented(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARIE_SXY_OFFLINE", "1")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache_root"))

    result = runner.invoke(app, ["organize", str(tmp_path), "--apply"])
    assert result.exit_code != 0
