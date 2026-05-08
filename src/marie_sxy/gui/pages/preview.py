"""Preview page: scan + classify in background, show plan, confirm."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import flet as ft

from marie_sxy.gui import theme as T
from marie_sxy.types import FileClassification, FileInfo, MoveOp


def build(
    page: ft.Page,
    root: Path,
    on_execute: Callable[[list[MoveOp]], None],
    on_back: Callable[[], None],
) -> ft.Control:
    """Return the preview page control tree.

    Launches scanning + classification in a background thread.
    on_execute(ops) is called when the user confirms.
    on_back() returns to the home page.
    """
    # ── mutable state ────────────────────────────────────────────────────────
    pairs: list[tuple[FileInfo, FileClassification]] = []
    ops_box: list[list[MoveOp]] = [[]]  # ops_box[0] = current ops

    # ── UI elements ──────────────────────────────────────────────────────────
    status_text = ft.Text("正在扫描文件…", color=T.TEXT_SECONDARY, size=T.FONT_BODY)
    progress_bar = ft.ProgressBar(value=None, color=T.PRIMARY, bgcolor=T.BORDER)
    progress_label = ft.Text("", size=T.FONT_SMALL, color=T.TEXT_SECONDARY)

    left_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
    right_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)

    execute_btn = ft.ElevatedButton(
        "执行整理",
        icon=ft.Icons.CHECK_CIRCLE,
        bgcolor=T.PRIMARY,
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
        disabled=True,
        height=44,
    )

    back_btn = ft.OutlinedButton(
        "返回",
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda _: on_back(),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
        height=44,
    )

    summary_text = ft.Text("", size=T.FONT_BODY, color=T.TEXT_PRIMARY)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _cat_icon(category: str) -> str:
        c = category.lower()
        if "图片" in c or "photo" in c or "image" in c:
            return "🖼️"
        if "代码" in c or "code" in c:
            return "💻"
        if "视频" in c or "video" in c:
            return "🎬"
        if "音频" in c or "audio" in c or "music" in c:
            return "🎵"
        if "压缩" in c or "archive" in c or "zip" in c:
            return "🗜️"
        if "安装" in c or "install" in c or "dmg" in c:
            return "📦"
        return "📄"

    def _build_tree(op_list: list[MoveOp]) -> None:
        """Populate right_col with a folder tree of destinations."""
        right_col.controls.clear()
        if not op_list:
            right_col.controls.append(
                ft.Text("所有文件已在正确位置 ✓", color=T.SUCCESS, size=T.FONT_BODY)
            )
            page.update()
            return

        # group by top-level category
        tree: dict[str, list[str]] = {}
        for op in op_list:
            parts = op.dst.relative_to(root).parts
            folder = "/".join(parts[:-1]) if len(parts) > 1 else "根目录"
            tree.setdefault(folder, []).append(parts[-1])

        for folder, files in sorted(tree.items()):
            icon = _cat_icon(folder)
            right_col.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{icon} {folder}",
                                size=T.FONT_BODY,
                                weight=ft.FontWeight.W_600,
                                color=T.TEXT_PRIMARY,
                            ),
                            *[
                                ft.Text(
                                    f"   📄 {f}",
                                    size=T.FONT_SMALL,
                                    color=T.TEXT_SECONDARY,
                                )
                                for f in sorted(files)
                            ],
                        ],
                        spacing=2,
                    ),
                    bgcolor=T.PRIMARY_LIGHT,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                )
            )
        page.update()

    # ── background worker ────────────────────────────────────────────────────

    def _run_scan() -> None:
        try:
            from marie_sxy.core import (
                ClassificationCache,
                Scanner,
                analyze_file,
                classify_file,
                plan_moves,
            )

            scanner = Scanner(root=root)
            scan_result = scanner.scan()
            total = scan_result.total

            if total == 0:
                status_text.value = "该文件夹内没有找到文件"
                progress_bar.value = 1.0
                summary_text.value = "空文件夹，无需整理"
                page.update()
                return

            status_text.value = f"找到 {total} 个文件，正在分类…"
            cache = ClassificationCache.default()

            left_col.controls.clear()
            for i, info in enumerate(scan_result.files):
                hint = analyze_file(info)
                clf = classify_file(info, cache=cache, content_hint=hint)
                pairs.append((info, clf))

                progress_bar.value = (i + 1) / total
                progress_label.value = f"{i + 1} / {total}"

                left_col.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.DESCRIPTION, size=14, color=T.PRIMARY),
                                ft.Text(info.name, size=T.FONT_SMALL, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(info.size_human, size=T.FONT_SMALL, color=T.TEXT_SECONDARY),
                            ],
                            spacing=6,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6,
                        bgcolor=T.SURFACE,
                        border=ft.border.all(1, T.BORDER),
                    )
                )
                page.update()

            ops = plan_moves(root, pairs)
            ops_box[0] = ops

            status_text.value = "分类完成 ✓"
            summary_text.value = (
                f"共 {total} 个文件，需要移动 {len(ops)} 个"
                if ops
                else f"共 {total} 个文件，已全部在正确位置 ✓"
            )
            execute_btn.disabled = len(ops) == 0
            _build_tree(ops)

        except Exception as exc:
            status_text.value = f"出错：{exc}"
            progress_bar.color = T.ERROR
            page.update()

    def on_execute_click(_: ft.ControlEvent) -> None:
        on_execute(ops_box[0])

    execute_btn.on_click = on_execute_click

    # start background thread
    threading.Thread(target=_run_scan, daemon=True).start()

    # ── layout ────────────────────────────────────────────────────────────────
    return ft.Container(
        content=ft.Column(
            [
                # top bar
                ft.Row(
                    [
                        back_btn,
                        ft.Text(
                            f"整理预览：{root}",
                            size=T.FONT_BODY,
                            color=T.TEXT_SECONDARY,
                            expand=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Divider(color=T.BORDER),

                # status
                ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color=T.PRIMARY), status_text], spacing=8),
                progress_bar,
                ft.Row([ft.Container(expand=True), progress_label]),

                # split view
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("原始文件", weight=ft.FontWeight.W_600, size=T.FONT_BODY, color=T.TEXT_SECONDARY),
                                    ft.Divider(color=T.BORDER),
                                    left_col,
                                ],
                                spacing=6,
                                expand=True,
                            ),
                            expand=1,
                            bgcolor=T.SURFACE,
                            border_radius=T.RADIUS,
                            padding=12,
                            border=ft.border.all(1, T.BORDER),
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("整理后布局", weight=ft.FontWeight.W_600, size=T.FONT_BODY, color=T.TEXT_SECONDARY),
                                    ft.Divider(color=T.BORDER),
                                    right_col,
                                ],
                                spacing=6,
                                expand=True,
                            ),
                            expand=1,
                            bgcolor=T.SURFACE,
                            border_radius=T.RADIUS,
                            padding=12,
                            border=ft.border.all(1, T.BORDER),
                        ),
                    ],
                    spacing=16,
                    expand=True,
                ),

                # bottom
                ft.Divider(color=T.BORDER),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SUMMARIZE, color=T.TEXT_SECONDARY, size=16),
                        summary_text,
                        ft.Container(expand=True),
                        execute_btn,
                    ],
                    spacing=8,
                ),
            ],
            spacing=12,
            expand=True,
        ),
        bgcolor=T.BG,
        padding=ft.padding.symmetric(horizontal=32, vertical=20),
        expand=True,
    )
