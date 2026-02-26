"""Thread helpers for safe UI updates from background threads."""

from __future__ import annotations

import threading
from typing import Any, Callable

import customtkinter as ctk


def run_in_thread(
    target: Callable[..., Any],
    *args: Any,
    daemon: bool = True,
    **kwargs: Any,
) -> threading.Thread:
    """Start a function in a daemon background thread."""
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=daemon)
    thread.start()
    return thread


def schedule_on_main(widget: ctk.CTkBaseClass, callback: Callable[[], None]) -> None:
    """Schedule a callback on the Tkinter main thread.

    Background threads must NEVER directly modify widget state.
    Use this to safely update UI from a background thread.
    """
    try:
        widget.after(0, callback)
    except RuntimeError:
        pass  # Widget was destroyed
