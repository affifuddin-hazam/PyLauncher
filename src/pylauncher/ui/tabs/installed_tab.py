"""Installed scripts tab with search, tag filtering, bulk actions, and Import."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from pylauncher.constants import (
    BG_CARD,
    BG_INPUT,
    BG_SURFACE,
    BG_HOVER,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_DIM,
    BORDER_COLOR,
    SCROLLBAR_COLOR,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
    INPUT_CORNER_RADIUS,
    IMPORT_BUTTON_WIDTH,
    IMPORT_BUTTON_HEIGHT,
    BUTTON_CORNER_RADIUS,
)
from pylauncher.core.script_manager import ScriptInfo
from pylauncher.ui.widgets.script_row import ScriptRow

if TYPE_CHECKING:
    from pylauncher.app import PyLauncherApp


class InstalledTab(ctk.CTkFrame):
    """Installed scripts list with search, tag filter, bulk actions, and Import."""

    def __init__(self, master: ctk.CTkBaseClass, app: "PyLauncherApp") -> None:
        super().__init__(master, fg_color=BG_CARD)
        self._app = app
        self._rows: dict[str, ScriptRow] = {}
        self._script_order: list[str] = []
        self._active_tag: str | None = None

        # ── Row 1: Header with search, bulk actions, import ──
        header = ctk.CTkFrame(self, fg_color=BG_CARD)
        header.pack(fill="x", padx=10, pady=(10, 3))

        # Select All checkbox
        self._select_all_var = ctk.BooleanVar(value=False)
        self._select_all_cb = ctk.CTkCheckBox(
            header, text="", variable=self._select_all_var,
            width=20, height=20, checkbox_width=18, checkbox_height=18,
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            border_color=BORDER_COLOR, command=self._on_select_all,
        )
        self._select_all_cb.pack(side="left", padx=(0, 8))

        # Search entry
        self._search_entry = ctk.CTkEntry(
            header, placeholder_text="Search scripts...",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BORDER_COLOR, corner_radius=INPUT_CORNER_RADIUS,
            width=200, height=35,
        )
        self._search_entry.pack(side="left", padx=(0, 10))
        self._search_entry.bind("<KeyRelease>", self._apply_filters)

        # Import button (rightmost)
        self._import_btn = ctk.CTkButton(
            header, text="Import",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=100, height=35, command=self._on_import,
        )
        self._import_btn.pack(side="right")

        # Bulk action buttons
        for text, cmd in [
            ("Install All", self._on_install_all),
            ("Stop All", self._on_stop_all),
            ("Start All", self._on_start_all),
        ]:
            btn = ctk.CTkButton(
                header, text=text,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                fg_color=BG_SURFACE, hover_color=BG_HOVER,
                text_color=TEXT_SECONDARY, corner_radius=8,
                width=80, height=35, command=cmd,
            )
            btn.pack(side="right", padx=3)

        # ── Row 2: Tag filter chips ──
        self._tags_frame = ctk.CTkFrame(self, fg_color=BG_CARD, height=0)
        self._tags_frame.pack(fill="x", padx=10, pady=(0, 3))
        self._tag_buttons: dict[str | None, ctk.CTkButton] = {}

        # ── Scrollable frame ──
        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_SURFACE, corner_radius=10,
            scrollbar_button_color=SCROLLBAR_COLOR,
            scrollbar_button_hover_color=DEEP_PINK,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=10, pady=(3, 10))

        # Empty state
        self._empty_label = ctk.CTkLabel(
            self._scroll_frame,
            text="No scripts installed. Click Import or press Ctrl+I to add a script.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), text_color=TEXT_DIM,
        )

    def refresh_scripts(self) -> None:
        """Re-scan scripts dir and rebuild all rows."""
        for widget in self._scroll_frame.winfo_children():
            if widget != self._empty_label:
                widget.destroy()
        self._rows.clear()
        self._script_order.clear()

        scripts = self._app.script_manager.discover_all()

        if not scripts:
            self._empty_label.pack(pady=100)
            self._rebuild_tag_chips([])
            return

        self._empty_label.pack_forget()
        self._rebuild_tag_chips(scripts)

        for script_info in scripts:
            folder_key = script_info.folder_path.name
            row = ScriptRow(
                self._scroll_frame,
                script_info=script_info,
                on_start=self._app.start_script,
                on_stop=self._app.stop_script,
                on_install=self._app.install_requirements,
                on_open_folder=lambda si: self._app.script_manager.open_folder(si),
                on_delete=self._app.delete_script,
                on_schedule=self._app.open_schedule,
                is_running=self._app.process_handler.is_running(folder_key),
                on_check_changed=self._on_check_changed,
            )
            row.pack(fill="x", padx=5, pady=3)
            self._rows[folder_key] = row
            self._script_order.append(folder_key)

        self._apply_filters()

    def update_script_state(self, folder_key: str, running: bool) -> None:
        if folder_key in self._rows:
            self._rows[folder_key].set_running(running)

    # ── Tag chips ──

    def _rebuild_tag_chips(self, scripts: list[ScriptInfo]) -> None:
        for w in self._tags_frame.winfo_children():
            w.destroy()
        self._tag_buttons.clear()

        all_tags: set[str] = set()
        for s in scripts:
            all_tags.update(s.meta.tag_list)

        if not all_tags:
            return

        # "All" chip
        all_btn = ctk.CTkButton(
            self._tags_frame, text="All",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fg_color=DEEP_PINK if self._active_tag is None else BG_SURFACE,
            hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            corner_radius=12, width=50, height=26,
            command=lambda: self._filter_by_tag(None),
        )
        all_btn.pack(side="left", padx=2, pady=3)
        self._tag_buttons[None] = all_btn

        for tag in sorted(all_tags):
            btn = ctk.CTkButton(
                self._tags_frame, text=tag,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                fg_color=DEEP_PINK if self._active_tag == tag else BG_SURFACE,
                hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
                corner_radius=12, width=60, height=26,
                command=lambda t=tag: self._filter_by_tag(t),
            )
            btn.pack(side="left", padx=2, pady=3)
            self._tag_buttons[tag] = btn

    def _filter_by_tag(self, tag: str | None) -> None:
        self._active_tag = tag
        # Update chip colors
        for t, btn in self._tag_buttons.items():
            btn.configure(fg_color=DEEP_PINK if t == tag else BG_SURFACE)
        self._apply_filters()

    # ── Filtering ──

    def _apply_filters(self, event=None) -> None:
        """Apply both search and tag filters, preserving order."""
        query = self._search_entry.get().lower().strip()
        for key in self._script_order:
            row = self._rows.get(key)
            if row is None:
                continue
            name_match = not query or query in row.script_info.meta.script_name.lower() or query in key.lower()
            tag_match = self._active_tag is None or self._active_tag in row.script_info.meta.tag_list
            if name_match and tag_match:
                row.pack(fill="x", padx=5, pady=3)
            else:
                row.pack_forget()

    # ── Bulk actions ──

    def _on_select_all(self) -> None:
        checked = self._select_all_var.get()
        for row in self._rows.values():
            row.set_checked(checked)

    def _on_check_changed(self) -> None:
        all_checked = all(row.is_checked for row in self._rows.values()) if self._rows else False
        self._select_all_var.set(all_checked)

    def _get_checked_scripts(self) -> list[ScriptInfo]:
        return [row.script_info for row in self._rows.values() if row.is_checked]

    def _on_start_all(self) -> None:
        for si in self._get_checked_scripts():
            self._app.start_script(si)

    def _on_stop_all(self) -> None:
        for si in self._get_checked_scripts():
            self._app.stop_script(si)

    def _on_install_all(self) -> None:
        for si in self._get_checked_scripts():
            self._app.install_requirements(si)

    def _on_import(self) -> None:
        self._app.import_script()
