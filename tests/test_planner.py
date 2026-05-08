"""Tests for Planner (plan_moves)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from marie_sxy.core.planner import plan_moves
from marie_sxy.types import FileClassification, FileInfo


def _info(path: Path) -> FileInfo:
    st = path.stat()
    return FileInfo(
        path=path.resolve(),
        name=path.name,
        suffix=path.suffix.lower(),
        size=st.st_size,
        modified_at=datetime.fromtimestamp(st.st_mtime),
        is_hidden=False,
        depth=0,
    )


def _clf(category: str) -> FileClassification:
    return FileClassification(category=category, confidence=0.9, reason="test")


# ── basic move ────────────────────────────────────────────────────────────────


def test_plan_moves_basic(tmp_path: Path) -> None:
    f = tmp_path / "invoice.pdf"
    f.write_bytes(b"x")
    pairs = [(_info(f), _clf("文档/发票"))]
    ops = plan_moves(tmp_path, pairs)
    assert len(ops) == 1
    assert ops[0].src == f.resolve()
    assert ops[0].dst == tmp_path / "文档" / "发票" / "invoice.pdf"


def test_plan_moves_already_in_place(tmp_path: Path) -> None:
    target_dir = tmp_path / "文档" / "发票"
    target_dir.mkdir(parents=True)
    f = target_dir / "invoice.pdf"
    f.write_bytes(b"x")
    pairs = [(_info(f), _clf("文档/发票"))]
    ops = plan_moves(tmp_path, pairs)
    assert ops == []  # already in the right place


def test_plan_moves_suggested_name(tmp_path: Path) -> None:
    f = tmp_path / "weird_name.pdf"
    f.write_bytes(b"x")
    clf = FileClassification(
        category="文档/发票",
        confidence=0.9,
        reason="test",
        suggested_name="invoice_2025.pdf",
    )
    ops = plan_moves(tmp_path, [(_info(f), clf)])
    assert ops[0].dst.name == "invoice_2025.pdf"


# ── conflict resolution ───────────────────────────────────────────────────────


def test_plan_moves_conflict_between_files(tmp_path: Path) -> None:
    """Two files with the same name going to the same category get disambiguated."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    f1 = dir_a / "report.pdf"
    f2 = dir_b / "report.pdf"
    f1.write_bytes(b"1")
    f2.write_bytes(b"2")
    pairs = [(_info(f1), _clf("文档")), (_info(f2), _clf("文档"))]
    ops = plan_moves(tmp_path, pairs)
    assert len(ops) == 2
    dsts = {op.dst.name for op in ops}
    assert "report.pdf" in dsts
    assert "report_1.pdf" in dsts


def test_plan_moves_conflict_with_existing_file(tmp_path: Path) -> None:
    """If target already exists on disk, the new file gets a numbered suffix."""
    dst_dir = tmp_path / "文档"
    dst_dir.mkdir()
    existing = dst_dir / "report.pdf"
    existing.write_bytes(b"existing")

    src = tmp_path / "report.pdf"
    src.write_bytes(b"new")
    pairs = [(_info(src), _clf("文档"))]
    ops = plan_moves(tmp_path, pairs)
    assert len(ops) == 1
    assert ops[0].dst.name == "report_1.pdf"
