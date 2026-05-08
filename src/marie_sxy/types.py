"""Shared data models used across marie_sxy modules."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


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


class FileClassification(BaseModel):
    """LLM / heuristic output for where a file should live."""

    model_config = ConfigDict(frozen=True)

    category: str = Field(
        ...,
        description='Target folder path using "/" segments, e.g. "文档/发票".',
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(default="", description="Short rationale.")
    suggested_name: str | None = Field(
        default=None,
        description="Optional better filename; None to keep the original.",
    )


class MoveOp(BaseModel):
    """A single file-move operation: source → destination."""

    model_config = ConfigDict(frozen=True)

    src: Path = Field(..., description="Absolute path of the file before the move.")
    dst: Path = Field(..., description="Absolute path of the file after the move.")

    @field_validator("src", "dst", mode="before")
    @classmethod
    def _coerce_path(cls, v: object) -> Path:
        return Path(v)

    @field_serializer("src", "dst")
    def _ser_path(self, v: Path) -> str:
        return str(v)


class HistorySession(BaseModel):
    """One complete organize-and-move session recorded for undo."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str = Field(..., description="UUID or timestamp-based unique ID.")
    timestamp: datetime = Field(..., description="When this session ran.")
    root: Path = Field(..., description="Directory that was organized.")
    ops: list[MoveOp] = Field(default_factory=list, description="Moves performed.")

    @field_validator("root", mode="before")
    @classmethod
    def _coerce_root(cls, v: object) -> Path:
        return Path(v)

    @field_serializer("root")
    def _ser_root(self, v: Path) -> str:
        return str(v)

    @field_serializer("timestamp")
    def _ser_ts(self, v: datetime) -> str:
        return v.isoformat()


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
