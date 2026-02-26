"""Single row in the installed scripts scrollable list."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from pylauncher.constants import (
    BG_INPUT,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
    SCRIPT_ROW_HEIGHT,
)
from pylauncher.core.script_manager import ScriptInfo
from pylauncher.ui.widgets.icon_button import IconButton
from pylauncher.utils.assets import load_icon_pair


class ScriptRow(ctk.CTkFrame):
    """A single row representing one installed script.

    Layout:
    [☐] [#01] [Script Name] [tags] [schedule] [Start/Stop] [Schedule] [Install] [Folder] [Delete]
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        script_info: ScriptInfo,
        on_start: Callable[[ScriptInfo], None],
        on_stop: Callable[[ScriptInfo], None],
        on_install: Callable[[ScriptInfo], None],
        on_open_folder: Callable[[ScriptInfo], None],
        on_delete: Callable[[ScriptInfo], None],
        on_schedule: Callable[[ScriptInfo], None],
        is_running: bool = False,
        on_check_changed: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=BG_INPUT, corner_radius=8, height=SCRIPT_ROW_HEIGHT, **kwargs)
        self.pack_propagate(False)

        self._script_info = script_info
        self._is_running = is_running
        self._on_start = on_start
        self._on_stop = on_stop

        # Checkbox for bulk actions
        self._checkbox_var = ctk.BooleanVar(value=False)
        self._checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self._checkbox_var,
            width=20,
            height=20,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=DEEP_PINK,
            hover_color=DEEP_PINK_HOVER,
            border_color=BORDER_COLOR,
            command=on_check_changed,
        )
        self._checkbox.pack(side="left", padx=(10, 0))

        # Load icon pairs
        self._start_icons = load_icon_pair("start")
        self._stop_icons = load_icon_pair("stop")
        self._install_icons = load_icon_pair("install")
        self._folder_icons = load_icon_pair("folder")
        self._delete_icons = load_icon_pair("delete")
        self._timer_icons = load_icon_pair("timer")

        # Row number
        self._number_label = ctk.CTkLabel(
            self,
            text=f"#{script_info.row_number:02d}",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=TEXT_SECONDARY,
            width=35,
        )
        self._number_label.pack(side="left", padx=(8, 5))

        # Script name
        self._name_label = ctk.CTkLabel(
            self,
            text=script_info.meta.script_name,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self._name_label.pack(side="left", fill="x", expand=True, padx=5)

        # Tags display
        tags = script_info.meta.tag_list
        if tags:
            tags_text = " ".join(f"[{t}]" for t in tags[:3])
            self._tags_label = ctk.CTkLabel(
                self,
                text=tags_text,
                font=(FONT_FAMILY, 10),
                text_color=TEXT_SECONDARY,
            )
            self._tags_label.pack(side="left", padx=5)

        # Schedule indicator
        if script_info.meta.has_schedule:
            self._schedule_label = ctk.CTkLabel(
                self,
                text=script_info.meta.schedule_display,
                font=(FONT_FAMILY, 10),
                text_color=DEEP_PINK,
            )
            self._schedule_label.pack(side="left", padx=5)

        # Action buttons (right to left)
        self._delete_btn = IconButton(
            self, self._delete_icons[0], self._delete_icons[1],
            command=lambda: on_delete(script_info),
        )
        self._delete_btn.pack(side="right", padx=5)

        self._folder_btn = IconButton(
            self, self._folder_icons[0], self._folder_icons[1],
            command=lambda: on_open_folder(script_info),
        )
        self._folder_btn.pack(side="right", padx=5)

        self._install_btn = IconButton(
            self, self._install_icons[0], self._install_icons[1],
            command=lambda: on_install(script_info),
        )
        self._install_btn.pack(side="right", padx=5)
        if not script_info.has_requirements:
            self._install_btn.configure(state="disabled")

        self._schedule_btn = IconButton(
            self, self._timer_icons[0], self._timer_icons[1],
            command=lambda: on_schedule(script_info),
        )
        self._schedule_btn.pack(side="right", padx=5)

        self._start_stop_btn = IconButton(
            self,
            self._start_icons[0] if not is_running else self._stop_icons[0],
            self._start_icons[1] if not is_running else self._stop_icons[1],
            command=self._on_start_stop_click,
        )
        self._start_stop_btn.pack(side="right", padx=5)

    def _on_start_stop_click(self) -> None:
        if self._is_running:
            self._on_stop(self._script_info)
        else:
            self._on_start(self._script_info)

    def set_running(self, running: bool) -> None:
        self._is_running = running
        if running:
            self._start_stop_btn.update_icons(self._stop_icons[0], self._stop_icons[1])
        else:
            self._start_stop_btn.update_icons(self._start_icons[0], self._start_icons[1])

    def update_row_number(self, number: int) -> None:
        self._number_label.configure(text=f"#{number:02d}")

    @property
    def is_checked(self) -> bool:
        return self._checkbox_var.get()

    def set_checked(self, checked: bool) -> None:
        self._checkbox_var.set(checked)

    @property
    def folder_key(self) -> str:
        return self._script_info.folder_path.name

    @property
    def script_info(self) -> ScriptInfo:
        return self._script_info
