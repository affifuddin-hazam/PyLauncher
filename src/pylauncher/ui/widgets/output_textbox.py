"""Read-only textbox with search overlay for displaying process output."""

from __future__ import annotations

import customtkinter as ctk

from pylauncher.constants import (
    FONT_MONO,
    FONT_MONO_SIZE,
    FONT_FAMILY,
    FONT_SIZE_SMALL,
    BG_INPUT,
    BG_SURFACE,
    BG_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_CURRENT_COLOR,
)


class OutputTextbox(ctk.CTkTextbox):
    """A CTkTextbox configured for read-only log/output display.

    Features:
    - Monospace font, auto-scroll, max 5000 lines
    - Ctrl+F search overlay with highlight and navigation
    - get_text() for export
    """

    MAX_LINES = 5000

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        defaults = {
            "font": (FONT_MONO, FONT_MONO_SIZE),
            "state": "disabled",
            "wrap": "word",
            "fg_color": BG_INPUT,
            "text_color": TEXT_PRIMARY,
            "border_color": BORDER_COLOR,
            "border_width": 1,
            "corner_radius": 10,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

        # Search state
        self._search_frame: ctk.CTkFrame | None = None
        self._search_entry: ctk.CTkEntry | None = None
        self._match_label: ctk.CTkLabel | None = None
        self._search_matches: list[str] = []
        self._current_match_idx: int = -1

        # Configure highlight tags on the underlying Text widget
        self._textbox.tag_config("search_hl", background=HIGHLIGHT_COLOR, foreground="black")
        self._textbox.tag_config("search_cur", background=HIGHLIGHT_CURRENT_COLOR, foreground="black")

        # Bind Ctrl+F
        self.bind("<Control-f>", self._toggle_search)
        self._textbox.bind("<Control-f>", self._toggle_search)

    def append_line(self, text: str) -> None:
        self.configure(state="normal")
        self.insert("end", text + "\n")
        line_count = int(self.index("end-1c").split(".")[0])
        if line_count > self.MAX_LINES:
            self.delete("1.0", f"{line_count - self.MAX_LINES}.0")
        self.configure(state="disabled")
        self.see("end")

    def clear(self) -> None:
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")

    def get_text(self) -> str:
        """Return all text content."""
        return self._textbox.get("1.0", "end-1c")

    # ── Search overlay ──

    def _toggle_search(self, event=None) -> None:
        if self._search_frame and self._search_frame.winfo_viewable():
            self._close_search()
        else:
            self._open_search()
        return "break"

    def _open_search(self) -> None:
        self._search_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=5)
        self._search_frame.place(relx=1.0, y=5, anchor="ne", x=-10)

        self._search_entry = ctk.CTkEntry(
            self._search_frame,
            width=200,
            height=28,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            border_color=BORDER_COLOR,
            placeholder_text="Search...",
        )
        self._search_entry.pack(side="left", padx=(5, 2), pady=4)
        self._search_entry.bind("<KeyRelease>", self._do_search)
        self._search_entry.bind("<Return>", lambda e: self._next_match())
        self._search_entry.bind("<Escape>", lambda e: self._close_search())

        prev_btn = ctk.CTkButton(
            self._search_frame, text="▲", width=28, height=28,
            font=(FONT_FAMILY, 10), fg_color=BG_HOVER, hover_color=DEEP_PINK,
            text_color=TEXT_PRIMARY, corner_radius=4, command=self._prev_match,
        )
        prev_btn.pack(side="left", padx=1, pady=4)

        next_btn = ctk.CTkButton(
            self._search_frame, text="▼", width=28, height=28,
            font=(FONT_FAMILY, 10), fg_color=BG_HOVER, hover_color=DEEP_PINK,
            text_color=TEXT_PRIMARY, corner_radius=4, command=self._next_match,
        )
        next_btn.pack(side="left", padx=1, pady=4)

        self._match_label = ctk.CTkLabel(
            self._search_frame, text="0/0", width=50,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), text_color=TEXT_SECONDARY,
        )
        self._match_label.pack(side="left", padx=(2, 2), pady=4)

        close_btn = ctk.CTkButton(
            self._search_frame, text="✕", width=28, height=28,
            font=(FONT_FAMILY, 10), fg_color=BG_HOVER, hover_color="#5c1a2a",
            text_color=TEXT_PRIMARY, corner_radius=4, command=self._close_search,
        )
        close_btn.pack(side="left", padx=(1, 5), pady=4)

        self._search_entry.focus_set()

    def _close_search(self) -> None:
        self._textbox.tag_remove("search_hl", "1.0", "end")
        self._textbox.tag_remove("search_cur", "1.0", "end")
        self._search_matches.clear()
        self._current_match_idx = -1
        if self._search_frame:
            self._search_frame.destroy()
            self._search_frame = None

    def _do_search(self, event=None) -> None:
        self._textbox.tag_remove("search_hl", "1.0", "end")
        self._textbox.tag_remove("search_cur", "1.0", "end")
        self._search_matches.clear()
        self._current_match_idx = -1

        query = self._search_entry.get() if self._search_entry else ""
        if not query:
            if self._match_label:
                self._match_label.configure(text="0/0")
            return

        start = "1.0"
        while True:
            pos = self._textbox.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self._textbox.tag_add("search_hl", pos, end)
            self._search_matches.append(pos)
            start = end

        total = len(self._search_matches)
        if total > 0:
            self._current_match_idx = 0
            self._highlight_current()
        if self._match_label:
            self._match_label.configure(text=f"0/{total}" if total == 0 else f"1/{total}")

    def _highlight_current(self) -> None:
        self._textbox.tag_remove("search_cur", "1.0", "end")
        if not self._search_matches or self._current_match_idx < 0:
            return
        pos = self._search_matches[self._current_match_idx]
        query = self._search_entry.get() if self._search_entry else ""
        end = f"{pos}+{len(query)}c"
        self._textbox.tag_add("search_cur", pos, end)
        self._textbox.see(pos)
        if self._match_label:
            self._match_label.configure(
                text=f"{self._current_match_idx + 1}/{len(self._search_matches)}"
            )

    def _next_match(self) -> None:
        if self._search_matches:
            self._current_match_idx = (self._current_match_idx + 1) % len(self._search_matches)
            self._highlight_current()

    def _prev_match(self) -> None:
        if self._search_matches:
            self._current_match_idx = (self._current_match_idx - 1) % len(self._search_matches)
            self._highlight_current()
