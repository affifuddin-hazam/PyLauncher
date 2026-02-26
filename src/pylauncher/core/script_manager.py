"""Discover, import, and delete script folders."""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pylauncher.core.config import ScriptMeta, ScriptMetaManager


@dataclass
class ScriptInfo:
    """Full representation of a discovered script."""

    meta: ScriptMeta
    folder_path: Path
    has_requirements: bool
    has_venv: bool
    row_number: int  # 1-based index for display


class ScriptManager:
    """Manages the scripts/ directory."""

    def __init__(self, scripts_dir: Path) -> None:
        self._scripts_dir = scripts_dir
        self._scripts_dir.mkdir(parents=True, exist_ok=True)

    @property
    def scripts_dir(self) -> Path:
        return self._scripts_dir

    def discover_all(self) -> list[ScriptInfo]:
        """Scan scripts/ directory and return all valid script entries."""
        scripts: list[ScriptInfo] = []
        if not self._scripts_dir.exists():
            return scripts

        folders = sorted(
            [f for f in self._scripts_dir.iterdir() if f.is_dir()],
            key=lambda f: f.name.lower(),
        )

        row_num = 0
        for folder in folders:
            meta = ScriptMetaManager.load(folder)
            if meta is None:
                continue

            # Auto-detect main script if not set
            if not meta.main_script:
                py_files = list(folder.glob("*.py"))
                if py_files:
                    meta.main_script = py_files[0].name

            row_num += 1
            scripts.append(
                ScriptInfo(
                    meta=meta,
                    folder_path=folder,
                    has_requirements=(folder / "requirements.txt").exists(),
                    has_venv=(folder / "venv").is_dir(),
                    row_number=row_num,
                )
            )

        return scripts

    def import_script(
        self,
        source_folder: Path,
        script_name: str,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> ScriptInfo:
        """Copy a folder into scripts/, create me.ini, return ScriptInfo.

        Steps:
        1. Copy source folder contents to scripts/{folder_name}/
        2. Auto-detect the main .py file
        3. Create me.ini with provided name
        """
        dest_folder = self._scripts_dir / source_folder.name

        if on_progress:
            on_progress(f"Copying {source_folder.name} to scripts/...")

        # Copy the folder
        shutil.copytree(
            source_folder,
            dest_folder,
            ignore=shutil.ignore_patterns("__pycache__", ".venv", "venv", "*.pyc"),
        )

        # Detect main script
        py_files = list(dest_folder.glob("*.py"))
        main_script = py_files[0].name if py_files else ""

        if on_progress:
            on_progress(f"Creating me.ini for '{script_name}'...")

        # Create me.ini
        meta = ScriptMetaManager.create(dest_folder, script_name, main_script)

        if on_progress:
            on_progress(f"Import complete: {script_name}")

        return ScriptInfo(
            meta=meta,
            folder_path=dest_folder,
            has_requirements=(dest_folder / "requirements.txt").exists(),
            has_venv=False,
            row_number=0,  # Will be reassigned on refresh
        )

    def delete_script(self, script: ScriptInfo) -> None:
        """Delete a script folder entirely, with retries for OneDrive locking."""
        folder = script.folder_path
        if not folder.exists():
            return

        # Remove contents first
        shutil.rmtree(folder, onerror=self._on_rm_error)

        # OneDrive may keep the empty directory locked briefly — retry removal
        for _ in range(5):
            if not folder.exists():
                return
            try:
                folder.rmdir()
                return
            except OSError:
                time.sleep(0.5)

    @staticmethod
    def _on_rm_error(func, path, _exc_info) -> None:
        """Handle rmtree errors — clear read-only flags and retry (OneDrive compat)."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    @staticmethod
    def open_folder(script: ScriptInfo) -> None:
        """Open the script folder in the system file explorer."""
        folder = str(script.folder_path)
        system = platform.system()
        if system == "Windows":
            os.startfile(folder)
        elif system == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    @staticmethod
    def auto_generate_requirements(
        folder_path: Path,
        python_path: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Run pipreqs to auto-generate requirements.txt in a background thread."""

        def _run() -> None:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            try:
                if on_output:
                    on_output(f"Running pipreqs on {folder_path.name}...")
                result = subprocess.run(
                    [python_path, "-m", "pipreqs.pipreqs", str(folder_path), "--force"],
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags,
                )
                if result.returncode == 0:
                    if on_output:
                        on_output("requirements.txt generated successfully.")
                    if on_complete:
                        on_complete(True)
                else:
                    if on_output:
                        on_output(f"pipreqs error: {result.stderr.strip()}")
                    if on_complete:
                        on_complete(False)
            except FileNotFoundError:
                if on_output:
                    on_output("pipreqs not installed. Install with: pip install pipreqs")
                if on_complete:
                    on_complete(False)
            except Exception as e:
                if on_output:
                    on_output(f"Error: {e}")
                if on_complete:
                    on_complete(False)

        threading.Thread(target=_run, daemon=True).start()
