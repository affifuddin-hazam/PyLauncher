"""CLI dialog for running manual Python/pip commands."""

from __future__ import annotations

import subprocess
import sys
import threading

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
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_LABEL,
    FONT_SIZE_TITLE,
    FONT_TITLE_FAMILY,
    INPUT_CORNER_RADIUS,
    BUTTON_CORNER_RADIUS,
    CLI_WINDOW_WIDTH,
    CLI_WINDOW_HEIGHT,
)
from pylauncher.ui.widgets.output_textbox import OutputTextbox


class CLIDialog(ctk.CTkToplevel):
    """Command line tool with Manual and Install Package modes."""

    def __init__(self, master: ctk.CTk, python_path: str) -> None:
        super().__init__(master)
        self._python_path = python_path
        self._mode = "manual"

        self.title("Command Line Tool")
        self.geometry(f"{CLI_WINDOW_WIDTH}x{CLI_WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()

        self.transient(master)
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - CLI_WINDOW_WIDTH) // 2
        y = master.winfo_y() + (master.winfo_height() - CLI_WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        # Escape to close
        self.bind("<Escape>", lambda e: self.destroy())

        ctk.CTkLabel(
            self, text="Command line tool",
            font=(FONT_TITLE_FAMILY, FONT_SIZE_TITLE), text_color=TEXT_PRIMARY,
        ).pack(padx=25, pady=(20, 15), anchor="w")

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        mode_frame = ctk.CTkFrame(card, fg_color=BG_CARD)
        mode_frame.pack(fill="x", padx=20, pady=(15, 10))

        self._manual_btn = ctk.CTkButton(
            mode_frame, text="Manual mode",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=10,
            width=140, height=34, command=self._set_manual,
        )
        self._manual_btn.pack(side="left", padx=(0, 10))

        self._install_btn = ctk.CTkButton(
            mode_frame, text="Install package",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_CARD, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, border_color=BORDER_COLOR, border_width=1,
            corner_radius=10, width=140, height=34, command=self._set_install,
        )
        self._install_btn.pack(side="left")

        ctk.CTkLabel(
            card, text="Command",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(padx=20, anchor="w")

        cmd_frame = ctk.CTkFrame(card, fg_color=BG_CARD)
        cmd_frame.pack(fill="x", padx=20, pady=(0, 10))

        self._command_entry = ctk.CTkEntry(
            cmd_frame, font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            corner_radius=INPUT_CORNER_RADIUS,
            border_color=BORDER_COLOR, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
        )
        self._command_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._command_entry.bind("<Return>", lambda e: self._execute())

        self._execute_btn = ctk.CTkButton(
            cmd_frame, text="▶", font=("Segoe UI", 14),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=INPUT_CORNER_RADIUS,
            width=40, height=30, command=self._execute,
        )
        self._execute_btn.pack(side="right")

        ctk.CTkLabel(
            card, text="Output",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(padx=20, anchor="w")

        self._output = OutputTextbox(card, corner_radius=15)
        self._output.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _set_manual(self) -> None:
        self._mode = "manual"
        self._manual_btn.configure(fg_color=DEEP_PINK, text_color=TEXT_PRIMARY, border_width=0)
        self._install_btn.configure(
            fg_color=BG_CARD, text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER_COLOR
        )

    def _set_install(self) -> None:
        self._mode = "install"
        self._install_btn.configure(fg_color=DEEP_PINK, text_color=TEXT_PRIMARY, border_width=0)
        self._manual_btn.configure(
            fg_color=BG_CARD, text_color=TEXT_SECONDARY, border_width=1, border_color=BORDER_COLOR
        )

    def _execute(self) -> None:
        cmd_text = self._command_entry.get().strip()
        if not cmd_text or not self._python_path:
            if not self._python_path:
                self._output.append_line("Error: Python path not set.")
            return
        if self._mode == "manual":
            command = f"{self._python_path} {cmd_text}"
        else:
            command = f"{self._python_path} -m pip install {cmd_text}"
        self._output.append_line(f"> {command}")
        self._execute_btn.configure(state="disabled")
        thread = threading.Thread(target=self._run_command, args=(command,), daemon=True)
        thread.start()

    def _run_command(self, command: str) -> None:
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                shell=True, creationflags=creation_flags,
            )
            if process.stdout:
                for line_bytes in iter(process.stdout.readline, b""):
                    decoded = line_bytes.decode("utf-8", errors="replace").rstrip()
                    if decoded:
                        self.after(0, lambda t=decoded: self._output.append_line(t))
            process.wait()
            self.after(0, lambda: self._output.append_line("--- Done ---"))
        except Exception as e:
            self.after(0, lambda: self._output.append_line(f"Error: {e}"))
        finally:
            self.after(0, lambda: self._execute_btn.configure(state="normal"))
