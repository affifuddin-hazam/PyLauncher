"""Main application class — the central controller."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from pylauncher.constants import (
    BG_DARK,
    MAIN_WINDOW_WIDTH,
    MAIN_WINDOW_HEIGHT,
)
from pylauncher.core.config import AppSettings, SettingsManager, ScriptMetaManager
from pylauncher.core.script_manager import ScriptInfo, ScriptManager
from pylauncher.core.process_handler import ProcessHandler
from pylauncher.core.venv_manager import VenvManager
from pylauncher.core.state import StateManager, AppState
from pylauncher.core.file_watcher import ScriptWatcher
from pylauncher.core.tray_manager import TrayManager
from pylauncher.core.scheduler import Scheduler
from pylauncher.utils.assets import get_settings_path, get_scripts_dir, get_state_path, get_app_icon_path
from pylauncher.ui.title_bar import TitleBar
from pylauncher.ui.main_window import MainWindow


class PyLauncherApp(ctk.CTk):
    """Root application window and controller."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")

        # Borderless window
        self.overrideredirect(True)
        self.title("PyLauncher")
        self.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self._center_window()
        self._setup_taskbar_icon()

        # Core initialization
        self._settings_manager = SettingsManager(get_settings_path())
        self._settings = self._settings_manager.load()
        self._script_manager = ScriptManager(get_scripts_dir())
        self._process_handler = ProcessHandler(self._settings.python_path)
        self._venv_manager = VenvManager(self._settings.python_path)
        self._state_manager = StateManager(get_state_path())

        # UI
        self._title_bar = TitleBar(
            self,
            on_settings=self.open_settings,
            on_cli=self.open_cli,
            on_close=self._on_close,
        )
        self._title_bar.pack(fill="x")

        self._main_window = MainWindow(self, self)
        self._main_window.pack(fill="both", expand=True)

        # Load scripts
        self._main_window.installed_tab.refresh_scripts()
        self._main_window.logs_tab.log("PyLauncher started.")

        # Scheduler
        self._scheduler = Scheduler(
            on_trigger=lambda key: self.after(0, lambda: self._on_scheduled_trigger(key)),
            is_running=self._process_handler.is_running,
            on_log=lambda msg: self.after(0, lambda: self._main_window.logs_tab.log(msg)),
        )
        self._load_schedules()
        self._scheduler.start()

        # File watcher for auto-discovery
        self._script_watcher = ScriptWatcher(
            get_scripts_dir(),
            on_change=lambda: self.after(0, self._main_window.installed_tab.refresh_scripts),
        )
        self._script_watcher.start()

        # System tray
        self._tray = TrayManager(
            on_show=lambda: self.after(0, self._show_window),
            on_exit=lambda: self.after(0, self._on_exit),
            get_running_names=self._process_handler.get_running_names,
        )
        self._tray.start()

        # Keyboard shortcuts
        self.bind_all("<Control-i>", lambda e: self.import_script())
        self.bind_all("<Control-s>", lambda e: self.open_settings())
        self.bind_all("<Control-l>", lambda e: self._main_window.set_tab("Logs"))
        self.bind_all("<F5>", lambda e: self._main_window.installed_tab.refresh_scripts())

        # Restore previous session
        self._restore_previous_session()

        # Drag-and-drop (optional)
        self._setup_dnd()

        # Shutdown hook
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Properties ──

    @property
    def script_manager(self) -> ScriptManager:
        return self._script_manager

    @property
    def process_handler(self) -> ProcessHandler:
        return self._process_handler

    # ── Controller methods ──

    def start_script(self, script_info: ScriptInfo) -> None:
        folder_key = script_info.folder_path.name
        if self._process_handler.is_running(folder_key):
            return
        if not script_info.meta.main_script:
            messagebox.showwarning("Warning", "No Python script found to run.")
            return

        self._main_window.logs_tab.log(f"Starting: {script_info.meta.script_name}")

        def on_output(key: str, line: str) -> None:
            self.after(0, lambda: self._main_window.running_tab.append_output(key, line))

        def on_exit(key: str, rc: int) -> None:
            self.after(0, lambda: self._on_script_exit(key, rc))

        self._process_handler.start_script(
            folder_path=script_info.folder_path,
            main_script=script_info.meta.main_script,
            script_name=script_info.meta.script_name,
            on_output=on_output,
            on_exit=on_exit,
        )

        self._main_window.running_tab.add_process_tab(folder_key, script_info.meta.script_name)
        self._main_window.installed_tab.update_script_state(folder_key, running=True)
        self._tray.update_menu()

    def stop_script(self, script_info: ScriptInfo) -> None:
        self.stop_script_by_key(script_info.folder_path.name)

    def stop_script_by_key(self, folder_key: str) -> None:
        self._main_window.logs_tab.log(f"Stopping: {folder_key}")
        self._process_handler.stop_script(folder_key)
        self._main_window.running_tab.remove_process_tab(folder_key)
        self._main_window.installed_tab.update_script_state(folder_key, running=False)
        self._tray.update_menu()

    def install_requirements(self, script_info: ScriptInfo) -> None:
        folder_path = script_info.folder_path
        self._main_window.logs_tab.log(f"Installing requirements for: {script_info.meta.script_name}")

        def on_output(line: str) -> None:
            self.after(0, lambda: self._main_window.logs_tab.log(line))

        def on_complete(success: bool) -> None:
            if success:
                self.after(0, lambda: messagebox.showinfo("Success", "Requirements installed successfully!"))
            self.after(0, lambda: self._main_window.installed_tab.refresh_scripts())

        self._venv_manager.install_requirements(folder_path, on_output, on_complete)

    def import_script(self) -> None:
        folder = filedialog.askdirectory(title="Select script folder")
        if not folder:
            return

        source = Path(folder)
        py_files = list(source.glob("*.py"))
        if not py_files:
            messagebox.showwarning("Warning", "No Python (.py) files found in the folder.")
            return

        dest = self._script_manager.scripts_dir / source.name
        if dest.exists():
            messagebox.showwarning("Warning", f"Script folder '{source.name}' already exists.")
            return

        dialog = ctk.CTkInputDialog(text="Enter the script name:", title="Script Name")
        self._center_dialog(dialog)
        script_name = dialog.get_input()
        if not script_name:
            return

        self._main_window.logs_tab.log(f"Importing: {script_name}")

        def on_progress(msg: str) -> None:
            self.after(0, lambda: self._main_window.logs_tab.log(msg))

        try:
            info = self._script_manager.import_script(source, script_name, on_progress)
            self._main_window.installed_tab.refresh_scripts()
            self._main_window.logs_tab.log(f"Import complete: {script_name}")

            # Auto-detect requirements if missing
            if not info.has_requirements and self._settings.python_path:
                result = messagebox.askyesno(
                    "Auto-detect Requirements",
                    "No requirements.txt found. Scan imports to generate one?",
                )
                if result:
                    self._script_manager.auto_generate_requirements(
                        info.folder_path,
                        self._settings.python_path,
                        on_output=lambda msg: self.after(0, lambda: self._main_window.logs_tab.log(msg)),
                        on_complete=lambda ok: self.after(0, lambda: self._main_window.installed_tab.refresh_scripts()),
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def delete_script(self, script_info: ScriptInfo) -> None:
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{script_info.meta.script_name}'?",
        )
        if not result:
            return

        folder_key = script_info.folder_path.name
        if self._process_handler.is_running(folder_key):
            self.stop_script_by_key(folder_key)

        self._scheduler.remove_schedule(folder_key)
        self._script_manager.delete_script(script_info)
        self._main_window.installed_tab.refresh_scripts()
        self._main_window.logs_tab.log(f"Deleted: {script_info.meta.script_name}")

    def open_settings(self) -> None:
        from pylauncher.ui.dialogs.settings_dialog import SettingsDialog
        SettingsDialog(self, self._settings_manager, self._settings, self._on_settings_saved)

    def open_cli(self) -> None:
        from pylauncher.ui.dialogs.cli_dialog import CLIDialog
        CLIDialog(self, self._settings.python_path)

    def open_schedule(self, script_info: ScriptInfo) -> None:
        from pylauncher.ui.dialogs.schedule_dialog import ScheduleDialog

        def on_save(new_schedule: str) -> None:
            script_info.meta.schedule = new_schedule
            ScriptMetaManager.save(script_info.folder_path, script_info.meta)
            folder_key = script_info.folder_path.name
            self._scheduler.update_schedule(folder_key, new_schedule)
            self._main_window.installed_tab.refresh_scripts()
            self._main_window.logs_tab.log(
                f"Schedule updated for '{script_info.meta.script_name}': {new_schedule}"
            )

        ScheduleDialog(
            self,
            script_name=script_info.meta.script_name,
            current_schedule=script_info.meta.schedule,
            on_save=on_save,
        )

    # ── Private methods ──

    def _load_schedules(self) -> None:
        """Load all script schedules into the scheduler."""
        scripts = self._script_manager.discover_all()
        schedule_map = {
            s.folder_path.name: s.meta.schedule
            for s in scripts
            if s.meta.has_schedule
        }
        self._scheduler.load_all(schedule_map)

    def _on_scheduled_trigger(self, folder_key: str) -> None:
        """Handle a scheduler trigger — find the script and start it."""
        scripts = self._script_manager.discover_all()
        script_map = {s.folder_path.name: s for s in scripts}
        if folder_key in script_map:
            self._main_window.logs_tab.log(
                f"[Scheduler] Starting '{script_map[folder_key].meta.script_name}'"
            )
            self.start_script(script_map[folder_key])
        else:
            self._main_window.logs_tab.log(
                f"[Scheduler] Script '{folder_key}' not found, skipping."
            )

    def _on_settings_saved(self, settings: AppSettings) -> None:
        self._settings = settings
        self._process_handler.update_python_path(settings.python_path)
        self._venv_manager.update_python_path(settings.python_path)
        self._main_window.logs_tab.log("Settings updated.")

    def _on_script_exit(self, folder_key: str, return_code: int) -> None:
        self._main_window.logs_tab.log(f"Script '{folder_key}' exited with code {return_code}")
        self._main_window.running_tab.mark_exited(folder_key, return_code)
        self._main_window.installed_tab.update_script_state(folder_key, running=False)
        self._tray.update_menu()

    def _on_close(self) -> None:
        """Minimize to tray if available, otherwise exit."""
        if self._tray.available:
            self.withdraw()
        else:
            self._on_exit()

    def _on_exit(self) -> None:
        """Actually exit the application."""
        # Save running script state for next session
        running_keys = self._process_handler.get_running_keys()
        if running_keys:
            self._state_manager.save(AppState(running_scripts=running_keys))

        self._scheduler.stop()
        self._script_watcher.stop()
        self._tray.stop()
        self._process_handler.shutdown()
        self.destroy()

    def _show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _restore_previous_session(self) -> None:
        state = self._state_manager.load()
        if not state.running_scripts:
            return

        names = ", ".join(state.running_scripts)
        result = messagebox.askyesno(
            "Restore Session",
            f"Previously running scripts:\n{names}\n\nRestart them?",
        )
        if result:
            scripts = self._script_manager.discover_all()
            script_map = {s.folder_path.name: s for s in scripts}
            for key in state.running_scripts:
                if key in script_map:
                    self.start_script(script_map[key])

        self._state_manager.clear()

    def _setup_dnd(self) -> None:
        """Set up drag-and-drop if windnd is available (Windows only)."""
        try:
            import windnd
            windnd.hook_dropfiles(self, func=self._on_dnd_drop)
            self._main_window.logs_tab.log("Drag-and-drop enabled.")
        except ImportError:
            pass

    def _on_dnd_drop(self, files: list) -> None:
        """Handle dropped files/folders."""
        for file_bytes in files:
            path_str = file_bytes.decode("utf-8") if isinstance(file_bytes, bytes) else str(file_bytes)
            source = Path(path_str)
            if source.is_dir() and list(source.glob("*.py")):
                dest = self._script_manager.scripts_dir / source.name
                if dest.exists():
                    self._main_window.logs_tab.log(f"Skipped: '{source.name}' already exists.")
                    continue

                dialog = ctk.CTkInputDialog(
                    text=f"Name for '{source.name}':", title="Script Name"
                )
                self._center_dialog(dialog)
                script_name = dialog.get_input()
                if script_name:
                    try:
                        self._script_manager.import_script(source, script_name)
                        self._main_window.installed_tab.refresh_scripts()
                        self._main_window.logs_tab.log(f"Imported via drop: {script_name}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Import failed: {e}")

    def _center_dialog(self, dialog: ctk.CTkToplevel) -> None:
        """Center a dialog over the main window."""
        dialog.update_idletasks()
        dw = dialog.winfo_width()
        dh = dialog.winfo_height()
        x = self.winfo_x() + (self.winfo_width() - dw) // 2
        y = self.winfo_y() + (self.winfo_height() - dh) // 2
        dialog.geometry(f"+{x}+{y}")

    def _setup_taskbar_icon(self) -> None:
        """Show the borderless window in the taskbar with an icon (Windows)."""
        import sys

        try:
            ico_path = get_app_icon_path()
            self.iconbitmap(str(ico_path))
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                import ctypes

                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080

                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                # Re-show to apply the style change
                self.withdraw()
                self.after(10, self.deiconify)
            except Exception:
                pass

    def _center_window(self) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - MAIN_WINDOW_WIDTH) // 2
        y = (screen_h - MAIN_WINDOW_HEIGHT) // 2
        self.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}+{x}+{y}")
