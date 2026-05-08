"""Command-line entrypoint for marie_sxy.

Run ``marie_sxy --help`` after installing the package (``uv sync``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from marie_sxy import __version__
from marie_sxy.core import ClassificationCache, Scanner, classify_file
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
    """Root command - shared options live here."""
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
    """Scan a directory and print a summary of what was found.

    This is a Week-1 read-only command: nothing is moved or modified.
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

    with console.status(f"[bold cyan]Scanning {scanner.root}..."):
        result = scanner.scan()

    _render_summary(result, limit=limit)


def _render_summary(result, *, limit: int) -> None:
    """Pretty-print the scan result using rich."""
    console.print()
    console.rule(f"[bold]✨ marie_sxy scan: {result.root}")

    if result.total == 0:
        console.print("[yellow]No files found.[/yellow]")
        return

    # Top-line stats.
    console.print(
        f"[bold green]Found {result.total} files[/bold green] "
        f"(total {_human_size(result.total_size)}"
        + (f", {result.skipped} skipped" if result.skipped else "")
        + ")"
    )

    # Breakdown by extension (top 10).
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

    # Sample of files.
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
            help="Preview classification tree (default). File moves arrive in Week 4.",
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
) -> None:
    """Classify files under PATH and show a Rich tree (Week 2).

    Requires an LLM key for cloud models (see LiteLLM docs), or set
    ``MARIE_SXY_OFFLINE=1`` for built-in filename heuristics.

    Example: ``marie_sxy organize ~/Downloads --dry-run``
    """
    if not dry_run:
        err_console.print(
            "[yellow]--apply[/yellow] is not implemented yet (planned Week 4). "
            "Use [cyan]--dry-run[/cyan] to preview."
        )
        raise typer.Exit(code=1)

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
            clf = classify_file(info, cache=cache)
            pairs.append((info, clf))

    console.print()
    console.rule(f"[bold]✨ marie_sxy organize (dry-run): {result.root}")
    if result.total == 0:
        console.print("[yellow]No files found.[/yellow]")
        return

    if result.total > limit:
        console.print(
            f"[yellow]Showing tree for first {limit} of {result.total} files "
            f"(use --limit to raise the cap).[/yellow]"
        )

    nested = _merge_categories(pairs)
    tree = _nested_to_tree("[bold green]Suggested layout[/bold green]", nested)
    console.print(tree)


def _merge_categories(pairs: list[tuple[FileInfo, FileClassification]]) -> dict:
    """Build a nested dict from slash-separated category paths."""
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
    """Turn nested folders + ``__files__`` leaves into a :class:`rich.tree.Tree`."""
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


if __name__ == "__main__":  # pragma: no cover
    app()
