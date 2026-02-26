"""INI file management for settings.ini and per-script me.ini files."""

from __future__ import annotations

import configparser
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    """Application-level settings from settings.ini."""

    python_path: str = ""
    chromedriver_path: str = ""
    googlechrome_path: str = ""


@dataclass
class ScriptMeta:
    """Per-script metadata from me.ini."""

    script_name: str = ""
    main_script: str = ""
    schedule: str = "off"
    tags: str = ""
    folder_path: Path = field(default_factory=Path)

    @property
    def tag_list(self) -> list[str]:
        """Return tags as a cleaned list."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def has_schedule(self) -> bool:
        return bool(self.schedule) and self.schedule.lower() != "off"

    @property
    def schedule_display(self) -> str:
        """Human-readable schedule summary for UI display."""
        if not self.has_schedule:
            return ""
        parts = self.schedule.split("|")
        stype = parts[0].lower()
        if stype == "daily" and len(parts) >= 2:
            return f"Daily {parts[1]}"
        elif stype == "interval" and len(parts) >= 2:
            return f"Every {parts[1]}"
        elif stype == "weekdays" and len(parts) >= 3:
            return f"{parts[2].upper()} {parts[1]}"
        return self.schedule


class SettingsManager:
    """Read/write settings.ini using configparser."""

    def __init__(self, settings_path: Path) -> None:
        self._path = settings_path

    def load(self) -> AppSettings:
        """Load settings from settings.ini, creating a default file if missing."""
        settings = AppSettings()
        if not self._path.exists():
            self.save(settings)
            return settings

        config = configparser.ConfigParser()
        config.read(str(self._path), encoding="utf-8")

        section = "DEFAULT"
        settings.python_path = config.get(section, "PythonPath", fallback="")
        settings.chromedriver_path = config.get(section, "ChromeDriverPath", fallback="")
        settings.googlechrome_path = config.get(section, "GoogleChromePath", fallback="")
        return settings

    def save(self, settings: AppSettings) -> None:
        """Save settings to settings.ini."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "[DEFAULT]",
            f"PythonPath={settings.python_path}",
            f"ChromeDriverPath={settings.chromedriver_path}",
            f"GoogleChromePath={settings.googlechrome_path}",
            "",
        ]
        self._path.write_text("\n".join(lines), encoding="utf-8")


class ScriptMetaManager:
    """Read/write me.ini files.

    me.ini files have NO section header — just raw Key=Value lines.
    We inject a fake [DEFAULT] when reading with configparser,
    and strip it when writing.
    """

    @staticmethod
    def load(folder_path: Path) -> Optional[ScriptMeta]:
        """Load me.ini from a script folder. Returns None if not found."""
        ini_path = folder_path / "me.ini"
        if not ini_path.exists():
            return None

        config = configparser.ConfigParser()
        text = ini_path.read_text(encoding="utf-8")
        config.read_string(f"[DEFAULT]\n{text}")

        return ScriptMeta(
            script_name=config.get("DEFAULT", "ScriptName", fallback=""),
            main_script=config.get("DEFAULT", "MainScript", fallback=""),
            schedule=config.get("DEFAULT", "Schedule", fallback="off"),
            tags=config.get("DEFAULT", "Tags", fallback=""),
            folder_path=folder_path,
        )

    @staticmethod
    def save(folder_path: Path, meta: ScriptMeta) -> None:
        """Save me.ini to a script folder (without section header)."""
        ini_path = folder_path / "me.ini"
        lines = [
            f"ScriptName={meta.script_name}",
            f"MainScript={meta.main_script}",
            f"Schedule={meta.schedule}",
            f"Tags={meta.tags}",
            "",
        ]
        ini_path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def create(folder_path: Path, script_name: str, main_script: str) -> ScriptMeta:
        """Create a new me.ini in the folder and return the ScriptMeta."""
        meta = ScriptMeta(
            script_name=script_name,
            main_script=main_script,
            folder_path=folder_path,
        )
        ScriptMetaManager.save(folder_path, meta)
        return meta
