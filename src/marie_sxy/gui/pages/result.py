"""Result page: show execution outcome, undo button."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import flet as ft

from marie_sxy.gui import theme as T
from marie_sxy.core.executor import ExecuteResult
from marie_sxy.types import MoveOp


def build(
    page: ft.Page,
    root: Path,
    exec_result: ExecuteResult,
    on_undo: Callable[[], None],
    on_home: Callable[[], None],
) -> ft.Control:
    """Return the result page control tree."""
    moved_count = exec_result.success_count
    failed_count = exec_result.failure_count

    # ── moved files list ─────────────────────────────────────────────────────
    moved_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
    for op in exec_result.moved[:100]:
        try:
            src_rel = op.src.relative_to(root)
        except ValueError:
            src_rel = op.src
        try:
            dst_rel = op.dst.relative_to(root)
        except ValueError:
            dst_rel = op.dst
        moved_list.controls.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=T.SUCCESS),
                        ft.Text(str(src_rel), size=T.FONT_SMALL, color=T.TEXT_SECONDARY, expand=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text("→", size=T.FONT_SMALL, color=T.TEXT_SECONDARY),
                        ft.Text(str(dst_rel), size=T.FONT_SMALL, color=T.TEXT_PRIMARY, expand=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=6,
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                bgcolor=T.SURFACE,
                border=ft.border.all(1, T.BORDER),
            )
        )

    # ── failed list (if any) ─────────────────────────────────────────────────
    failed_section = ft.Column(
        [
            ft.Text(f"失败 {failed_count} 个：", color=T.ERROR, size=T.FONT_BODY, weight=ft.FontWeight.W_600),
            *[
                ft.Text(f"  {op.src.name}: {exc}", size=T.FONT_SMALL, color=T.ERROR)
                for op, exc in exec_result.failed
            ],
        ],
        spacing=4,
        visible=failed_count > 0,
    )

    # ── undo state ───────────────────────────────────────────────────────────
    undo_status = ft.Text("", size=T.FONT_BODY)

    def on_undo_click(_: ft.ControlEvent) -> None:
        try:
            from marie_sxy.core.history import History

            h = History.default()
            result = h.undo_last()
            if result is None:
                undo_status.value = "没有可撤销的操作"
            elif result.success:
                undo_status.value = f"✓ 已还原 {len(result.restored)} 个文件"
                undo_btn.disabled = True
                on_undo()
            else:
                undo_status.value = f"部分失败：{len(result.failed)} 个文件无法还原"
            page.update()
        except Exception as exc:
            undo_status.value = f"撤销出错：{exc}"
            page.update()

    undo_btn = ft.OutlinedButton(
        "撤销整理",
        icon=ft.Icons.UNDO,
        on_click=on_undo_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
        disabled=moved_count == 0,
        height=44,
    )

    home_btn = ft.ElevatedButton(
        "整理另一个文件夹",
        icon=ft.Icons.HOME,
        bgcolor=T.PRIMARY,
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
        on_click=lambda _: on_home(),
        height=44,
    )

    # ── summary banner ───────────────────────────────────────────────────────
    if moved_count > 0:
        banner_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=T.SUCCESS, size=48)
        banner_text = ft.Text(
            f"成功移动 {moved_count} 个文件！",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=T.SUCCESS,
        )
        banner_bg = "#F0FDF4"
    else:
        banner_icon = ft.Icon(ft.Icons.INFO, color=T.WARNING, size=48)
        banner_text = ft.Text("没有文件被移动", size=22, weight=ft.FontWeight.BOLD, color=T.WARNING)
        banner_bg = "#FFFBEB"

    banner = ft.Container(
        content=ft.Row([banner_icon, banner_text], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=banner_bg,
        border_radius=T.RADIUS,
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
    )

    return ft.Container(
        content=ft.Column(
            [
                # header
                ft.Row(
                    [
                        ft.Text("整理完成", size=T.FONT_TITLE, weight=ft.FontWeight.BOLD, color=T.TEXT_PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(str(root), size=T.FONT_SMALL, color=T.TEXT_SECONDARY, overflow=ft.TextOverflow.ELLIPSIS),
                    ]
                ),
                ft.Divider(color=T.BORDER),

                banner,
                failed_section,

                # moved list
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("移动明细", size=T.FONT_BODY, weight=ft.FontWeight.W_600, color=T.TEXT_SECONDARY),
                            moved_list,
                        ],
                        spacing=6,
                        expand=True,
                    ),
                    bgcolor=T.SURFACE,
                    border_radius=T.RADIUS,
                    padding=12,
                    border=ft.border.all(1, T.BORDER),
                    expand=True,
                ),

                # bottom actions
                ft.Divider(color=T.BORDER),
                ft.Row(
                    [
                        undo_btn,
                        ft.Text(undo_status.value, ref=ft.Ref[ft.Text]()),
                        undo_status,
                        ft.Container(expand=True),
                        home_btn,
                    ],
                    spacing=12,
                ),
            ],
            spacing=16,
            expand=True,
        ),
        bgcolor=T.BG,
        padding=ft.padding.symmetric(horizontal=32, vertical=20),
        expand=True,
    )
