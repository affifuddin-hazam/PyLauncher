"""Subprocess lifecycle management for running Python scripts."""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional


class ProcessState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERRORED = auto()


@dataclass
class RunningProcess:
    """Tracks a single running script process."""

    script_name: str
    folder_path: Path
    process: Optional[subprocess.Popen] = None
    state: ProcessState = ProcessState.IDLE
    thread: Optional[threading.Thread] = None


class ProcessHandler:
    """Manages all running script processes."""

    def __init__(self, python_path: str) -> None:
        self._python_path = python_path
        self._processes: dict[str, RunningProcess] = {}
        self._lock = threading.Lock()

    def update_python_path(self, python_path: str) -> None:
        """Update the Python executable path."""
        self._python_path = python_path

    def start_script(
        self,
        folder_path: Path,
        main_script: str,
        script_name: str,
        on_output: Callable[[str, str], None],
        on_exit: Callable[[str, int], None],
    ) -> str:
        """Launch a script in a subprocess.

        Args:
            folder_path: Script folder (used as working directory)
            main_script: The .py filename to run
            script_name: Display name for tracking
            on_output: Called with (folder_key, line) for each output line
            on_exit: Called with (folder_key, return_code) when process exits

        Returns:
            folder_key for tracking this process
        """
        folder_key = folder_path.name

        with self._lock:
            if folder_key in self._processes:
                existing = self._processes[folder_key]
                if existing.state == ProcessState.RUNNING:
                    return folder_key  # Already running

        # Determine python executable — prefer venv if available
        python_exe = self._get_python_exe(folder_path)
        script_path = folder_path / main_script

        # Build the subprocess
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            [str(python_exe), "-u", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(folder_path),
            creationflags=creation_flags,
        )

        rp = RunningProcess(
            script_name=script_name,
            folder_path=folder_path,
            process=process,
            state=ProcessState.RUNNING,
        )

        # Start reader thread
        reader = threading.Thread(
            target=self._reader_thread,
            args=(rp, folder_key, on_output, on_exit),
            daemon=True,
        )
        rp.thread = reader

        with self._lock:
            self._processes[folder_key] = rp

        reader.start()
        return folder_key

    def stop_script(self, folder_key: str) -> None:
        """Kill a running script process."""
        with self._lock:
            rp = self._processes.get(folder_key)
            if rp is None or rp.state != ProcessState.RUNNING:
                return
            rp.state = ProcessState.STOPPING

        proc = rp.process
        if proc is None:
            return

        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        except OSError:
            pass  # Process already dead

        with self._lock:
            rp.state = ProcessState.STOPPED

    def is_running(self, folder_key: str) -> bool:
        """Check if a script is currently running."""
        with self._lock:
            rp = self._processes.get(folder_key)
            return rp is not None and rp.state == ProcessState.RUNNING

    def get_running_keys(self) -> list[str]:
        """Get all currently running script folder keys."""
        with self._lock:
            return [
                key
                for key, rp in self._processes.items()
                if rp.state == ProcessState.RUNNING
            ]

    def get_running_names(self) -> list[str]:
        """Get display names of all currently running scripts."""
        with self._lock:
            return [
                rp.script_name
                for rp in self._processes.values()
                if rp.state == ProcessState.RUNNING
            ]

    def stop_all(self) -> None:
        """Kill all running processes."""
        keys = self.get_running_keys()
        for key in keys:
            self.stop_script(key)

    def shutdown(self) -> None:
        """Stop all processes and clean up. Called on application exit."""
        self.stop_all()

    def _get_python_exe(self, folder_path: Path) -> str:
        """Get the Python executable path, preferring venv if it exists."""
        if sys.platform == "win32":
            venv_python = folder_path / "venv" / "Scripts" / "python.exe"
        else:
            venv_python = folder_path / "venv" / "bin" / "python"

        if venv_python.exists():
            return str(venv_python)
        return self._python_path

    def _reader_thread(
        self,
        rp: RunningProcess,
        folder_key: str,
        on_output: Callable[[str, str], None],
        on_exit: Callable[[str, int], None],
    ) -> None:
        """Background thread that reads stdout line-by-line."""
        proc = rp.process
        if proc is None or proc.stdout is None:
            return

        try:
            for line_bytes in iter(proc.stdout.readline, b""):
                if rp.state == ProcessState.STOPPING:
                    break
                decoded = line_bytes.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    on_output(folder_key, decoded)
        except (OSError, ValueError):
            pass  # Stream closed

        rc = proc.wait()

        with self._lock:
            if rp.state != ProcessState.STOPPING:
                rp.state = ProcessState.STOPPED

        on_exit(folder_key, rc)
