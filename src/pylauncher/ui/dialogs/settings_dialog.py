"""Settings dialog with path validation."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from pylauncher.constants import (
    BG_DARK,
    BG_CARD,
    BG_INPUT,
    BG_HOVER,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
    WARNING_COLOR,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_LABEL,
    FONT_SIZE_SMALL,
    FONT_SIZE_TITLE,
    FONT_TITLE_FAMILY,
    BUTTON_CORNER_RADIUS,
    INPUT_CORNER_RADIUS,
    SETTINGS_WINDOW_WIDTH,
    SETTINGS_WINDOW_HEIGHT,
)
from pylauncher.core.config import AppSettings, SettingsManager


class SettingsDialog(ctk.CTkToplevel):
    """Settings form with path validation."""

    def __init__(
        self,
        master: ctk.CTk,
        settings_manager: SettingsManager,
        current_settings: AppSettings,
        on_save: callable,
    ) -> None:
        super().__init__(master)
        self._settings_manager = settings_manager
        self._on_save = on_save
        self._path_entries: list[tuple[str, ctk.CTkEntry, ctk.CTkLabel]] = []

        self.title("Settings")
        self.geometry(f"{SETTINGS_WINDOW_WIDTH}x{SETTINGS_WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()

        self.transient(master)
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - SETTINGS_WINDOW_WIDTH) // 2
        y = master.winfo_y() + (master.winfo_height() - SETTINGS_WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        # Escape to close
        self.bind("<Escape>", lambda e: self.destroy())

        ctk.CTkLabel(
            self, text="Settings",
            font=(FONT_TITLE_FAMILY, FONT_SIZE_TITLE), text_color=TEXT_PRIMARY,
        ).pack(padx=25, pady=(20, 15), anchor="w")

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._python_entry = self._create_path_row(
            card, "Python path", current_settings.python_path, "Python Executable|python.exe", 0
        )
        self._chrome_driver_entry = self._create_path_row(
            card, "ChromeDriver path", current_settings.chromedriver_path, "ChromeDriver|chromedriver.exe", 1
        )
        self._chrome_entry = self._create_path_row(
            card, "Google Chrome path", current_settings.googlechrome_path, "Google Chrome|chrome.exe", 2
        )

        ctk.CTkButton(
            card, text="Save",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=150, height=40, command=self._save,
        ).grid(row=9, column=0, columnspan=3, pady=(10, 20), sticky="e", padx=20)

    def _create_path_row(
        self, parent: ctk.CTkFrame, label: str, value: str, file_filter: str, row: int
    ) -> ctk.CTkEntry:
        label_row = row * 3
        entry_row = row * 3 + 1
        warn_row = row * 3 + 2

        ctk.CTkLabel(
            parent, text=label,
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).grid(row=label_row, column=0, padx=(20, 5), pady=(15, 0), sticky="w", columnspan=3)

        entry = ctk.CTkEntry(
            parent, font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            corner_radius=INPUT_CORNER_RADIUS,
            border_color=BORDER_COLOR, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
        )
        entry.grid(row=entry_row, column=0, padx=(20, 5), pady=(5, 0), sticky="ew", columnspan=2)
        entry.insert(0, value)

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)

        browse_btn = ctk.CTkButton(
            parent, text="Browse",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_HOVER, hover_color=DEEP_PINK,
            text_color=TEXT_PRIMARY, corner_radius=INPUT_CORNER_RADIUS,
            width=70, height=30,
            command=lambda: self._browse(entry, file_filter),
        )
        browse_btn.grid(row=entry_row, column=2, padx=(5, 20), pady=(5, 0))

        # Warning label (hidden by default)
        warning_label = ctk.CTkLabel(
            parent, text="",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), text_color=WARNING_COLOR, anchor="w",
        )
        warning_label.grid(row=warn_row, column=0, padx=(20, 5), pady=(2, 0), sticky="w", columnspan=3)

        self._path_entries.append((label, entry, warning_label))
        return entry

    def _browse(self, entry: ctk.CTkEntry, file_filter: str) -> None:
        parts = file_filter.split("|")
        filetypes = [(parts[0], parts[1])] if len(parts) == 2 else [("All files", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _validate_paths(self) -> list[str]:
        warnings = []
        for label_text, entry, warning_label in self._path_entries:
            path_str = entry.get().strip()
            if path_str and not Path(path_str).exists():
                entry.configure(border_color=WARNING_COLOR)
                warning_label.configure(text=f"Path not found")
                warnings.append(f"{label_text}: path not found")
            else:
                entry.configure(border_color=BORDER_COLOR)
                warning_label.configure(text="")
        return warnings

    def _save(self) -> None:
        warnings = self._validate_paths()
        if warnings:
            result = messagebox.askyesno(
                "Invalid Paths",
                "Some paths don't exist:\n\n" + "\n".join(f"• {w}" for w in warnings) +
                "\n\nSave anyway?",
                parent=self,
            )
            if not result:
                return

        settings = AppSettings(
            python_path=self._python_entry.get(),
            chromedriver_path=self._chrome_driver_entry.get(),
            googlechrome_path=self._chrome_entry.get(),
        )
        self._settings_manager.save(settings)
        self._on_save(settings)
        messagebox.showinfo("Success", "Settings saved successfully!", parent=self)
        self.destroy()
