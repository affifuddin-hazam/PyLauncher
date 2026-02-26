"""Application state persistence (running scripts across sessions)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    """Serializable application state."""

    running_scripts: list[str] = field(default_factory=list)


class StateManager:
    """Read/write state.json for session persistence."""

    def __init__(self, state_path: Path) -> None:
        self._path = state_path

    def load(self) -> AppState:
        """Load state from file. Returns empty state if missing/corrupt."""
        if not self._path.exists():
            return AppState()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return AppState(running_scripts=data.get("running_scripts", []))
        except (json.JSONDecodeError, KeyError, TypeError):
            return AppState()

    def save(self, state: AppState) -> None:
        """Save state to file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"running_scripts": state.running_scripts}, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        """Delete state file."""
        if self._path.exists():
            self._path.unlink()
