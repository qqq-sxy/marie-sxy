"""Command-line entrypoint for marie_sxy."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from marie_sxy import __version__
from marie_sxy.core import (
    ClassificationCache,
    History,
    Scanner,
    analyze_file,
    classify_file,
    execute_moves,
    make_session,
    plan_moves,
)
from marie_sxy.env_loader import load_dotenv_files
from marie_sxy.types import FileClassification, FileInfo

app = typer.Typer(
    name="marie_sxy",
    help="✨ AI-powered file organizer. Drop a folder, get magic.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True, style="bold red")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"marie_sxy {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    load_dotenv_files()


@app.command()
def scan(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to scan.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option("--recursive/--no-recursive", "-r/-R", help="Walk into sub-directories."),
    ] = True,
    include_hidden: Annotated[
        bool,
        typer.Option("--hidden/--no-hidden", help="Include dotfiles and dot-directories."),
    ] = False,
    max_depth: Annotated[
        int | None,
        typer.Option("--max-depth", "-d", help="Maximum recursion depth (root = 0)."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Show at most N rows in the table preview."),
    ] = 20,
) -> None:
    """Scan a directory and print a summary of what was found."""
    try:
        scanner = Scanner(
            root=path,
            recursive=recursive,
            include_hidden=include_hidden,
            max_depth=max_depth,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        err_console.print(f"Error: {exc}")
        raise typer.Exit(code=1) from exc

    with console.status(f"[bold cyan]Scanning {scanner.root}..."):
        result = scanner.scan()

    _render_summary(result, limit=limit)


@app.command()
def organize(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to classify.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run/--apply",
            help="Preview moves (default). Use --apply to execute.",
        ),
    ] = True,
    recursive: Annotated[
        bool,
        typer.Option("--recursive/--no-recursive", "-r/-R", help="Walk into sub-directories."),
    ] = True,
    include_hidden: Annotated[
        bool,
        typer.Option("--hidden/--no-hidden", help="Include dotfiles and dot-directories."),
    ] = False,
    max_depth: Annotated[
        int | None,
        typer.Option("--max-depth", "-d", help="Maximum recursion depth (root = 0)."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Classify at most N files (safety cap)."),
    ] = 200,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt when using --apply."),
    ] = False,
) -> None:
    """Classify files and show a move plan. Use --apply to execute.

    Example: ``marie_sxy organize ~/Downloads --apply``
    """
    try:
        scanner = Scanner(
            root=path,
            recursive=recursive,
            include_hidden=include_hidden,
            max_depth=max_depth,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        err_console.print(f"Error: {exc}")
        raise typer.Exit(code=1) from exc

    cache = ClassificationCache.default()
    pairs: list[tuple[FileInfo, FileClassification]] = []

    with console.status("[bold cyan]Scanning + classifying..."):
        result = scanner.scan()
        subset = result.files[:limit]
        for info in subset:
            hint = analyze_file(info)
            clf = classify_file(info, cache=cache, content_hint=hint)
            pairs.append((info, clf))

    console.print()
    console.rule(f"[bold]✨ marie_sxy organize: {result.root}")

    if result.total == 0:
        console.print("[yellow]No files found.[/yellow]")
        return

    if result.total > limit:
        console.print(
            f"[yellow]Showing plan for first {limit} of {result.total} files "
            f"(use --limit to raise the cap).[/yellow]"
        )

    ops = plan_moves(path, pairs)

    if dry_run:
        # Show classification tree + move plan
        nested = _merge_categories(pairs)
        tree = _nested_to_tree("[bold green]Suggested layout[/bold green]", nested)
        console.print(tree)

        if ops:
            from marie_sxy.ui.confirm import render_move_plan

            console.print()
            render_move_plan(ops, path)
            console.print(
                "\n[dim]Run with [bold]--apply[/bold] to execute these moves.[/dim]"
            )
        else:
            console.print("[green]All files are already in the right place.[/green]")
        return

    # --apply path
    if not ops:
        console.print("[green]All files are already in the right place. Nothing to do.[/green]")
        return

    from marie_sxy.ui.confirm import ask_confirm, render_move_plan

    render_move_plan(ops, path)
    console.print()

    if not yes and not ask_confirm("Execute these moves?"):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)

    history = History.default()
    exec_result = execute_moves(ops)
    session = make_session(path, exec_result.moved)
    if exec_result.moved:
        history.record(session)

    console.print()
    if exec_result.moved:
        console.print(
            f"[bold green]Moved {exec_result.success_count} file(s).[/bold green]"
        )
    if exec_result.failed:
        console.print(
            f"[bold red]{exec_result.failure_count} move(s) failed:[/bold red]"
        )
        for op, exc in exec_result.failed:
            console.print(f"  [red]{op.src.name}[/red]: {exc}")

    if exec_result.moved:
        console.print("[dim]Run [bold]marie_sxy undo[/bold] to reverse this session.[/dim]")


@app.command()
def undo(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--apply", help="Preview undo (default). Use --apply to execute."),
    ] = True,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Reverse the last organize session.

    Example: ``marie_sxy undo --apply``
    """
    history = History.default()
    session = history.last_session()

    if session is None:
        console.print("[yellow]No history found. Nothing to undo.[/yellow]")
        return

    console.print()
    console.rule("[bold]✨ marie_sxy undo")
    console.print(
        f"Last session: [cyan]{session.session_id}[/cyan] "
        f"at [dim]{session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim] "
        f"in [cyan]{session.root}[/cyan]"
    )
    console.print(f"Operations to reverse: [bold]{len(session.ops)}[/bold]")

    if not session.ops:
        console.print("[yellow]Session has no moves to reverse.[/yellow]")
        return

    # Show what will be undone
    from rich.table import Table as RichTable

    table = RichTable(title="Files to restore", header_style="bold magenta")
    table.add_column("Moved file (current)", style="cyan", overflow="fold")
    table.add_column("→  Original location", style="green", overflow="fold")
    for op in session.ops[:40]:
        table.add_row(str(op.dst), str(op.src))
    if len(session.ops) > 40:
        table.add_row(f"[dim]… {len(session.ops) - 40} more[/dim]", "")
    console.print(table)

    if dry_run:
        console.print("\n[dim]Run with [bold]--apply[/bold] to reverse these moves.[/dim]")
        return

    console.print()
    if not yes:
        from rich.prompt import Confirm

        if not Confirm.ask("Reverse these moves?"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=0)

    result = history.undo_last()
    if result is None:
        console.print("[yellow]Nothing to undo.[/yellow]")
        return

    console.print()
    if result.restored:
        console.print(f"[bold green]Restored {len(result.restored)} file(s).[/bold green]")
    if result.failed:
        console.print(f"[bold red]{len(result.failed)} restore(s) failed:[/bold red]")
        for op, exc in result.failed:
            console.print(f"  [red]{op.dst.name}[/red]: {exc}")


