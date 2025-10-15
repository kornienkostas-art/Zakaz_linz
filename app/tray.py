import os
import threading
from typing import Optional

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None
    ImageDraw = None


def _get_exec_command() -> str:
    """
    Return command string for autostart:
    - If running as packaged exe (sys.frozen): sys.executable
    - Else: pythonw.exe + full path to project main.py
    """
    import sys
    try:
        if getattr(sys, "frozen", False):
            return sys.executable
        # Prefer pythonw.exe to avoid console window on Windows
        pythonw = sys.executable
        try:
            base = os.path.dirname(sys.executable)
            candidate = os.path.join(base, "pythonw.exe")
            if os.path.isfile(candidate):
                pythonw = candidate
        except Exception:
            pass
        # Resolve path to main.py at project root (../main.py from this file)
        here = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.normpath(os.path.join(here, "..", "main.py"))
        if not os.path.isfile(main_script):
            # Fallback: try current working directory
            main_script = os.path.abspath("main.py")
        return f'"{pythonw}" "{main_script}"'
    except Exception:
        # Last resort
        return os.path.abspath("main.py")


def _windows_autostart_set(enabled: bool):
    """Enable/disable autostart via HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run."""
    if os.name != "nt":
        return
    try:
        import winreg
        app_name = "UssurochkiRF"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                cmd = _get_exec_command()
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
    except Exception:
        # Ignore errors silently; will be surfaced in UI when toggling
        pass


def _windows_autostart_get() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg
        app_name = "UssurochkiRF"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ) as key:
            try:
                _ = winreg.QueryValueEx(key, app_name)
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False


def _create_tray_image(settings: dict) -> Optional["Image.Image"]:
    """Create tray image from the best-suited asset.

    Heuristic:
    - Prefer square PNG with alpha and size >= 128 (closest to 192 ideal)
    - Fall back to ICO/other sizes
    - Finally, generate a simple placeholder if nothing found

    Also supports PyInstaller onefile by checking sys._MEIPASS.
    """
    if Image is None:
        return None

    # Candidate paths (explicit first)
    configured = (settings or {}).get("tray_logo_path") or ""
    rel_candidates = [
        configured,
        os.path.join("app", "assets", "logo.png"),
        os.path.join("app", "assets", "android-chrome-192x192.png"),
        os.path.join("app", "assets", "apple-touch-icon.png"),
        os.path.join("app", "assets", "favicon-32x32.png"),
        os.path.join("app", "assets", "favicon-16x16.png"),
        os.path.join("app", "assets", "favicon.ico"),
    ]

    # Resolve candidates against common bases (for PyInstaller onefile support)
    bases: list[str] = []
    try:
        import sys
        bases.extend([
            os.getcwd(),
            os.path.dirname(__file__),
            os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd(),
            getattr(sys, "_MEIPASS", None),
        ])
    except Exception:
        pass
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

    existing: list[str] = []
    for rel in rel_candidates:
        existing.extend(_resolve(rel))

    def _score(path: str) -> float:
        # Higher is better
        try:
            with Image.open(path) as im:
                w, h = im.size
                ext = os.path.splitext(path)[1].lower()
                score = 0.0
                # Format preference: PNG > ICO > others
                if ext == ".png":
                    score += 3.0
                elif ext == ".ico":
                    score += 1.5
                else:
                    score += 0.5
                # Prefer square
                if w == h:
                    score += 2.0
                else:
                    score -= 0.5
                # Prefer alpha channel (RGBA/LA)
                try:
                    if im.mode in ("RGBA", "LA") or ("transparency" in im.info):
                        score += 1.0
                except Exception:
                    pass
                # Prefer size >= 128, and around 128..256 (ideal 192)
                ideal = 192
                long_side = max(w, h)
                if long_side >= 128:
                    score += 2.0
                # penalize distance from ideal
                score -= abs(long_side - ideal) / 256.0
                return score
        except Exception:
            # If cannot open, but file exists — very low score
            return -10.0

    best_path = None
    best_score = -1e9
    for p in existing:
        s = _score(p)
        if s > best_score:
            best_score = s
            best_path = p

    if best_path:
        try:
            img = Image.open(best_path)
            img = img.convert("RGBA")
            img = img.resize((128, 128), Image.LANCZOS)
            return img
        except Exception:
            pass

    # Fallback: generate simple icon with text 'УО'
    img = Image.new("RGBA", (128, 128), (248, 250, 252, 255))  # bg #f8fafc
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 120, 120), fill=(59, 130, 246, 255))  # blue circle
    try:
        draw.text((36, 44), "УО", fill=(255, 255, 255, 255))
    except Exception:
        pass
    return img


def _start_tray(master):
    """Start system tray icon if pystray is available."""
    if pystray is None or Image is None:
        return
    # Avoid duplicates
    if getattr(master, "tray_icon", None):
        return

    settings = getattr(master, "app_settings", {})
    image = _create_tray_image(settings) or None

    def _ensure_main():
        try:
            from app.views.main import MainWindow
            # Initialize main window if not yet built
            if not getattr(master, "main_initialized", False):
                MainWindow(master)
                master.main_initialized = True
        except Exception:
            pass

    def on_open(icon, item=None):
        try:
            master.after(0, lambda: (_ensure_main(), _show_main_window(master), _stop_tray(master)))
        except Exception:
            pass

    def on_exit(icon, item=None):
        try:
            def _exit():
                # Save main window geometry before exit
                try:
                    geom = master.geometry()
                    settings = getattr(master, "app_settings", {}) or {}
                    settings["main_geometry"] = geom
                    try:
                        import json
                        with open("settings.json", "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            data["main_geometry"] = geom
                            with open("settings.json", "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                except Exception:
                    pass
                _stop_tray(master)
                try:
                    master.quit()
                except Exception:
                    pass
                try:
                    master.destroy()
                except Exception:
                    pass
            master.after(0, _exit)
        except Exception:
            pass

    def on_toggle_autostart(icon, item=None):
        try:
            cur = _windows_autostart_get()
            _windows_autostart_set(not cur)
            master.app_settings["autostart_enabled"] = not cur
            _stop_tray(master)
            _start_tray(master)
        except Exception:
            pass

    autostart_label = "Автозапуск: " + ("Вкл" if _windows_autostart_get() else "Выкл")
    menu = pystray.Menu(
        pystray.MenuItem("Открыть", on_open, default=True),
        pystray.MenuItem(autostart_label, on_toggle_autostart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Выход", on_exit),
    )

    icon = pystray.Icon("ussurochki_rf", image, title="УссурОЧки.рф", menu=menu)
    master.tray_icon = icon

    def run_icon():
        try:
            icon.run()
        except Exception:
            pass

    t = threading.Thread(target=run_icon, daemon=True)
    master.tray_thread = t
    t.start()


def _stop_tray(master):
    try:
        icon = getattr(master, "tray_icon", None)
        if icon:
            icon.stop()
        master.tray_icon = None
        master.tray_thread = None
    except Exception:
        pass


def _show_main_window(master):
    try:
        master.deiconify()
        # Maximize when restoring from tray
        try:
            master.state("zoomed")
        except Exception:
            try:
                master.attributes("-zoomed", True)
            except Exception:
                pass
        master.after(50, lambda: master.attributes("-alpha", 1.0))
    except Exception:
        pass