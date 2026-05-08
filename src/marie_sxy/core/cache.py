"""Persistent JSON cache for classification results (keyed by path + mtime + size)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from marie_sxy.types import FileClassification, FileInfo

logger = logging.getLogger(__name__)


def default_cache_path() -> Path:
    """Return ``~/.cache/marie_sxy/classifications.json`` (respects ``XDG_CACHE_HOME``)."""
    import os

    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base) if base else Path.home() / ".cache"
    return root / "marie_sxy" / "classifications.json"


def cache_key_for_file(info: FileInfo) -> str:
    """Stable short key so edits to a file invalidate the entry."""
    raw = f"{info.path.resolve()}|{info.size}|{info.modified_at.timestamp():.6f}"
    return hashlib.sha256(raw.encode()).hexdigest()


class ClassificationCache:
    """Append-only style JSON store; small enough for interactive CLI use."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_cache_path()
        self._data: dict[str, dict] = {}
        self._load()

    @classmethod
    def default(cls) -> ClassificationCache:
        return cls(default_cache_path())

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            text = self.path.read_text(encoding="utf-8")
            raw = json.loads(text)
            if isinstance(raw, dict):
                self._data = raw
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load classification cache %s: %s", self.path, exc)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.path)

    def get(self, key: str) -> FileClassification | None:
        row = self._data.get(key)
        if not row:
            return None
        try:
            return FileClassification.model_validate(row)
        except Exception:
            logger.debug("Dropping invalid cache row for key digest")
            return None

    def set(self, key: str, value: FileClassification) -> None:
        self._data[key] = value.model_dump(mode="json")
        self._save()
