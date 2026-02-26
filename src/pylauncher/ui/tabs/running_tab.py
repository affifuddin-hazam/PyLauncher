"""Running scripts tab with dynamic sub-tabs and export."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from pylauncher.constants import (
    BG_CARD,
    BG_SURFACE,
    BG_HOVER,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    TEXT_PRIMARY,
    TEXT_DIM,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
    BUTTON_CORNER_RADIUS,
)
from pylauncher.ui.widgets.output_textbox import OutputTextbox

if TYPE_CHECKING:
    from pylauncher.app import PyLauncherApp


class RunningTab(ctk.CTkFrame):
    """Dynamic tabs for each running script with output and export."""

    def __init__(self, master: ctk.CTkBaseClass, app: "PyLauncherApp") -> None:
        super().__init__(master, fg_color=BG_CARD)
        self._app = app
        self._tab_map: dict[str, tuple[str, OutputTextbox]] = {}

        self._empty_label = ctk.CTkLabel(
            self, text="No scripts running.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), text_color=TEXT_DIM,
        )
        self._empty_label.pack(pady=100)

        self._tabview: ctk.CTkTabview | None = None

    def _ensure_tabview(self) -> ctk.CTkTabview:
        if self._tabview is None:
            self._empty_label.pack_forget()
            self._tabview = ctk.CTkTabview(
                self, fg_color=BG_CARD,
                segmented_button_fg_color=BG_SURFACE,
                segmented_button_selected_color=DEEP_PINK,
                segmented_button_selected_hover_color=DEEP_PINK_HOVER,
                segmented_button_unselected_color=BG_SURFACE,
                segmented_button_unselected_hover_color=BG_HOVER,
            )
            self._tabview.pack(fill="both", expand=True, padx=5, pady=5)
        return self._tabview

    def add_process_tab(self, folder_key: str, script_name: str) -> None:
        tabview = self._ensure_tabview()
        tab_name = script_name
        if tab_name in [name for name, _ in self._tab_map.values()]:
            tab_name = f"{script_name} ({folder_key})"

        tab_frame = tabview.add(tab_name)

        textbox = OutputTextbox(tab_frame)
        textbox.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        # Button row: Export + Close
        btn_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
        btn_frame.pack(pady=8)

        export_btn = ctk.CTkButton(
            btn_frame, text="Export",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_SURFACE, hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=100, height=35,
            command=lambda: self._export_output(textbox, script_name),
        )
        export_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            btn_frame, text="Close",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=100, height=35,
            command=lambda: self._on_close(folder_key),
        )
        close_btn.pack(side="left", padx=5)

        self._tab_map[folder_key] = (tab_name, textbox)

    def append_output(self, folder_key: str, line: str) -> None:
        if folder_key in self._tab_map:
            _, textbox = self._tab_map[folder_key]
            textbox.append_line(line)

    def mark_exited(self, folder_key: str, return_code: int) -> None:
        """Mark a script tab as exited without removing it."""
        if folder_key in self._tab_map:
            _, textbox = self._tab_map[folder_key]
            status = "finished" if return_code == 0 else f"crashed (code {return_code})"
            textbox.append_line(f"\n--- Process {status} ---")

    def remove_process_tab(self, folder_key: str) -> None:
        if folder_key not in self._tab_map:
            return
        tab_name, _ = self._tab_map.pop(folder_key)
        if self._tabview is not None:
            try:
                self._tabview.delete(tab_name)
            except ValueError:
                pass
        if not self._tab_map and self._tabview is not None:
            self._tabview.pack_forget()
            self._tabview = None
            self._empty_label.pack(pady=100)

    def _export_output(self, textbox: OutputTextbox, script_name: str) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{script_name}_{ts}.txt",
        )
        if path:
            Path(path).write_text(textbox.get_text(), encoding="utf-8")

    def _on_close(self, folder_key: str) -> None:
        if self._app.process_handler.is_running(folder_key):
            self._app.stop_script_by_key(folder_key)
        else:
            self.remove_process_tab(folder_key)
