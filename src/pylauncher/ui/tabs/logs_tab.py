"""General application log viewer tab with export."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from pylauncher.constants import (
    BG_CARD,
    BG_SURFACE,
    BG_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
)
from pylauncher.ui.widgets.output_textbox import OutputTextbox


class LogsTab(ctk.CTkFrame):
    """The 'Logs' tab with timestamped log viewer and Export button."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=BG_CARD)

        # Header with Export button
        header = ctk.CTkFrame(self, fg_color=BG_CARD)
        header.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            header, text="Application Logs",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT), text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            header, text="Export",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fg_color=BG_SURFACE, hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=8,
            width=70, height=28, command=self._export_logs,
        )
        export_btn.pack(side="right", padx=5)

        clear_btn = ctk.CTkButton(
            header, text="Clear",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fg_color=BG_SURFACE, hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=8,
            width=60, height=28, command=self.clear,
        )
        clear_btn.pack(side="right", padx=2)

        self._textbox = OutputTextbox(self, border_width=0)
        self._textbox.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._textbox.append_line(f"[{timestamp}] {message}")

    def clear(self) -> None:
        self._textbox.clear()

    def _export_logs(self) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"pylauncher_logs_{ts}.txt",
        )
        if path:
            Path(path).write_text(self._textbox.get_text(), encoding="utf-8")
