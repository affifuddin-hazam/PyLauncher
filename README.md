# PyLauncher

A lightweight Python script manager and launcher with a modern dark-themed GUI, built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

<img width="1102" height="677" alt="image" src="https://github.com/user-attachments/assets/f48dabb0-10e1-456f-9bc4-7441bec42bb0" />


## Background

PyLauncher started as a personal tool to simplify running and managing multiple Python monitoring scripts. Over time it became a team utility, originally written in VB.NET. This version is a complete rewrite in Python — designed for open-source use, with the internal download functionality removed and the focus kept on local script management.

## Features

**Script Management**
- Import, organize, tag, and delete Python script projects
- One-click start/stop with real-time output streaming
- Bulk actions: select multiple scripts and start, stop, or install dependencies at once
- Instant search and tag-based filtering

**Scheduling**
- Cron-style scheduler with daily, interval, and weekday modes
- Scripts auto-start on schedule, even when minimized to tray

**Dependency Management**
- Auto-create virtual environments and install requirements
- Auto-detect missing dependencies via pipreqs

**Developer Tools**
- Built-in CLI for running Python commands and installing pip packages
- Output search with Ctrl+F highlighting
- Log and output export to text files

**Quality of Life**
- Session restore — remembers running scripts across restarts
- File watcher — auto-detects new or removed scripts
- System tray — minimize and keep scripts running in the background
- Drag-and-drop import (Windows, optional)
- Configurable paths for Python, ChromeDriver, and Google Chrome
- Keyboard shortcuts: Ctrl+I (import), Ctrl+S (settings), Ctrl+L (logs), F5 (refresh)

## Requirements

- Python 3.10+
- Windows (primary target); Linux and macOS have partial support

## Installation

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dnd]"     # Drag-and-drop support (Windows)
pip install -e ".[build]"   # PyInstaller for building executables
pip install -e ".[dev]"     # Development tools (pytest)
```

## Usage

```bash
python -m pylauncher
```

### Getting Started

1. Launch the app and open **Settings** (Ctrl+S) to configure your Python executable path. You can also set ChromeDriver and Google Chrome paths here if your scripts use Selenium.
2. Click **Import** (Ctrl+I) to add a script folder. PyLauncher will copy the folder into its `scripts/` directory, auto-detect the main `.py` file, and generate a `me.ini` metadata file.
3. If no `requirements.txt` is found, the app will offer to scan imports and generate one automatically.

### Running Scripts

- Click the **play** button on any script row to start it. Output streams in real-time under the **Running** tab.
- Click the **stop** button to terminate a running script.
- When a script finishes or crashes, the output tab stays open so you can review the logs. Close it manually when done.
- Use the checkboxes to select multiple scripts, then use the bulk action bar to start, stop, or install dependencies for all of them at once.

### Scheduling

- Click the **timer** icon on a script row to open the schedule dialog.
- Choose a schedule type: **Daily** (run at a specific time), **Interval** (run every N minutes/hours), or **Weekdays** (run at a time on selected days).
- Scheduled scripts start automatically in the background. The scheduler runs even when the app is minimized to the system tray.

### Managing Dependencies

- If a script has a `requirements.txt`, click the **install** button to create a virtual environment and install dependencies.
- The install button is disabled for scripts without a `requirements.txt`.

### Other Features

- **Search** — Use the search bar to filter scripts by name. Click a tag to filter by tag.
- **Logs** — The Logs tab (Ctrl+L) shows application-level events: script starts, stops, imports, errors.
- **CLI** — Open the built-in CLI from the title bar to run Python commands or install packages directly.
- **System tray** — Closing the window minimizes to tray. Scripts keep running in the background. Right-click the tray icon to see running scripts or exit.
- **Drag-and-drop** — Drop a script folder onto the app window to import it (requires `windnd`).
- **Session restore** — On next launch, the app will ask if you want to restart scripts that were running when you last closed it.

## Script Structure

Each script lives in its own folder inside the `scripts/` directory:

```
scripts/
  my_script/
    main.py
    requirements.txt   (optional)
    me.ini             (auto-generated metadata)
```

The `me.ini` file stores metadata:

```ini
ScriptName=My Script
MainScript=main.py
Schedule=off
Tags=automation,monitoring
```

Schedule format examples:
- `off` — no schedule
- `daily|09:30` — run every day at 09:30
- `interval|30m` — run every 30 minutes
- `weekdays|08:00|mon,wed,fri` — run at 08:00 on specific days

### Accessing Settings from Scripts

PyLauncher stores shared configuration (Python path, ChromeDriver path, Google Chrome path) in `settings.ini` at the project root. Scripts can read these paths using the relative path `../../settings.ini` from their folder:

```python
import configparser

def load_settings(settings_file='../../settings.ini'):
    config = configparser.ConfigParser()
    config.read(settings_file)
    return config

config = load_settings()
chromedriver_path = config.get('DEFAULT', 'ChromeDriverPath')
chrome_path = config.get('DEFAULT', 'GoogleChromePath')
```

The `settings.ini` file is managed through the Settings dialog in the app:

```ini
[DEFAULT]
PythonPath=python
ChromeDriverPath=C:\Tools\chromedriver\chromedriver.exe
GoogleChromePath=C:\Program Files\Google\Chrome\Application\chrome.exe
```

This allows all your scripts to share the same configured paths without hardcoding them.

## Building an Executable

```bash
pip install -e ".[build]"
pyinstaller build.spec
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
