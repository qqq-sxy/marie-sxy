"""Tests for Executor (execute_moves)."""

from __future__ import annotations

from pathlib import Path

from marie_sxy.core.executor import execute_moves
from marie_sxy.types import MoveOp


def test_execute_moves_basic(tmp_path: Path) -> None:
    src = tmp_path / "file.txt"
    src.write_text("hello")
    dst = tmp_path / "subdir" / "file.txt"

    ops = [MoveOp(src=src, dst=dst)]
    result = execute_moves(ops)

    assert result.success_count == 1
    assert result.failure_count == 0
    assert dst.exists()
    assert not src.exists()


def test_execute_moves_creates_parent_dirs(tmp_path: Path) -> None:
    src = tmp_path / "a.pdf"
    src.write_bytes(b"pdf")
    dst = tmp_path / "深" / "层" / "目录" / "a.pdf"

    execute_moves([MoveOp(src=src, dst=dst)])
    assert dst.exists()


def test_execute_moves_dry_run(tmp_path: Path) -> None:
    src = tmp_path / "b.txt"
    src.write_text("hi")
    dst = tmp_path / "other" / "b.txt"

    result = execute_moves([MoveOp(src=src, dst=dst)], dry_run=True)
    assert result.success_count == 1
    assert src.exists()  # not actually moved
    assert not dst.exists()


def test_execute_moves_missing_source(tmp_path: Path) -> None:
    src = tmp_path / "ghost.txt"  # does not exist
    dst = tmp_path / "out" / "ghost.txt"

    result = execute_moves([MoveOp(src=src, dst=dst)])
    assert result.success_count == 0
    assert result.failure_count == 1


def test_execute_moves_multiple(tmp_path: Path) -> None:
    files = []
    ops = []
    for i in range(5):
        src = tmp_path / f"f{i}.txt"
        src.write_text(f"content {i}")
        dst = tmp_path / "out" / f"f{i}.txt"
        files.append((src, dst))
        ops.append(MoveOp(src=src, dst=dst))

    result = execute_moves(ops)
    assert result.success_count == 5
    for src, dst in files:
        assert dst.exists()
        assert not src.exists()
