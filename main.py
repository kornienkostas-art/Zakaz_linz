import atexit
import json
import os
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import font as tkfont

from db import AppDB
from app.views.main import MainWindow
from app.tray import _start_tray, _stop_tray, _windows_autostart_set, _windows_autostart_get

SETTINGS_FILE = "settings.json"
DB_FILE = "data.db"


def ensure_settings(path: str):
    if not os.path.exists(path):
        # Defaults: UI scale, font size, export path and tray/autostart
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        export_path = desktop if os.path.isdir(desktop) else os.getcwd()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": 1,
                    "ui_scale": 1.25,
                    "ui_font_size": 17,
                    "export_path": export_path,
                    "tray_enabled": True,
                    "minimize_to_tray": True,
                    "start_in_tray": True,
                    "autostart_enabled": False,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )


def load_settings(path: str) -> dict:
    ensure_settings(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            # Fill missing keys with defaults
            defaults = {
                "ui_scale": 1.25,
                "ui_font_size": 17,
                "tray_enabled": True,
                "minimize_to_tray": True,
                "start_in_tray": True,
                "autostart_enabled": False,
            }
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return {}


def save_settings(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _apply_global_fonts(root: tk.Tk, size: int):
    # Update Tk named fonts used by ttk
    try:
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont"):
            try:
                f = tkfont.nametofont(name)
                f.configure(size=size)
                f.configure(weight="normal")
            except Exception:
                pass
        # Increase row height for Treeview to fit larger font
        try:
            style = ttk.Style(root)
            style.configure("Treeview", rowheight=size + 12)
            style.configure("Treeview.Heading", font=(None, size))
            style.configure("TButton", font=(None, size))
            style.configure("TLabel", font=(None, size))
            # Distinct style for 'Back' buttons
            style.configure("Back.TButton", font=(None, size + 1, "bold"), padding=(18, 12))
        except Exception:
            pass
    except Exception:
        pass


def _handle_close(root: tk.Tk):
    settings = getattr(root, "app_settings", {}) or {}
    if settings.get("tray_enabled", True) and settings.get("minimize_to_tray", True):
        try:
            root.withdraw()
            _start_tray(root)
            return  # do not quit
        except Exception:
            pass
    # Fallback: quit
    try:
        root.quit()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass


def _bind_minimize_to_tray(root: tk.Tk):
    # Intercept minimize (iconify) and move to tray
    def on_unmap(event):
        settings = getattr(root, "app_settings", {}) or {}
        if settings.get("tray_enabled", True) and settings.get("minimize_to_tray", True):
            try:
                if root.state() == "iconic":  # minimized
                    root.withdraw()
                    _start_tray(root)
            except Exception:
                pass
    try:
        root.bind("<Unmap>", on_unmap)
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

    # Apply global font size
    ui_font_size = int(app_settings.get("ui_font_size", 17))
    _apply_global_fonts(root, ui_font_size)

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

    # Apply autostart setting (Windows)
    try:
        if os.name == "nt":
            want_autostart = bool(app_settings.get("autostart_enabled", False))
            current = _windows_autostart_get()
            if want_autostart != current:
                _windows_autostart_set(want_autostart)
    except Exception:
        pass

    # Ensure DB connection closes on exit
    def _close_db():
        db = getattr(root, "db", None)
        if db:
            try:
                db.conn.close()
            except Exception:
                pass

    atexit.register(_close_db)

    # Close/minimize behavior
    try:
        root.protocol("WM_DELETE_WINDOW", lambda: _handle_close(root))
        _bind_minimize_to_tray(root)
    except Exception:
        pass

    # Launch UI
    if app_settings.get("tray_enabled", True) and app_settings.get("start_in_tray", True):
        # Initialize UI, then start hidden in tray
        try:
            MainWindow(root)
            root.main_initialized = True
        except Exception:
            pass
        try:
            root.withdraw()
            _start_tray(root)
        except Exception:
            # Fallback to visible UI
            MainWindow(root)
            root.main_initialized = True
            root.mainloop()
            return
    else:
        MainWindow(root)
        root.main_initialized = True

    root.mainloop()


if __name__ == "__main__":
    main()