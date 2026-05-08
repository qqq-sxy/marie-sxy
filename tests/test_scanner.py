"""Unit tests for :class:`marie.core.scanner.Scanner`."""

from __future__ import annotations

from pathlib import Path

import pytest

from marie.core import Scanner
from marie.types import FileInfo, ScanResult

# --------------------------------------------------------------------- fixtures


@pytest.fixture()
def sample_tree(tmp_path: Path) -> Path:
    """Build a small directory tree:

    tmp/
    ├── a.txt
    ├── b.PDF                       (uppercase suffix)
    ├── .hidden_file
    ├── .hidden_dir/
    │   └── nope.txt
    ├── node_modules/               (ignored by default)
    │   └── junk.js
    ├── photos/
    │   ├── 1.jpg
    │   └── 2.jpg
    └── docs/
        └── deep/
            └── deeper.md
    """
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.PDF").write_text("pdf-bytes")
    (tmp_path / ".hidden_file").write_text("secret")

    hidden_dir = tmp_path / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "nope.txt").write_text("x")

    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "junk.js").write_text("x")

    photos = tmp_path / "photos"
    photos.mkdir()
    (photos / "1.jpg").write_text("img1")
    (photos / "2.jpg").write_text("img2")

    deep = tmp_path / "docs" / "deep"
    deep.mkdir(parents=True)
    (deep / "deeper.md").write_text("deep content")

    return tmp_path


# ------------------------------------------------------------------ basic scan


def test_scan_returns_scan_result(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    assert isinstance(result, ScanResult)
    assert result.root == sample_tree.resolve()
    assert all(isinstance(f, FileInfo) for f in result.files)


def test_scan_default_skips_hidden_and_ignored(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    names = {f.name for f in result.files}
    # visible files should be present
    assert {"a.txt", "b.PDF", "1.jpg", "2.jpg", "deeper.md"} <= names
    # hidden files / dirs / ignored dirs should be absent
    assert ".hidden_file" not in names
    assert "nope.txt" not in names
    assert "junk.js" not in names


def test_scan_total_count(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    assert result.total == 5


def test_scan_total_size(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    expected = sum(
        (sample_tree / rel).stat().st_size
        for rel in ["a.txt", "b.PDF", "photos/1.jpg", "photos/2.jpg", "docs/deep/deeper.md"]
    )
    assert result.total_size == expected


# ---------------------------------------------------------------- file metadata


def test_file_info_fields(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    a = next(f for f in result.files if f.name == "a.txt")
    assert a.suffix == ".txt"
    assert a.size == len("hello")
    assert a.is_hidden is False
    assert a.depth == 0


def test_suffix_is_lowercased(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    pdf = next(f for f in result.files if f.name == "b.PDF")
    assert pdf.suffix == ".pdf"


def test_depth_increases_with_nesting(sample_tree: Path) -> None:
    result = Scanner(sample_tree).scan()
    by_name = {f.name: f for f in result.files}
    assert by_name["a.txt"].depth == 0
    assert by_name["1.jpg"].depth == 1
    assert by_name["deeper.md"].depth == 2


# --------------------------------------------------------------------- options


def test_include_hidden(sample_tree: Path) -> None:
    result = Scanner(sample_tree, include_hidden=True).scan()
    names = {f.name for f in result.files}
    assert ".hidden_file" in names
    assert "nope.txt" in names  # from .hidden_dir


def test_non_recursive(sample_tree: Path) -> None:
    result = Scanner(sample_tree, recursive=False).scan()
    names = {f.name for f in result.files}
    assert names == {"a.txt", "b.PDF"}


def test_max_depth_limits_recursion(sample_tree: Path) -> None:
    # depth=1 should include photos/* but exclude docs/deep/deeper.md (depth 2)
    result = Scanner(sample_tree, max_depth=1).scan()
    names = {f.name for f in result.files}
    assert "1.jpg" in names
    assert "deeper.md" not in names


def test_custom_ignored_dirs(sample_tree: Path) -> None:
    # Override default ignores so node_modules is now visible,
    # but explicitly drop "photos" instead.
    result = Scanner(sample_tree, ignored_dirs={"photos"}).scan()
    names = {f.name for f in result.files}
    assert "junk.js" in names  # node_modules no longer ignored
    assert "1.jpg" not in names  # photos is now ignored


# -------------------------------------------------------------- error handling


def test_scan_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Scanner(tmp_path / "does_not_exist")


def test_scan_root_is_file_raises(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        Scanner(f)


# --------------------------------------------------------------- streaming API


def test_iter_files_yields_same_count(sample_tree: Path) -> None:
    streamed = list(Scanner(sample_tree).iter_files())
    aggregated = Scanner(sample_tree).scan().files
    assert len(streamed) == len(aggregated)


# --------------------------------------------------------------------- helpers


def test_size_human_formats() -> None:
    info = FileInfo(
        path=Path("/tmp/x"),
        name="x",
        suffix="",
        size=2048,
        modified_at=__import__("datetime").datetime.now(),
        is_hidden=False,
        depth=0,
    )
    assert info.size_human == "2.0 KB"
