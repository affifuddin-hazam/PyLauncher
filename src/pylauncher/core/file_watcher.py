"""File system watcher for auto-detecting script changes."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent

    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False


class ScriptDirectoryHandler:
    """Watches for changes in the scripts directory with debounce."""

    def __init__(self, on_change: Callable[[], None], debounce_sec: float = 1.0) -> None:
        self._on_change = on_change
        self._debounce_sec = debounce_sec
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _schedule_callback(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_sec, self._on_change)
            self._timer.daemon = True
            self._timer.start()


if _WATCHDOG_AVAILABLE:

    class _WatchdogHandler(FileSystemEventHandler, ScriptDirectoryHandler):
        """Watchdog event handler with debounced callbacks."""

        def __init__(self, on_change: Callable[[], None], debounce_sec: float = 1.0) -> None:
            FileSystemEventHandler.__init__(self)
            ScriptDirectoryHandler.__init__(self, on_change, debounce_sec)

        def on_created(self, event: FileSystemEvent) -> None:
            self._schedule_callback()

        def on_deleted(self, event: FileSystemEvent) -> None:
            self._schedule_callback()

        def on_modified(self, event: FileSystemEvent) -> None:
            if event.src_path.endswith("me.ini"):
                self._schedule_callback()


class ScriptWatcher:
    """Manages a watchdog Observer for the scripts directory.

    Degrades gracefully if watchdog is not installed.
    """

    def __init__(self, scripts_dir: Path, on_change: Callable[[], None]) -> None:
        self._scripts_dir = scripts_dir
        self._on_change = on_change
        self._observer = None

    def start(self) -> None:
        """Start watching. No-op if watchdog is not installed."""
        if not _WATCHDOG_AVAILABLE:
            return
        try:
            handler = _WatchdogHandler(self._on_change)
            self._observer = Observer()
            self._observer.schedule(handler, str(self._scripts_dir), recursive=True)
            self._observer.daemon = True
            self._observer.start()
        except Exception:
            self._observer = None

    def stop(self) -> None:
        """Stop watching."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
