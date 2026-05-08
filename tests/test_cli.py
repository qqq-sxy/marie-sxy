"""CLI smoke tests using Typer's built-in test runner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from marie import __version__
from marie.cli import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "marie" in result.stdout.lower()


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
