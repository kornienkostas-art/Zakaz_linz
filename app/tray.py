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
    - Else: pythonw.exe + full path to main.py
    """
    import sys
    try:
        if getattr(sys, "frozen", False):
            return sys.executable
        # Fallback: use pythonw.exe to avoid console
        pythonw = sys.executable  # may be python.exe; try to find pythonw
        try:
            base = os.path.dirname(sys.executable)
            candidate = os.path.join(base, "pythonw.exe")
            if os.path.isfile(candidate):
                pythonw = candidate
        except Exception:
            pass
        script = os.path.abspath(__file__)
        return f'"{pythonw}" "{script}"'
    except Exception:
        # Last resort
        return os.path.abspath(__file__)


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
    """Create tray image from logo path or generate a simple one."""
    if Image is None:
        return None
    path = (settings or {}).get("tray_logo_path") or ""
    if path and os.path.isfile(path):
        try:
            img = Image.open(path)
            # Resize to typical tray icon size
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