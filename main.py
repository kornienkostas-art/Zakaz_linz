import atexit
import json
import os
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import font as tkfont

from app.db import AppDB
from app.views.main import MainWindow
from app.tray import _start_tray, _stop_tray, _windows_autostart_set, _windows_autostart_get
from app.utils import install_copy_paste_bindings

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
                    "start_in_tray": False,  # start visible by default
                    "autostart_enabled": False,
                    "tray_logo_path": "app/assets/logo.png",
                    # Meridian notifications
                    "notify_enabled": False,
                    "notify_days": [],
                    "notify_time": "09:00",
                    # MKL notifications
                    "mkl_notify_enabled": False,
                    "mkl_notify_after_days": 3,
                    "mkl_notify_time": "09:00",
                    # Sound
                    "notify_sound_enabled": True,
                    "notify_sound_alias": "SystemAsterisk",
                    "notify_sound_mode": "alias",
                    "notify_sound_file": "",
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
                "start_in_tray": False,  # start visible by default
                "autostart_enabled": False,
                "tray_logo_path": "app/assets/logo.png",
                # Meridian notifications
                "notify_enabled": False,
                "notify_days": [],
                "notify_time": "09:00",
                # MKL notifications
                "mkl_notify_enabled": False,
                "mkl_notify_after_days": 3,
                "mkl_notify_time": "09:00",
                # Sound
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

    # Install global copy/paste bindings that work on any layout
    try:
        install_copy_paste_bindings(root)
    except Exception:
        pass

    # Load settings and apply UI scale
    app_settings = load_settings(SETTINGS_FILE)

    # Set crisp window icon (optimize for title bar): prefer 32x32 or ICO on Windows
    try:
        import sys
        configured = (app_settings.get("tray_logo_path") or "").strip()
        rel_candidates = [
            configured,
            os.path.join("app", "assets", "favicon.ico"),                  # often contains 16/32 px
            os.path.join("app", "assets", "favicon-32x32.png"),
            os.path.join("app", "assets", "favicon-16x16.png"),
            os.path.join("app", "assets", "android-chrome-192x192.png"),
            os.path.join("app", "assets", "apple-touch-icon.png"),
            os.path.join("app", "assets", "logo.png"),
        ]
        bases = [
            os.getcwd(),
            os.path.dirname(__file__),
            os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd(),
            getattr(sys, "_MEIPASS", None),
        ]
        bases = [b for b in bases if b]

        def _resolve(path_like: str) -> list[str]:
            if not path_like:
                return []
            if os.path.isabs(path_like) and os.path.isfile(path_like):
                return [path_like]
            paths = []
            for b in bases:
                p = os.path.normpath(os.path.join(b, path_like))
                try:
                    if os.path.isfile(p):
                        paths.append(p)
                except Exception:
                    continue
            return paths

        existing = []
        for rel in rel_candidates:
            existing.extend(_resolve(rel))

        # On Windows, prefer .ico directly for the title bar if available
        icon_path = None
        if os.name == "nt":
            for p in existing:
                if p.lower().endswith(".ico"):
                    icon_path = p
                    break

        if icon_path:
            try:
                root.iconbitmap(icon_path)
            except Exception:
                icon_path = None

        if not icon_path:
            # Create a 32x32 PNG for the title bar using Pillow if possible
            try:
                from PIL import Image
                src = None
                # Choose best source for downscale: square PNG with alpha and size >= 32
                def _score_src(path: str) -> float:
                    try:
                        with Image.open(path) as im:
                            w, h = im.size
                            ext = os.path.splitext(path)[1].lower()
                            score = 0.0
                            if ext == ".png": score += 3.0
                            if w == h: score += 2.0
                            if im.mode in ("RGBA", "LA") or ("transparency" in im.info): score += 1.0
                            long_side = max(w, h)
                            ideal = 48  # 32..48 for title looks crisp
                            if long_side >= 32: score += 1.5
                            score -= abs(long_side - ideal) / 128.0
                            return score
                    except Exception:
                        return -10.0
                best = None
                best_s = -1e9
                for p in existing:
                    if p.lower().endswith(".ico"):
                        continue
                    s = _score_src(p)
                    if s > best_s:
                        best_s = s
                        best = p
                src = best if best else (existing[0] if existing else None)

                if src:
                    with Image.open(src) as im:
                        im = im.convert("RGBA")
                        im = im.resize((32, 32), Image.LANCZOS)
                        # Ensure assets dir exists (works both dev and onefile temp)
                        out_dir = os.path.join(os.getcwd(), "app", "assets")
                        try:
                            os.makedirs(out_dir, exist_ok=True)
                        except Exception:
                            pass
                        out_path = os.path.join(out_dir, "_window_icon_32.png")
                        try:
                            im.save(out_path, format="PNG")
                            icon_img = tk.PhotoImage(file=out_path)
                            root.iconphoto(True, icon_img)
                            root._app_icon_img = icon_img  # keep ref to prevent GC
                        except Exception:
                            # fallback: try direct PhotoImage from src
                            try:
                                icon_img = tk.PhotoImage(file=src)
                                root.iconphoto(True, icon_img)
                                root._app_icon_img = icon_img
                            except Exception:
                                pass
            except Exception:
                # Last resort: try first existing as-is
                try:
                    if existing:
                        any_path = existing[0]
                        if any_path.lower().endswith(".ico") and os.name == "nt":
                            root.iconbitmap(any_path)
                        else:
                            icon_img = tk.PhotoImage(file=any_path)
                            root.iconphoto(True, icon_img)
                            root._app_icon_img = icon_img
                except Exception:
                    pass
    except Exception:
        pass
    root.app_settings = app_settings
    ui_scale = float(app_settings.get("ui_scale", 1.25))
    try:
        root.tk.call("tk", "scaling", ui_scale)
    except tk.TclError:
        pass

    # Apply global font size
    ui_font_size = int(app_settings.get("ui_font_size", 17))
    _apply_global_fonts(root, ui_font_size)

    # Restore main window geometry if saved; otherwise start maximized
    geom = app_settings.get("main_geometry")
    if isinstance(geom, str) and geom:
        try:
            root.geometry(geom)
        except Exception:
            pass
    else:
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
    _scheduler = {"snoozed_until": None, "mkl_snoozed_until": None}

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

        # Meridian snooze
        until = _scheduler.get("snoozed_until")
        if until and now < until:
            pass
        else:
            if _should_notify(now):
                # Meridian 'Не заказан'
                try:
                    db = getattr(root, "db", None)
                    orders = db.list_meridian_orders() if db else []
                    pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан"]
                except Exception:
                    pending = []
                if pending:
                    _reveal_from_tray()
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

        # MKL notifications: time-based daily check with age threshold
        try:
            settings = root.app_settings or {}
            if bool(settings.get("mkl_notify_enabled", False)):
                hh, mm = _parse_notify_time(settings.get("mkl_notify_time", "09:00"))
                if now.hour == hh and now.minute == mm:
                    # Snooze gate for MKL
                    mkl_until = _scheduler.get("mkl_snoozed_until")
                    if not (mkl_until and now < mkl_until):
                        days = int(settings.get("mkl_notify_after_days", 3))
                        threshold = now - timedelta(days=max(0, days))
                        try:
                            db = getattr(root, "db", None)
                            mkl_orders = db.list_mkl_orders() if db else []
                        except Exception:
                            mkl_orders = []
                        aged_pending = []
                        for o in mkl_orders:
                            try:
                                if (o.get("status", "") or "").strip() != "Не заказан":
                                    continue
                                ds = (o.get("date", "") or "").strip()
                                dt = None
                                for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
                                    try:
                                        from datetime import datetime as _dt
                                        dt = _dt.strptime(ds, fmt)
                                        break
                                    except Exception:
                                        continue
                                if dt is None:
                                    continue
                                if dt <= threshold:
                                    aged_pending.append(o)
                            except Exception:
                                continue
                        if aged_pending:
                            _reveal_from_tray()
                            try:
                                from app.views.notify import show_mkl_notification
                                def on_snooze_days(d):
                                    _scheduler["mkl_snoozed_until"] = now + timedelta(days=d)
                                def on_mark_ordered_mkl():
                                    try:
                                        for o in aged_pending:
                                            root.db.update_mkl_order(o["id"], {"status": "Заказан", "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                                    except Exception:
                                        pass
                                show_mkl_notification(root, aged_pending, on_snooze_days=on_snooze_days, on_mark_ordered=on_mark_ordered_mkl)
                            except Exception:
                                pass
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