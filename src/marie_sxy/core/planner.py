"""Generate a conflict-free list of MoveOps from classification results."""

from __future__ import annotations

from pathlib import Path

from marie_sxy.types import FileClassification, FileInfo, MoveOp


def plan_moves(
    root: Path,
    pairs: list[tuple[FileInfo, FileClassification]],
) -> list[MoveOp]:
    """Return a MoveOp list for all files that need to be moved.

    Rules:
    - Destination = root / category_path / filename (or suggested_name).
    - Files already in the correct location are skipped.
    - Name collisions (between proposed destinations) are resolved by
      appending _1, _2, … before the extension.
    - Files that would collide with an *existing* file on disk are also
      disambiguated the same way.
    """
    ops: list[MoveOp] = []
    claimed: set[Path] = set()  # destinations already committed in this plan

    for info, clf in pairs:
        target_name = clf.suggested_name or info.name
        # Build destination directory from category (slash-separated segments)
        segments = [s.strip() for s in clf.category.split("/") if s.strip()]
        dst_dir = root.joinpath(*segments) if segments else root
        ideal_dst = dst_dir / target_name

        # Skip files that are already in the right place (same resolved path).
        if ideal_dst.resolve() == info.path.resolve():
            claimed.add(ideal_dst.resolve())
            continue

        dst = _resolve_conflict(ideal_dst, claimed)
        claimed.add(dst)
        ops.append(MoveOp(src=info.path, dst=dst))

    return ops


def _resolve_conflict(candidate: Path, claimed: set[Path]) -> Path:
    """Append _1, _2, … before the extension until the path is free."""
    if candidate not in claimed and not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    parent = candidate.parent
    counter = 1
    while True:
        new_candidate = parent / f"{stem}_{counter}{suffix}"
        if new_candidate not in claimed and not new_candidate.exists():
            return new_candidate
        counter += 1
