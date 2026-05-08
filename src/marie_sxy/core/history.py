"""Persistent operation history for undo support."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from marie_sxy.types import HistorySession, MoveOp

logger = logging.getLogger(__name__)


def default_history_path() -> Path:
    import os

    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "marie_sxy" / "history.json"


@dataclass
class UndoResult:
    session: HistorySession
    restored: list[MoveOp] = field(default_factory=list)
    failed: list[tuple[MoveOp, Exception]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.failed) == 0


class History:
    """Append-only JSON history of organize sessions.

    Each session stores the list of moves performed so they can be reversed.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_history_path()
        self._sessions: list[HistorySession] = []
        self._load()

    @classmethod
    def default(cls) -> History:
        return cls(default_history_path())

    # ------------------------------------------------------------------ I/O

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for entry in raw:
                try:
                    self._sessions.append(HistorySession.model_validate(entry))
                except Exception as exc:
                    logger.debug("Skipping invalid history entry: %s", exc)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load history %s: %s", self.path, exc)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [s.model_dump(mode="json") for s in self._sessions],
            ensure_ascii=False,
            indent=2,
        )
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------------ API

    def record(self, session: HistorySession) -> None:
        """Append a completed session to the history file."""
        self._sessions.append(session)
        self._save()

    def last_session(self) -> HistorySession | None:
        return self._sessions[-1] if self._sessions else None

    def all_sessions(self) -> list[HistorySession]:
        return list(self._sessions)

    def undo_last(self, *, dry_run: bool = False) -> UndoResult | None:
        """Reverse the last session's moves.

        Returns None if there is no history. On success the session is removed
        from the history log. On partial failure the session is kept so the
        user can inspect and retry.
        """
        session = self.last_session()
        if session is None:
            return None

        result = UndoResult(session=session)
        import shutil

        for op in reversed(session.ops):
            # Undo: move dst back to src
            if not op.dst.exists():
                exc = FileNotFoundError(f"Cannot undo: destination missing: {op.dst}")
                logger.warning("%s", exc)
                result.failed.append((op, exc))
                continue

            if dry_run:
                result.restored.append(op)
                continue

            try:
                op.src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(op.dst), str(op.src))
                result.restored.append(op)
                logger.debug("Restored %s → %s", op.dst, op.src)
            except Exception as exc:
                logger.warning("Failed to restore %s → %s: %s", op.dst, op.src, exc)
                result.failed.append((op, exc))

        if result.success and not dry_run:
            self._sessions.pop()
            self._save()

        return result


def new_session_id() -> str:
    return str(uuid.uuid4())


def make_session(root: Path, ops: list[MoveOp]) -> HistorySession:
    return HistorySession(
        session_id=new_session_id(),
        timestamp=datetime.now(tz=timezone.utc),
        root=root,
        ops=ops,
    )
