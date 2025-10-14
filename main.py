import atexit
import json
import os
import tkinter as tk

from db import AppDB
from app.views.main import MainWindow

SETTINGS_FILE = "settings.json"
DB_FILE = "data.db"


def ensure_settings(path: str):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 1}, f, ensure_ascii=False, indent=2)


def main():
    # High-DPI scaling for readability (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Tk scaling improves text/UI size on HiDPI
    try:
        root.tk.call("tk", "scaling", 1.25)
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

    # Ensure settings and DB
    ensure_settings(SETTINGS_FILE)
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