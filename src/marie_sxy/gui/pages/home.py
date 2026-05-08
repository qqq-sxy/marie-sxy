"""Home page: directory picker + settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import flet as ft

from marie_sxy.gui import theme as T


def build(
    page: ft.Page,
    on_start: Callable[[Path, bool, str], None],
) -> ft.Control:
    """Return the home page control tree.

    on_start(root, offline, model) is called when the user confirms a directory.
    """
    # ── state ────────────────────────────────────────────────────────────────
    selected_path: list[Path] = []  # mutable container so closure can update

    offline_switch = ft.Switch(
        label="离线模式（无需 API Key）",
        value=os.environ.get("MARIE_SXY_OFFLINE", "").lower() in {"1", "true", "yes"},
        active_color=T.PRIMARY,
    )

    api_key_field = ft.TextField(
        label="API Key",
        password=True,
        can_reveal_password=True,
        value=os.environ.get("MARIE_SXY_API_KEY", ""),
        border_color=T.BORDER,
        focused_border_color=T.PRIMARY,
        border_radius=T.RADIUS,
        expand=True,
    )

    model_field = ft.TextField(
        label="模型",
        value=os.environ.get("MARIE_SXY_MODEL", "gpt-4o-mini"),
        border_color=T.BORDER,
        focused_border_color=T.PRIMARY,
        border_radius=T.RADIUS,
        expand=True,
        hint_text="gpt-4o-mini / deepseek/deepseek-chat / anthropic/claude-haiku-4-5",
    )

    path_label = ft.Text(
        "尚未选择文件夹",
        color=T.TEXT_SECONDARY,
        size=T.FONT_BODY,
        italic=True,
    )

    start_btn = ft.ElevatedButton(
        "开始整理",
        icon=ft.Icons.AUTO_FIX_HIGH,
        bgcolor=T.PRIMARY,
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
        disabled=True,
        height=48,
    )

    recent_col = ft.Column(spacing=6)

    # ── file picker ──────────────────────────────────────────────────────────
    async def pick_dir(_: ft.ControlEvent) -> None:
        result = await file_picker.get_directory_path(dialog_title="选择要整理的文件夹")
        if result:
            p = Path(result)
            selected_path.clear()
            selected_path.append(p)
            path_label.value = str(p)
            path_label.italic = False
            path_label.color = T.TEXT_PRIMARY
            start_btn.disabled = False
            page.update()

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # ── start button ─────────────────────────────────────────────────────────
    def on_start_click(_: ft.ControlEvent) -> None:
        if not selected_path:
            return
        # Apply settings to env so core modules pick them up
        if offline_switch.value:
            os.environ["MARIE_SXY_OFFLINE"] = "1"
        else:
            os.environ.pop("MARIE_SXY_OFFLINE", None)
            if api_key_field.value:
                os.environ["MARIE_SXY_API_KEY"] = api_key_field.value
            if model_field.value:
                os.environ["MARIE_SXY_MODEL"] = model_field.value

        on_start(
            selected_path[0],
            bool(offline_switch.value),
            model_field.value or "gpt-4o-mini",
        )

    start_btn.on_click = on_start_click

    # ── recent dirs from history ─────────────────────────────────────────────
    def _load_recent() -> None:
        try:
            from marie_sxy.core.history import History

            sessions = History.default().all_sessions()
            seen: list[Path] = []
            for s in reversed(sessions):
                if s.root not in seen:
                    seen.append(s.root)
                if len(seen) >= 5:
                    break
            for p in seen:
                chip = ft.ActionChip(
                    label=ft.Text(str(p), size=T.FONT_SMALL),
                    leading=ft.Icon(ft.Icons.HISTORY, size=14, color=T.PRIMARY),
                    on_click=lambda _, p=p: _select_recent(p),
                )
                recent_col.controls.append(chip)
        except Exception:
            pass

    def _select_recent(p: Path) -> None:
        if not p.exists():
            return
        selected_path.clear()
        selected_path.append(p)
        path_label.value = str(p)
        path_label.italic = False
        path_label.color = T.TEXT_PRIMARY
        start_btn.disabled = False
        page.update()

    _load_recent()

    # ── settings panel ───────────────────────────────────────────────────────
    settings_panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("设置", size=T.FONT_HEADING, weight=ft.FontWeight.BOLD, color=T.TEXT_PRIMARY),
                offline_switch,
                ft.Row([api_key_field], expand=True),
                ft.Row([model_field], expand=True),
            ],
            spacing=12,
        ),
        bgcolor=T.SURFACE,
        border_radius=T.RADIUS,
        padding=T.PADDING,
        border=ft.border.all(1, T.BORDER),
    )

    # ── layout ───────────────────────────────────────────────────────────────
    return ft.Container(
        content=ft.Column(
            [
                # hero
                ft.Container(height=40),
                ft.Text("✨ marie_sxy", size=T.FONT_TITLE, weight=ft.FontWeight.BOLD, color=T.PRIMARY),
                ft.Text(
                    "丢一个文件夹给我，还你一个井井有条的世界",
                    size=T.FONT_BODY,
                    color=T.TEXT_SECONDARY,
                ),
                ft.Container(height=32),

                # pick dir
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.FOLDER_OPEN, color=T.PRIMARY),
                                    ft.Text("选择文件夹", size=T.FONT_HEADING, weight=ft.FontWeight.W_600),
                                ],
                                spacing=8,
                            ),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=path_label,
                                        bgcolor=T.PRIMARY_LIGHT,
                                        border_radius=8,
                                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                        expand=True,
                                    ),
                                    ft.OutlinedButton(
                                        "浏览…",
                                        icon=ft.Icons.FOLDER,
                                        on_click=pick_dir,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=T.RADIUS)),
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Row([start_btn], alignment=ft.MainAxisAlignment.END),
                        ],
                        spacing=12,
                    ),
                    bgcolor=T.SURFACE,
                    border_radius=T.RADIUS,
                    padding=T.PADDING,
                    border=ft.border.all(1, T.BORDER),
                ),

                # recent
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("最近整理", size=T.FONT_SMALL, color=T.TEXT_SECONDARY),
                            recent_col,
                        ],
                        spacing=6,
                    ),
                    visible=len(recent_col.controls) > 0,
                ),

                ft.Container(height=12),
                settings_panel,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor=T.BG,
        padding=ft.padding.symmetric(horizontal=40, vertical=20),
        expand=True,
    )
