"""Interactive confirmation UI for proposed file moves."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from marie_sxy.types import MoveOp

console = Console()


def render_move_plan(ops: list[MoveOp], root: Path, *, max_rows: int = 40) -> None:
    """Print a Rich table summarising the proposed moves."""
    if not ops:
        console.print("[yellow]No files need to be moved.[/yellow]")
        return

    table = Table(
        title=f"Proposed moves ({len(ops)} files)",
        show_header=True,
        header_style="bold magenta",
        expand=False,
    )
    table.add_column("Source (relative)", style="cyan", overflow="fold", ratio=4)
    table.add_column("→  Destination (relative)", style="green", overflow="fold", ratio=5)

    shown = ops[:max_rows]
    for op in shown:
        try:
            src_rel = op.src.relative_to(root)
        except ValueError:
            src_rel = op.src
        try:
            dst_rel = op.dst.relative_to(root)
        except ValueError:
            dst_rel = op.dst
        table.add_row(str(src_rel), str(dst_rel))

    if len(ops) > max_rows:
        table.add_row(
            f"[dim]… {len(ops) - max_rows} more[/dim]",
            "",
        )

    console.print(table)


def ask_confirm(prompt: str = "Execute these moves?") -> bool:
    """Prompt the user for Y/N confirmation. Returns True for yes."""
    from rich.prompt import Confirm

    return Confirm.ask(prompt)
