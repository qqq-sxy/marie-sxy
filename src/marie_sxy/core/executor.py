"""Execute a list of MoveOps: create directories, move files, report results."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field

from marie_sxy.types import MoveOp

logger = logging.getLogger(__name__)


@dataclass
class ExecuteResult:
    moved: list[MoveOp] = field(default_factory=list)
    failed: list[tuple[MoveOp, Exception]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.moved) + len(self.failed)

    @property
    def success_count(self) -> int:
        return len(self.moved)

    @property
    def failure_count(self) -> int:
        return len(self.failed)


def execute_moves(ops: list[MoveOp], *, dry_run: bool = False) -> ExecuteResult:
    """Perform the moves described in *ops*.

    Parameters
    ----------
    ops:
        List of MoveOp to execute.
    dry_run:
        If True, validate paths but do NOT touch the filesystem.

    Returns
    -------
    ExecuteResult with successfully moved ops and any failures.
    """
    result = ExecuteResult()

    for op in ops:
        if not op.src.exists():
            exc = FileNotFoundError(f"Source missing: {op.src}")
            logger.warning("Skipping missing source: %s", op.src)
            result.failed.append((op, exc))
            continue

        if dry_run:
            result.moved.append(op)
            continue

        try:
            op.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(op.src), str(op.dst))
            result.moved.append(op)
            logger.debug("Moved %s → %s", op.src, op.dst)
        except Exception as exc:
            logger.warning("Failed to move %s → %s: %s", op.src, op.dst, exc)
            result.failed.append((op, exc))

    return result
