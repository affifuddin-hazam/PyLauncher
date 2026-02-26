"""Custom title bar for borderless window with drag support."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from pylauncher.constants import (
    BG_CARD,
    BG_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    DEEP_PINK,
    TRANSPARENT,
    FONT_TITLE_FAMILY,
    FONT_SIZE_TITLE,
    TITLE_BAR_HEIGHT,
)


class TitleBar(ctk.CTkFrame):
    """Borderless window title bar with drag-to-move and action buttons."""

    def __init__(
        self,
        master: ctk.CTk,
        on_settings: Callable[[], None],
        on_cli: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color=BG_CARD, height=TITLE_BAR_HEIGHT, corner_radius=0)
        self.pack_propagate(False)

        self._app_root = master
        self._offset_x = 0
        self._offset_y = 0

        # Title label
        self._title = ctk.CTkLabel(
            self,
            text="PyLauncher",
            font=(FONT_TITLE_FAMILY, FONT_SIZE_TITLE),
            text_color=TEXT_PRIMARY,
        )
        self._title.pack(side="left", padx=20)

        # Close button (rightmost)
        self._close_btn = ctk.CTkButton(
            self,
            text="✕",
            width=40,
            height=TITLE_BAR_HEIGHT,
            fg_color=TRANSPARENT,
            hover_color="#5c1a2a",
            text_color=TEXT_SECONDARY,
            font=("Segoe UI", 14),
            corner_radius=0,
            command=on_close,
        )
        self._close_btn.pack(side="right")

        # Settings button
        self._settings_btn = ctk.CTkButton(
            self,
            text="⚙",
            width=40,
            height=TITLE_BAR_HEIGHT,
            fg_color=TRANSPARENT,
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            font=("Segoe UI Symbol", 16),
            corner_radius=0,
            command=on_settings,
        )
        self._settings_btn.pack(side="right")

        # CLI button
        self._cli_btn = ctk.CTkButton(
            self,
            text="▸_",
            width=40,
            height=TITLE_BAR_HEIGHT,
            fg_color=TRANSPARENT,
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            font=("Consolas", 14),
            corner_radius=0,
            command=on_cli,
        )
        self._cli_btn.pack(side="right")

        # Drag bindings
        self.bind("<ButtonPress-1>", self._start_drag)
        self.bind("<B1-Motion>", self._do_drag)
        self._title.bind("<ButtonPress-1>", self._start_drag)
        self._title.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, event) -> None:
        self._offset_x = event.x
        self._offset_y = event.y

    def _do_drag(self, event) -> None:
        x = self._app_root.winfo_pointerx() - self._offset_x
        y = self._app_root.winfo_pointery() - self._offset_y
        self._app_root.geometry(f"+{x}+{y}")
