"""Resolve asset paths for both development and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image

from pylauncher.constants import ICON_SIZE


def get_base_path() -> Path:
    """Get the base path for the application.

    In PyInstaller, this is sys._MEIPASS. In development, the project root.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # Development: go up from src/pylauncher/utils/ to project root
    return Path(__file__).resolve().parent.parent.parent.parent


def get_assets_dir() -> Path:
    """Get the assets directory path."""
    return get_base_path() / "assets"


def get_scripts_dir() -> Path:
    """Get the scripts directory path.

    Scripts dir is always next to the executable, not inside _MEIPASS.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "scripts"
    return get_base_path() / "scripts"


def get_settings_path() -> Path:
    """Get the settings.ini file path."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "settings.ini"
    return get_base_path() / "settings.ini"


def get_state_path() -> Path:
    """Get the state.json file path for session persistence."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "state.json"
    return get_base_path() / "state.json"


def get_app_icon_path() -> Path:
    """Get (or create) an .ico file for the app window/taskbar icon."""
    ico_path = get_assets_dir() / "img" / "app_icon.ico"
    if not ico_path.exists():
        from PIL import ImageDraw, ImageFont

        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=40, fill="#FF1493")
        try:
            font = ImageFont.truetype("arialbd.ttf", 140)
        except OSError:
            font = ImageFont.load_default()
        draw.text((size // 2, size // 2), "P", fill="white", font=font, anchor="mm")
        ico_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(ico_path, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    return ico_path


def load_icon(name: str, size: tuple[int, int] = ICON_SIZE) -> ctk.CTkImage:
    """Load a single icon as a CTkImage."""
    img_path = get_assets_dir() / "img" / f"{name}.png"
    img = Image.open(img_path)
    return ctk.CTkImage(light_image=img, size=size)


def load_icon_pair(
    name: str, size: tuple[int, int] = ICON_SIZE
) -> tuple[ctk.CTkImage, ctk.CTkImage]:
    """Load default and hover icon variants as CTkImage objects.

    Returns (default_ctk_image, hover_ctk_image).
    """
    img_dir = get_assets_dir() / "img"
    default_img = Image.open(img_dir / f"{name}_icon.png")
    hover_img = Image.open(img_dir / f"{name}_hover_icon.png")

    default_ctk = ctk.CTkImage(light_image=default_img, size=size)
    hover_ctk = ctk.CTkImage(light_image=hover_img, size=size)

    return default_ctk, hover_ctk
