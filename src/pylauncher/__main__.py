"""Entry point for `python -m pylauncher`."""

from pylauncher.app import PyLauncherApp


def main() -> None:
    app = PyLauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
