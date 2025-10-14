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
                    "notify_enabled": False,
                    "notify_days": [],
                    "notify_time": "09:00",
                    "notify_sound_enabled": True,
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
                "notify_enabled": False,
                "notify_days": [],
                "notify_time": "09:00",
                "notify_sound_enabled": True,
                "notify_sound_alias": "SystemAsterisk",
                "notify_sound_mode": "alias",  # 'alias' or 'file'
                "notify_sound_file": "",
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

    # --- Notifications scheduler (Meridian 'Не заказан') ---
    _scheduler = {"snoozed_until": None}

    def _parse_notify_time(s: str):
        try:
            parts = (s or "").strip().split(":")
            hh = int(parts[0])
            mm = int(parts[1]) if len(parts) > 1 else 0
            return max(0, min(23, hh)), max(0, min(59, mm))
        except Exception:
            return 9, 0  # default 09:00

    def _should_notify(now):
        settings = root.app_settings or {}
        if not bool(settings.get("notify_enabled", False)):
            return False
        days = settings.get("notify_days") or []
        try:
            # Python Monday=0 ... Sunday=6
            wday = now.weekday()
        except Exception:
            wday = -1
        if wday not in days:
            return False
        hh, mm = _parse_notify_time(settings.get("notify_time", "09:00"))
        return (now.hour == hh and now.minute == mm)

    def _reveal_from_tray():
        # Robustly bring window to front even if tray helpers are unavailable
        try:
            from app.tray import _show_main_window
        except Exception:
            _show_main_window = None
        try:
            if _show_main_window:
                _show_main_window(root)
            else:
                root.deiconify()
                try:
                    root.state("zoomed")
                except Exception:
                    try:
                        root.attributes("-zoomed", True)
                    except Exception:
                        pass
                # Force focus/topmost briefly
                try:
                    root.attributes("-topmost", True)
                    root.after(300, lambda: root.attributes("-topmost", False))
                except Exception:
                    pass
        except Exception:
            pass

    def _check_and_notify():
        from datetime import datetime, timedelta

        now = datetime.now()

        # Snooze gate
        until = _scheduler.get("snoozed_until")
        if until and now < until:
            root.after(60_000, _check_and_notify)
            return

        if _should_notify(now):
            # Only notify if there are Meridian orders with status 'Не заказан'
            try:
                db = getattr(root, "db", None)
                orders = db.list_meridian_orders() if db else []
                pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан"]
            except Exception:
                pending = []
            if pending:
                # Reveal window reliably
                _reveal_from_tray()
                # Show notification dialog
                try:
                    from app.views.notify import show_meridian_notification
                    def on_snooze(minutes):
                        _scheduler["snoozed_until"] = now + timedelta(minutes=minutes)
                    def on_mark_ordered():
                        try:
                            for o in pending:
                                root.db.update_meridian_order(o["id"], {"status": "Заказан", "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                        except Exception:
                            pass
                    show_meridian_notification(root, pending, on_snooze=on_snooze, on_mark_ordered=on_mark_ordered)
                except Exception:
                    pass
        # Re-check every minute
        root.after(60_000, _check_and_notify)

    # Start scheduler loop
    try:
        root.after(3_000, _check_and_notify)
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