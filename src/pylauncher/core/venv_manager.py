"""Create virtual environments and install requirements."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional


class VenvManager:
    """Handles venv creation and pip install for script folders."""

    def __init__(self, python_path: str) -> None:
        self._python_path = python_path

    def update_python_path(self, python_path: str) -> None:
        """Update the Python executable path."""
        self._python_path = python_path

    def install_requirements(
        self,
        folder_path: Path,
        on_output: Callable[[str], None],
        on_complete: Callable[[bool], None],
    ) -> threading.Thread:
        """Install requirements.txt into script's venv on a background thread.

        Returns the thread handle.
        """
        thread = threading.Thread(
            target=self._install_worker,
            args=(folder_path, on_output, on_complete),
            daemon=True,
        )
        thread.start()
        return thread

    def has_venv(self, folder_path: Path) -> bool:
        """Check if a venv exists in the folder."""
        return (folder_path / "venv").is_dir()

    def get_venv_python(self, folder_path: Path) -> Optional[Path]:
        """Get the venv's python executable path, or None."""
        if sys.platform == "win32":
            venv_python = folder_path / "venv" / "Scripts" / "python.exe"
        else:
            venv_python = folder_path / "venv" / "bin" / "python"

        return venv_python if venv_python.exists() else None

    def _install_worker(
        self,
        folder_path: Path,
        on_output: Callable[[str], None],
        on_complete: Callable[[bool], None],
    ) -> None:
        """Worker thread that creates venv and installs requirements."""
        req_file = folder_path / "requirements.txt"
        venv_path = folder_path / "venv"

        if not req_file.exists():
            on_output(f"requirements.txt not found in {folder_path.name}")
            on_complete(False)
            return

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            # Step 1: Create venv if it doesn't exist
            if not venv_path.exists():
                on_output(f"Creating virtual environment in {folder_path.name}/venv...")
                result = subprocess.run(
                    [self._python_path, "-m", "venv", str(venv_path)],
                    capture_output=True,
                    text=True,
                    creationflags=creation_flags,
                )
                if result.returncode != 0:
                    on_output(f"Error creating venv: {result.stderr}")
                    on_complete(False)
                    return
                on_output("Virtual environment created.")
            else:
                on_output("Virtual environment already exists.")

            # Step 2: Install requirements
            if sys.platform == "win32":
                pip_python = venv_path / "Scripts" / "python.exe"
            else:
                pip_python = venv_path / "bin" / "python"

            on_output(f"Installing requirements from {req_file.name}...")

            process = subprocess.Popen(
                [str(pip_python), "-u", "-m", "pip", "install", "-r", str(req_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(folder_path),
                creationflags=creation_flags,
            )

            if process.stdout:
                for line_bytes in iter(process.stdout.readline, b""):
                    decoded = line_bytes.decode("utf-8", errors="replace").rstrip()
                    if decoded:
                        on_output(decoded)

            rc = process.wait()
            if rc == 0:
                on_output("Requirements installed successfully.")
                on_complete(True)
            else:
                on_output(f"pip install failed with exit code {rc}")
                on_complete(False)

        except Exception as e:
            on_output(f"Error: {e}")
            on_complete(False)
