"""Flet desktop application entry point."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from marie_sxy.gui import theme as T
from marie_sxy.types import MoveOp


def _main(page: ft.Page) -> None:
    page.title = "marie_sxy ✨"
    page.bgcolor = T.BG
    page.window.width = 960
    page.window.height = 680
    page.window.min_width = 720
    page.window.min_height = 520
    page.fonts = {}
    page.theme = ft.Theme(color_scheme_seed=T.PRIMARY)

    # ── router ────────────────────────────────────────────────────────────────

    def show_home() -> None:
        from marie_sxy.gui.pages import home

        page.controls.clear()
        page.controls.append(home.build(page, on_start=show_preview))
        page.update()

    def show_preview(root: Path, offline: bool, model: str) -> None:
        from marie_sxy.gui.pages import preview

        page.controls.clear()
        page.controls.append(
            preview.build(
                page,
                root=root,
                on_execute=lambda ops: show_executing(root, ops),
                on_back=show_home,
            )
        )
        page.update()

    def show_executing(root: Path, ops: list[MoveOp]) -> None:
        """Run execute_moves in a thread then navigate to result page."""
        import threading

        # Show a loading overlay while moving
        loading = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(color=T.PRIMARY),
                    ft.Text("正在移动文件…", size=T.FONT_BODY, color=T.TEXT_SECONDARY),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
            bgcolor=T.BG,
            expand=True,
            alignment=ft.alignment.center,
        )
        page.controls.clear()
        page.controls.append(loading)
        page.update()

        def _do_execute() -> None:
            from marie_sxy.core.executor import execute_moves
            from marie_sxy.core.history import History, make_session

            exec_result = execute_moves(ops)
            if exec_result.moved:
                session = make_session(root, exec_result.moved)
                History.default().record(session)

            show_result(root, exec_result)

        threading.Thread(target=_do_execute, daemon=True).start()

    def show_result(root, exec_result) -> None:
        from marie_sxy.gui.pages import result

        page.controls.clear()
        page.controls.append(
            result.build(
                page,
                root=root,
                exec_result=exec_result,
                on_undo=show_home,
                on_home=show_home,
            )
        )
        page.update()

    show_home()


def run_app() -> None:
    ft.app(target=_main)


if __name__ == "__main__":
    run_app()