# ─── helpers ────────────────────────────────────────────────────────────────


def _render_summary(result, *, limit: int) -> None:
    console.print()
    console.rule(f"[bold]✨ marie_sxy scan: {result.root}")

    if result.total == 0:
        console.print("[yellow]No files found.[/yellow]")
        return

    console.print(
        f"[bold green]Found {result.total} files[/bold green] "
        f"(total {_human_size(result.total_size)}"
        + (f", {result.skipped} skipped" if result.skipped else "")
        + ")"
    )

    ext_counts: dict[str, int] = {}
    for f in result.files:
        ext = f.suffix or "(no ext)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    top_exts = sorted(ext_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]

    ext_table = Table(title="Top file types", show_header=True, header_style="bold magenta")
    ext_table.add_column("Extension", style="cyan")
    ext_table.add_column("Count", justify="right")
    for ext, count in top_exts:
        ext_table.add_row(ext, str(count))
    console.print(ext_table)

    sample_table = Table(
        title=f"First {min(limit, result.total)} files",
        show_header=True,
        header_style="bold magenta",
    )
    sample_table.add_column("Name", style="cyan", overflow="fold")
    sample_table.add_column("Size", justify="right")
    sample_table.add_column("Modified", style="dim")
    sample_table.add_column("Depth", justify="right")
    for f in result.files[:limit]:
        sample_table.add_row(
            f.name,
            f.size_human,
            f.modified_at.strftime("%Y-%m-%d %H:%M"),
            str(f.depth),
        )
    console.print(sample_table)

    if result.total > limit:
        console.print(f"[dim]... and {result.total - limit} more files[/dim]")


def _merge_categories(pairs: list[tuple[FileInfo, FileClassification]]) -> dict:
    nested: dict = {}
    for info, clf in pairs:
        parts = [p.strip() for p in clf.category.split("/") if p.strip()]
        if not parts:
            parts = ["未分类"]
        node = nested
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                leaf = node.setdefault(part, {})
                leaf.setdefault("__files__", []).append(info.name)
            else:
                node = node.setdefault(part, {})
    return nested


def _nested_to_tree(title: str, node: dict) -> Tree:
    root = Tree(title)
    subdirs = sorted(k for k in node if k != "__files__")
    for key in subdirs:
        root.add(_nested_to_tree(f"[cyan]📁 {key}[/cyan]", node[key]))
    for fname in sorted(node.get("__files__", [])):
        root.add(f"📄 {fname}")
    return root


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@app.command()
def gui() -> None:
    """Launch the desktop GUI window.

    Requires the gui extra: ``uv sync --extra gui``
    """
    try:
        from marie_sxy.gui.app import run_app
    except ImportError:
        err_console.print(
            "GUI dependencies not installed. Run: [cyan]uv sync --extra gui[/cyan]"
        )
        raise typer.Exit(code=1)

    run_app()


if __name__ == "__main__":  # pragma: no cover
    app()
