import atexit
import json
import os
import tkinter as tk
from tkinter import filedialog

from db import AppDB
from app.views.main import MainWindow

SETTINGS_FILE = "settings.json"
DB_FILE = "data.db"


def ensure_settings(path: str):
    if not os.path.exists(path):
        # Defaults: UI scale, export path, and notifications
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        export_path = desktop if os.path.isdir(desktop) else os.getcwd()
        defaults = {
            "version": 1,
            "ui_scale": 1.25,
            "export_path": export_path,
            "notify_enabled": True,
            "notify_interval_minutes": 10,
            "notify_age_hours": 24,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=2)


def load_settings(path: str) -> dict:
    ensure_settings(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def save_settings(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main():
    # High-DPI scaling for readability (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Load settings and apply UI scale
    app_settings = load_settings(SETTINGS_FILE)
    root.app_settings = app_settings
    ui_scale = float(app_settings.get("ui_scale", 1.25))
    try:
        root.tk.call("tk", "scaling", ui_scale)
    except tk.TclError:
        pass

    # Start maximized on all platforms
    try:
        root.state("zoomed")  # Windows
    except tk.TclError:
        try:
            root.attributes("-zoomed", True)  # Some X11/WM
        except tk.TclError:
            try:
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                root.geometry(f"{sw}x{sh}+0+0")
            except Exception:
                pass

    # Ensure DB
    root.db = AppDB(DB_FILE)

    # Ensure DB connection closes on exit
    def _close_db():
        db = getattr(root, "db", None)
        if db:
            try:
                db.conn.close()
            except Exception:
                pass

    atexit.register(_close_db)

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()