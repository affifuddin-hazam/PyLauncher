"""System tray icon and menu management."""

from __future__ import annotations

import threading
from typing import Callable

try:
    import pystray
    from pystray import MenuItem, Menu
    from PIL import Image, ImageDraw

    _PYSTRAY_AVAILABLE = True
except ImportError:
    _PYSTRAY_AVAILABLE = False


def _create_default_icon() -> "Image.Image":
    """Create a simple DeepPink circle icon for the tray."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#FF1493")
    draw.text((size // 2 - 8, size // 2 - 10), "P", fill="white")
    return img


class TrayManager:
    """System tray icon with show/hide and running scripts menu.

    Degrades gracefully if pystray is not installed.
    """

    def __init__(
        self,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
        get_running_names: Callable[[], list[str]],
        icon_path: str | None = None,
    ) -> None:
        self._on_show = on_show
        self._on_exit = on_exit
        self._get_running_names = get_running_names
        self._icon_path = icon_path
        self._icon: "pystray.Icon | None" = None

    @property
    def available(self) -> bool:
        return _PYSTRAY_AVAILABLE

    def start(self) -> None:
        """Start the tray icon. No-op if pystray unavailable."""
        if not _PYSTRAY_AVAILABLE:
            return

        try:
            if self._icon_path:
                image = Image.open(self._icon_path)
            else:
                image = _create_default_icon()
        except Exception:
            image = _create_default_icon()

        self._icon = pystray.Icon(
            "PyLauncher",
            image,
            "PyLauncher",
            menu=self._build_menu(),
        )
        thread = threading.Thread(target=self._icon.run, daemon=True)
        thread.start()

    def _build_menu(self) -> "Menu":
        running = self._get_running_names()
        running_items = (
            [MenuItem(name, None, enabled=False) for name in running]
            if running
            else [MenuItem("(none)", None, enabled=False)]
        )

        return Menu(
            MenuItem("Show PyLauncher", lambda: self._on_show(), default=True),
            Menu.SEPARATOR,
            MenuItem("Running Scripts", Menu(*running_items)),
            Menu.SEPARATOR,
            MenuItem("Exit", lambda: self._on_exit()),
        )

    def update_menu(self) -> None:
        """Refresh the tray menu (e.g., after scripts start/stop)."""
        if self._icon:
            self._icon.menu = self._build_menu()
            try:
                self._icon.update_menu()
            except Exception:
                pass

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
