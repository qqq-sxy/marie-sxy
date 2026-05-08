"""Tests for History and undo."""

from __future__ import annotations

from pathlib import Path

import pytest

from marie_sxy.core.history import History, make_session
from marie_sxy.types import MoveOp


def _make_op(src: Path, dst: Path) -> MoveOp:
    return MoveOp(src=src, dst=dst)


def test_history_empty(tmp_path: Path) -> None:
    h = History(tmp_path / "hist.json")
    assert h.last_session() is None


def test_history_record_and_reload(tmp_path: Path) -> None:
    hist_file = tmp_path / "hist.json"
    src = tmp_path / "a.txt"
    dst = tmp_path / "out" / "a.txt"
    src.write_text("x")

    h = History(hist_file)
    session = make_session(tmp_path, [_make_op(src, dst)])
    h.record(session)

    h2 = History(hist_file)
    last = h2.last_session()
    assert last is not None
    assert last.session_id == session.session_id
    assert len(last.ops) == 1
    assert last.ops[0].src == src
    assert last.ops[0].dst == dst


def test_undo_last_restores_file(tmp_path: Path) -> None:
    hist_file = tmp_path / "hist.json"

    src = tmp_path / "original.txt"
    src.write_text("data")
    dst_dir = tmp_path / "移动后"
    dst_dir.mkdir()
    dst = dst_dir / "original.txt"

    # Simulate a move
    import shutil

    shutil.move(str(src), str(dst))
    assert dst.exists()

    h = History(hist_file)
    session = make_session(tmp_path, [_make_op(src, dst)])
    h.record(session)

    result = h.undo_last()
    assert result is not None
    assert result.success
    assert src.exists()
    assert not dst.exists()

    # Session should be removed after successful undo
    assert h.last_session() is None


def test_undo_last_dry_run(tmp_path: Path) -> None:
    hist_file = tmp_path / "hist.json"

    src = tmp_path / "f.txt"
    dst_dir = tmp_path / "done"
    dst_dir.mkdir()
    dst = dst_dir / "f.txt"
    dst.write_text("hello")  # dst exists

    h = History(hist_file)
    session = make_session(tmp_path, [_make_op(src, dst)])
    h.record(session)

    result = h.undo_last(dry_run=True)
    assert result is not None
    assert len(result.restored) == 1
    # Dry-run should NOT remove from history
    assert h.last_session() is not None
    # dst should still be there
    assert dst.exists()


def test_undo_last_missing_dst_marks_failure(tmp_path: Path) -> None:
    hist_file = tmp_path / "hist.json"

    src = tmp_path / "ghost.txt"
    dst = tmp_path / "out" / "ghost.txt"  # dst doesn't exist

    h = History(hist_file)
    session = make_session(tmp_path, [_make_op(src, dst)])
    h.record(session)

    result = h.undo_last()
    assert result is not None
    assert not result.success
    assert len(result.failed) == 1
    # Session stays in history when undo partially fails
    assert h.last_session() is not None


def test_multiple_sessions_undo_last_only(tmp_path: Path) -> None:
    hist_file = tmp_path / "hist.json"

    files = []
    for i in range(3):
        s = tmp_path / f"s{i}.txt"
        d_dir = tmp_path / f"d{i}"
        d_dir.mkdir()
        d = d_dir / f"s{i}.txt"
        s.write_text(str(i))
        import shutil

        shutil.move(str(s), str(d))
        files.append((s, d))

    h = History(hist_file)
    sessions = []
    for s, d in files:
        sess = make_session(tmp_path, [_make_op(s, d)])
        h.record(sess)
        sessions.append(sess)

    assert len(h.all_sessions()) == 3

    # Undo only the last one
    result = h.undo_last()
    assert result is not None
    assert result.session.session_id == sessions[-1].session_id
    assert len(h.all_sessions()) == 2
