"""Background scheduler that auto-starts scripts on a cron-style schedule."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Optional


class ScheduleType(Enum):
    OFF = auto()
    DAILY = auto()
    INTERVAL = auto()
    WEEKDAYS = auto()


_DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _parse_time(s: str) -> tuple[int, int]:
    """Parse 'HH:MM' -> (hour, minute)."""
    h_str, m_str = s.strip().split(":")
    return int(h_str), int(m_str)


def _parse_interval(s: str) -> int:
    """Parse '30m' or '2h' -> seconds."""
    s = s.strip().lower()
    if s.endswith("m"):
        return int(s[:-1]) * 60
    elif s.endswith("h"):
        return int(s[:-1]) * 3600
    return int(s) * 60  # Default to minutes


def _parse_weekdays(s: str) -> list[int]:
    """Parse 'mon,wed,fri' -> [0, 2, 4]."""
    result = []
    for day_str in s.lower().split(","):
        day_str = day_str.strip()
        if day_str in _DAY_MAP:
            result.append(_DAY_MAP[day_str])
    return sorted(set(result))


@dataclass
class ScheduleEntry:
    """Parsed schedule for one script."""

    schedule_type: ScheduleType = ScheduleType.OFF
    time_of_day: Optional[tuple[int, int]] = None
    interval_seconds: int = 0
    weekdays: list[int] = field(default_factory=list)

    @staticmethod
    def parse(raw: str) -> ScheduleEntry:
        """Parse a schedule string like 'daily|09:30' into a ScheduleEntry."""
        if not raw or raw.lower() == "off":
            return ScheduleEntry()
        parts = raw.split("|")
        stype = parts[0].lower().strip()
        try:
            if stype == "daily" and len(parts) >= 2:
                h, m = _parse_time(parts[1])
                return ScheduleEntry(schedule_type=ScheduleType.DAILY, time_of_day=(h, m))
            elif stype == "interval" and len(parts) >= 2:
                seconds = _parse_interval(parts[1])
                return ScheduleEntry(schedule_type=ScheduleType.INTERVAL, interval_seconds=seconds)
            elif stype == "weekdays" and len(parts) >= 3:
                h, m = _parse_time(parts[1])
                days = _parse_weekdays(parts[2])
                return ScheduleEntry(
                    schedule_type=ScheduleType.WEEKDAYS, time_of_day=(h, m), weekdays=days
                )
        except (ValueError, IndexError):
            pass
        return ScheduleEntry()


class Scheduler:
    """Background scheduler that checks script schedules and triggers starts."""

    POLL_INTERVAL = 30  # seconds between checks

    def __init__(
        self,
        on_trigger: Callable[[str], None],
        is_running: Callable[[str], bool],
        on_log: Callable[[str], None],
    ) -> None:
        self._on_trigger = on_trigger
        self._is_running = is_running
        self._on_log = on_log

        self._schedules: dict[str, ScheduleEntry] = {}
        self._last_fired: dict[str, datetime] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def update_schedule(self, folder_key: str, raw_schedule: str) -> None:
        entry = ScheduleEntry.parse(raw_schedule)
        with self._lock:
            if entry.schedule_type == ScheduleType.OFF:
                self._schedules.pop(folder_key, None)
                self._last_fired.pop(folder_key, None)
            else:
                self._schedules[folder_key] = entry

    def remove_schedule(self, folder_key: str) -> None:
        with self._lock:
            self._schedules.pop(folder_key, None)
            self._last_fired.pop(folder_key, None)

    def load_all(self, schedule_map: dict[str, str]) -> None:
        with self._lock:
            self._schedules.clear()
            self._last_fired.clear()
        for folder_key, raw in schedule_map.items():
            self.update_schedule(folder_key, raw)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _poll_loop(self) -> None:
        while self._running:
            try:
                self._check_all()
            except Exception as e:
                try:
                    self._on_log(f"Scheduler error: {e}")
                except Exception:
                    pass
            # Sleep in small increments so stop() is responsive
            for _ in range(self.POLL_INTERVAL * 2):
                if not self._running:
                    return
                time.sleep(0.5)

    def _check_all(self) -> None:
        now = datetime.now()
        with self._lock:
            entries = dict(self._schedules)

        for folder_key, entry in entries.items():
            if self._should_fire(folder_key, entry, now):
                if not self._is_running(folder_key):
                    with self._lock:
                        self._last_fired[folder_key] = now
                    self._on_trigger(folder_key)

    def _should_fire(self, folder_key: str, entry: ScheduleEntry, now: datetime) -> bool:
        with self._lock:
            last = self._last_fired.get(folder_key)

        if entry.schedule_type == ScheduleType.DAILY:
            return self._check_time_trigger(entry.time_of_day, now, last)

        elif entry.schedule_type == ScheduleType.INTERVAL:
            if last is None:
                return True
            elapsed = (now - last).total_seconds()
            return elapsed >= entry.interval_seconds

        elif entry.schedule_type == ScheduleType.WEEKDAYS:
            if now.weekday() not in entry.weekdays:
                return False
            return self._check_time_trigger(entry.time_of_day, now, last)

        return False

    @staticmethod
    def _check_time_trigger(
        time_of_day: Optional[tuple[int, int]],
        now: datetime,
        last_fired: Optional[datetime],
    ) -> bool:
        if time_of_day is None:
            return False
        target_h, target_m = time_of_day
        if now.hour != target_h or now.minute != target_m:
            return False
        if last_fired is None:
            return True
        return not (
            last_fired.year == now.year
            and last_fired.month == now.month
            and last_fired.day == now.day
            and last_fired.hour == now.hour
            and last_fired.minute == now.minute
        )
