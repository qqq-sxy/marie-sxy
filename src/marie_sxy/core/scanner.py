"""File scanner: walks a directory tree and yields :class:`FileInfo` objects.

The scanner intentionally does NOT touch file *contents* - that is the
responsibility of the analyzer / extractor layer. Keeping responsibilities
separated makes Scanner trivial to unit-test against synthetic fixtures.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path

from marie_sxy.types import FileInfo, ScanResult

logger = logging.getLogger(__name__)

DEFAULT_IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".idea",
        ".vscode",
        ".DS_Store",
    }
)


class Scanner:
    """Recursively scan a directory and collect file metadata.

    Parameters
    ----------
    root:
        Directory to scan. Must exist and be a directory.
    recursive:
        Walk into sub-directories. Default ``True``.
    include_hidden:
        Include dotfiles / dotdirs. Default ``False``.
    ignored_dirs:
        Directory names to skip entirely (matched on basename).
        Defaults to a sensible set (``.git``, ``node_modules``, ...).
    follow_symlinks:
        Whether to follow symbolic links. Default ``False`` for safety.
    max_depth:
        Optional cap on recursion depth (root files are depth 0).
    """

    def __init__(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
        include_hidden: bool = False,
        ignored_dirs: Iterable[str] | None = None,
        follow_symlinks: bool = False,
        max_depth: int | None = None,
    ) -> None:
        root_path = Path(root).expanduser().resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Scan root does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Scan root is not a directory: {root_path}")

        self.root: Path = root_path
        self.recursive: bool = recursive
        self.include_hidden: bool = include_hidden
        self.ignored_dirs: frozenset[str] = (
            DEFAULT_IGNORED_DIRS if ignored_dirs is None else frozenset(ignored_dirs)
        )
        self.follow_symlinks: bool = follow_symlinks
        self.max_depth: int | None = max_depth

    # ------------------------------------------------------------------ API

    def scan(self) -> ScanResult:
        """Run the scan and return the aggregate :class:`ScanResult`."""
        files: list[FileInfo] = []
        skipped = 0
        for item in self._iter_paths():
            try:
                info = self._build_file_info(item.path, item.depth)
            except OSError as exc:
                logger.debug("Skipping %s: %s", item.path, exc)
                skipped += 1
                continue
            files.append(info)
        return ScanResult(root=self.root, files=files, skipped=skipped)

    def iter_files(self) -> Iterator[FileInfo]:
        """Stream :class:`FileInfo` objects one by one (memory-friendly)."""
        for item in self._iter_paths():
            try:
                yield self._build_file_info(item.path, item.depth)
            except OSError as exc:
                logger.debug("Skipping %s: %s", item.path, exc)
                continue

    # ---------------------------------------------------------- internals

    def _iter_paths(self) -> Iterator[_WalkItem]:
        """Yield candidate file paths along with their depth from root."""
        yield from self._walk(self.root, depth=0)

    def _walk(self, directory: Path, *, depth: int) -> Iterator[_WalkItem]:
        if self.max_depth is not None and depth > self.max_depth:
            return
        try:
            entries = list(directory.iterdir())
        except (PermissionError, OSError) as exc:
            logger.debug("Cannot list %s: %s", directory, exc)
            return

        # Sort for deterministic ordering (helps testing & stable UI).
        entries.sort(key=lambda p: p.name.lower())

        for entry in entries:
            name = entry.name
            is_hidden = name.startswith(".")

            if entry.is_symlink() and not self.follow_symlinks:
                continue

            if entry.is_dir():
                if not self.recursive:
                    continue
                if name in self.ignored_dirs:
                    continue
                if is_hidden and not self.include_hidden:
                    continue
                yield from self._walk(entry, depth=depth + 1)
            elif entry.is_file():
                if is_hidden and not self.include_hidden:
                    continue
                yield _WalkItem(path=entry, depth=depth)
            # Other entry types (sockets, devices, ...) are ignored.

    def _build_file_info(self, path: Path, depth: int) -> FileInfo:
        stat = path.stat()
        return FileInfo(
            path=path,
            name=path.name,
            suffix=path.suffix.lower(),
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            is_hidden=path.name.startswith("."),
            depth=depth,
        )


class _WalkItem:
    """Lightweight tuple-like container used during traversal."""

    __slots__ = ("depth", "path")

    def __init__(self, path: Path, depth: int) -> None:
        self.path = path
        self.depth = depth
