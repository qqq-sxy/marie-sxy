"""Shared data models used across Marie modules."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class FileInfo(BaseModel):
    """Metadata about a single file discovered by the scanner.

    Designed to be serialisable so it can be cached / sent to LLMs.
    """

    model_config = ConfigDict(frozen=True)

    path: Path = Field(..., description="Absolute path to the file.")
    name: str = Field(..., description="File name (basename).")
    suffix: str = Field(..., description="Lowercased extension including the dot, e.g. '.pdf'.")
    size: int = Field(..., ge=0, description="File size in bytes.")
    modified_at: datetime = Field(..., description="Last modification time.")
    is_hidden: bool = Field(..., description="Whether the file is hidden (name starts with '.').")
    depth: int = Field(..., ge=0, description="Depth from the scan root (root files are 0).")

    @property
    def size_human(self) -> str:
        """Human-readable file size, e.g. '1.2 MB'."""
        size = float(self.size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class ScanResult(BaseModel):
    """Aggregate result returned by Scanner."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    root: Path
    files: list[FileInfo]
    skipped: int = Field(default=0, description="Number of entries skipped (errors / filtered).")

    @property
    def total(self) -> int:
        return len(self.files)

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)
