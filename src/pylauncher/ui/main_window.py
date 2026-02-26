"""Main application window content with tabbed interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from pylauncher.constants import (
    BG_DARK,
    BG_CARD,
    BG_SURFACE,
    BG_HOVER,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    TEXT_SECONDARY,
    CARD_CORNER_RADIUS,
)
from pylauncher.ui.tabs.installed_tab import InstalledTab
from pylauncher.ui.tabs.running_tab import RunningTab
from pylauncher.ui.tabs.logs_tab import LogsTab

if TYPE_CHECKING:
    from pylauncher.app import PyLauncherApp


class MainWindow(ctk.CTkFrame):
    """Main content area below the title bar."""

    def __init__(self, master: ctk.CTkBaseClass, app: "PyLauncherApp") -> None:
        super().__init__(master, fg_color=BG_DARK)
        self._app = app

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_CORNER_RADIUS)
        card.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self._tabview = ctk.CTkTabview(
            card, fg_color=BG_CARD,
            segmented_button_fg_color=BG_SURFACE,
            segmented_button_selected_color=DEEP_PINK,
            segmented_button_selected_hover_color=DEEP_PINK_HOVER,
            segmented_button_unselected_color=BG_SURFACE,
            segmented_button_unselected_hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, corner_radius=15,
        )
        self._tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self._tabview.add("Installed")
        self._tabview.add("Running")
        self._tabview.add("Logs")

        self.installed_tab = InstalledTab(self._tabview.tab("Installed"), app)
        self.installed_tab.pack(fill="both", expand=True)

        self.running_tab = RunningTab(self._tabview.tab("Running"), app)
        self.running_tab.pack(fill="both", expand=True)

        self.logs_tab = LogsTab(self._tabview.tab("Logs"))
        self.logs_tab.pack(fill="both", expand=True)

    def set_tab(self, name: str) -> None:
        """Programmatically switch to a named tab."""
        self._tabview.set(name)
