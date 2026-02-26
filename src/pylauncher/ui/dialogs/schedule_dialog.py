"""Schedule configuration dialog for a single script."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from pylauncher.constants import (
    BG_DARK,
    BG_CARD,
    BG_INPUT,
    BG_HOVER,
    DEEP_PINK,
    DEEP_PINK_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
    FONT_FAMILY,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_SMALL,
    FONT_SIZE_LABEL,
    FONT_SIZE_TITLE,
    FONT_TITLE_FAMILY,
    BUTTON_CORNER_RADIUS,
    INPUT_CORNER_RADIUS,
    SCHEDULE_DIALOG_WIDTH,
    SCHEDULE_DIALOG_HEIGHT,
)

_TYPE_OPTIONS = ["Off", "Daily", "Interval", "Weekdays"]
_UNIT_OPTIONS = ["Minutes", "Hours"]
_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class ScheduleDialog(ctk.CTkToplevel):
    """Configure schedule for a single script."""

    def __init__(
        self,
        master: ctk.CTk,
        script_name: str,
        current_schedule: str,
        on_save: callable,
    ) -> None:
        super().__init__(master)
        self._on_save = on_save

        self.title("Schedule")
        self.geometry(f"{SCHEDULE_DIALOG_WIDTH}x{SCHEDULE_DIALOG_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()

        self.transient(master)
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - SCHEDULE_DIALOG_WIDTH) // 2
        y = master.winfo_y() + (master.winfo_height() - SCHEDULE_DIALOG_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())

        ctk.CTkLabel(
            self, text=f"Schedule: {script_name}",
            font=(FONT_TITLE_FAMILY, FONT_SIZE_TITLE), text_color=TEXT_PRIMARY,
        ).pack(padx=25, pady=(20, 15), anchor="w")

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Type selector
        type_frame = ctk.CTkFrame(card, fg_color=BG_CARD)
        type_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            type_frame, text="Type",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 10))

        self._type_var = ctk.StringVar(value="Off")
        self._type_menu = ctk.CTkOptionMenu(
            type_frame, values=_TYPE_OPTIONS, variable=self._type_var,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_INPUT, button_color=BG_HOVER, button_hover_color=DEEP_PINK,
            text_color=TEXT_PRIMARY, dropdown_fg_color=BG_INPUT,
            dropdown_text_color=TEXT_PRIMARY, dropdown_hover_color=DEEP_PINK,
            width=160, height=35, command=self._on_type_changed,
        )
        self._type_menu.pack(side="left")

        # Daily / Weekdays time frame
        self._time_frame = ctk.CTkFrame(card, fg_color=BG_CARD)

        ctk.CTkLabel(
            self._time_frame, text="Time (HH:MM)",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20)

        time_row = ctk.CTkFrame(self._time_frame, fg_color=BG_CARD)
        time_row.pack(fill="x", padx=20, pady=(5, 0))

        self._hour_entry = ctk.CTkEntry(
            time_row, width=60, height=35,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BORDER_COLOR, corner_radius=INPUT_CORNER_RADIUS,
            placeholder_text="09",
        )
        self._hour_entry.pack(side="left")

        ctk.CTkLabel(
            time_row, text=" : ",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._minute_entry = ctk.CTkEntry(
            time_row, width=60, height=35,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BORDER_COLOR, corner_radius=INPUT_CORNER_RADIUS,
            placeholder_text="30",
        )
        self._minute_entry.pack(side="left")

        # Interval frame
        self._interval_frame = ctk.CTkFrame(card, fg_color=BG_CARD)

        ctk.CTkLabel(
            self._interval_frame, text="Run every",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20)

        interval_row = ctk.CTkFrame(self._interval_frame, fg_color=BG_CARD)
        interval_row.pack(fill="x", padx=20, pady=(5, 0))

        self._interval_entry = ctk.CTkEntry(
            interval_row, width=80, height=35,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BORDER_COLOR, corner_radius=INPUT_CORNER_RADIUS,
            placeholder_text="30",
        )
        self._interval_entry.pack(side="left", padx=(0, 10))

        self._unit_var = ctk.StringVar(value="Minutes")
        ctk.CTkOptionMenu(
            interval_row, values=_UNIT_OPTIONS, variable=self._unit_var,
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_INPUT, button_color=BG_HOVER, button_hover_color=DEEP_PINK,
            text_color=TEXT_PRIMARY, dropdown_fg_color=BG_INPUT,
            dropdown_text_color=TEXT_PRIMARY, dropdown_hover_color=DEEP_PINK,
            width=120, height=35,
        ).pack(side="left")

        # Weekdays frame
        self._weekdays_frame = ctk.CTkFrame(card, fg_color=BG_CARD)

        ctk.CTkLabel(
            self._weekdays_frame, text="Days",
            font=(FONT_FAMILY, FONT_SIZE_LABEL), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20)

        days_row = ctk.CTkFrame(self._weekdays_frame, fg_color=BG_CARD)
        days_row.pack(fill="x", padx=20, pady=(5, 0))

        self._day_vars: dict[str, ctk.BooleanVar] = {}
        for day in _DAY_NAMES:
            var = ctk.BooleanVar(value=False)
            self._day_vars[day.lower()] = var
            ctk.CTkCheckBox(
                days_row, text=day, variable=var,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
                border_color=BORDER_COLOR, text_color=TEXT_PRIMARY,
                checkbox_width=18, checkbox_height=18, width=55,
            ).pack(side="left", padx=1)

        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color=BG_CARD)
        btn_frame.pack(fill="x", padx=20, pady=(15, 20), side="bottom")

        ctk.CTkButton(
            btn_frame, text="Save",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=DEEP_PINK, hover_color=DEEP_PINK_HOVER,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=100, height=38, command=self._save,
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            btn_frame, text="Cancel",
            font=(FONT_FAMILY, FONT_SIZE_DEFAULT),
            fg_color=BG_HOVER, hover_color=BG_INPUT,
            text_color=TEXT_PRIMARY, corner_radius=BUTTON_CORNER_RADIUS,
            width=100, height=38, command=self.destroy,
        ).pack(side="right")

        # Load current schedule
        self._load_schedule(current_schedule)

    def _load_schedule(self, raw: str) -> None:
        """Parse and populate the form from a schedule string."""
        if not raw or raw.lower() == "off":
            self._type_var.set("Off")
            self._on_type_changed("Off")
            return

        parts = raw.split("|")
        stype = parts[0].lower().strip()

        if stype == "daily" and len(parts) >= 2:
            self._type_var.set("Daily")
            self._set_time(parts[1])
        elif stype == "interval" and len(parts) >= 2:
            self._type_var.set("Interval")
            val = parts[1].strip().lower()
            if val.endswith("h"):
                self._interval_entry.insert(0, val[:-1])
                self._unit_var.set("Hours")
            elif val.endswith("m"):
                self._interval_entry.insert(0, val[:-1])
                self._unit_var.set("Minutes")
            else:
                self._interval_entry.insert(0, val)
        elif stype == "weekdays" and len(parts) >= 3:
            self._type_var.set("Weekdays")
            self._set_time(parts[1])
            for day_str in parts[2].lower().split(","):
                day_str = day_str.strip()
                if day_str in self._day_vars:
                    self._day_vars[day_str].set(True)
        else:
            self._type_var.set("Off")

        self._on_type_changed(self._type_var.get())

    def _set_time(self, time_str: str) -> None:
        try:
            h, m = time_str.strip().split(":")
            self._hour_entry.insert(0, h)
            self._minute_entry.insert(0, m)
        except ValueError:
            pass

    def _on_type_changed(self, value: str) -> None:
        self._time_frame.pack_forget()
        self._interval_frame.pack_forget()
        self._weekdays_frame.pack_forget()

        if value == "Daily":
            self._time_frame.pack(fill="x", pady=(5, 0))
        elif value == "Interval":
            self._interval_frame.pack(fill="x", pady=(5, 0))
        elif value == "Weekdays":
            self._time_frame.pack(fill="x", pady=(5, 0))
            self._weekdays_frame.pack(fill="x", pady=(5, 0))

    def _save(self) -> None:
        schedule = self._build_schedule_string()
        if schedule is None:
            return
        self._on_save(schedule)
        self.destroy()

    def _build_schedule_string(self) -> str | None:
        stype = self._type_var.get()

        if stype == "Off":
            return "off"

        if stype in ("Daily", "Weekdays"):
            time_str = self._get_time_str()
            if time_str is None:
                return None

        if stype == "Daily":
            return f"daily|{time_str}"

        elif stype == "Interval":
            val = self._interval_entry.get().strip()
            if not val or not val.isdigit() or int(val) <= 0:
                messagebox.showwarning("Invalid", "Enter a positive number.", parent=self)
                return None
            unit = "m" if self._unit_var.get() == "Minutes" else "h"
            return f"interval|{val}{unit}"

        elif stype == "Weekdays":
            days = self._get_selected_days()
            if not days:
                messagebox.showwarning("Invalid", "Select at least one day.", parent=self)
                return None
            return f"weekdays|{time_str}|{days}"

        return "off"

    def _get_time_str(self) -> str | None:
        h = self._hour_entry.get().strip()
        m = self._minute_entry.get().strip()
        if not h or not m:
            messagebox.showwarning("Invalid", "Enter hour and minute.", parent=self)
            return None
        try:
            hour = int(h)
            minute = int(m)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Time must be HH:MM (00-23:00-59).", parent=self)
            return None
        return f"{hour:02d}:{minute:02d}"

    def _get_selected_days(self) -> str:
        selected = []
        for day in _DAY_NAMES:
            if self._day_vars[day.lower()].get():
                selected.append(day.lower())
        return ",".join(selected)
