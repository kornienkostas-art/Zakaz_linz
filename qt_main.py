import os
import sys
import json
import atexit
import ctypes
import platform
from typing import Optional

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLabel,
    QStatusBar,
    QSystemTrayIcon,
    QMenu,
    QFileDialog,
    QMessageBox,
)

# App DB and pages
from app.db import AppDB
from app.qt.orders_mkl import OrdersMklPage
from app.qt.clients import ClientsPage
from app.qt.products import ProductsPage
from app.qt.settings import SettingsPage

SETTINGS_FILE = "settings.json"
DB_FILE = "data.db"


def _windows_set_high_dpi_awareness():
    # No-op: Qt 6 uses DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 by default.
    # Explicit SetProcessDpiAwareness may fail or conflict; we rely on Qt defaults.
    return


def _desktop_path() -> str:
    try:
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "Desktop")
        if os.path.isdir(desktop):
            return desktop
    except Exception:
        pass
    return os.getcwd()


def ensure_settings(path: str):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": 1,
                    # Light theme only (as agreed)
                    "theme": "light",
                    # Design tokens
                    "primary_color": "#2563EB",
                    "font_family": "Segoe UI",
                    "font_size_base_pt": 12,
                    "scale_percent": 100,
                    "spacing_base_px": 8,
                    "corner_radius_px": 6,
                    # App behavior
                    "export_path": _desktop_path(),
                    "tray_enabled": True,
                    "minimize_to_tray": True,
                    "start_in_tray": False,
                    "autostart_enabled": True,
                    # Notifications (Meridian)
                    "notify_enabled": False,
                    "notify_days": [],
                    "notify_time": "09:00",
                    # Notifications (MKL)
                    "mkl_notify_enabled": False,
                    "mkl_notify_after_days": 3,
                    "mkl_notify_time": "09:00",
                    # Sound
                    "notify_sound_enabled": True,
                    "notify_sound_mode": "alias",  # alias or file
                    "notify_sound_alias": "SystemAsterisk",
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
            defaults = {
                "theme": "light",
                "primary_color": "#2563EB",
                "font_family": "Segoe UI",
                "font_size_base_pt": 12,
                "scale_percent": 100,
                "spacing_base_px": 8,
                "corner_radius_px": 6,
                "export_path": _desktop_path(),
                "tray_enabled": True,
                "minimize_to_tray": True,
                "start_in_tray": False,
                "autostart_enabled": True,
                # Notifications (Meridian)
                "notify_enabled": False,
                "notify_days": [],
                "notify_time": "09:00",
                # Notifications (MKL)
                "mkl_notify_enabled": False,
                "mkl_notify_after_days": 3,
                "mkl_notify_time": "09:00",
                # Sound
                "notify_sound_enabled": True,
                "notify_sound_mode": "alias",
                "notify_sound_alias": "SystemAsterisk",
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


def _windows_autostart_set(enabled: bool) -> bool:
    """Enable/disable autostart via HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"""
    if os.name != "nt":
        return False
    try:
        import winreg

        app_name = "UssurochkiRF"
        exe_path = sys.executable
        # If running from interpreter, try pythonw with qt_main.py
        if not getattr(sys, "frozen", False):
            # Use pythonw to avoid console window
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if os.path.isfile(pythonw):
                value = f'"{pythonw}" "{os.path.abspath(__file__)}"'
            else:
                value = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        else:
            # When packaged (PyInstaller), sys.executable points to the built exe
            value = f'"{exe_path}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, value)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _windows_autostart_get() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg

        app_name = "UssurochkiRF"
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        try:
            _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


class PlaceholderPage(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_lbl.setStyleSheet("font-weight: 600; font-size: 16pt; color: #0F172A;")
        hint = QLabel("Здесь будет функционал раздела.\nСписки, формы, фильтры и экспорт TXT.")
        hint.setStyleSheet("color: #475569;")
        hint.setWordWrap(True)
        layout.addWidget(title_lbl)
        layout.addWidget(hint)
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self, settings: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("УссурОЧки.рф")
        self.setMinimumSize(QSize(1024, 700))
        self._apply_icon()

        central = QWidget(self)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(self.settings.get("spacing_base_px", 8))

        # Sidebar navigation
        self.nav = QListWidget()
        self.nav.setFixedWidth(220)
        self.nav.addItem(QListWidgetItem("Заказы МКЛ"))
        self.nav.addItem(QListWidgetItem("Заказы «Меридиан»"))
        self.nav.addItem(QListWidgetItem("Клиенты"))
        self.nav.addItem(QListWidgetItem("Товары"))
        self.nav.addItem(QListWidgetItem("Настройки"))
        # Подключим обработчик навигации после инициализации страниц

        # Database connection (shared)
        self.db = AppDB(DB_FILE)

        # Stacked pages
        self.pages = QStackedWidget()
        # Orders MKL page (real implementation)
        self.pages.addWidget(OrdersMklPage(self.db, export_folder_getter=lambda: self.settings.get("export_path")))
        # Meridian orders (real implementation)
        from app.qt.orders_meridian import OrdersMeridianPage
        self.pages.addWidget(OrdersMeridianPage(self.db, export_folder_getter=lambda: self.settings.get("export_path")))
        # Clients page
        self.pages.addWidget(ClientsPage(self.db))
        # Products page (МКЛ/Меридиан)
        self.pages.addWidget(ProductsPage(self.db))
        # Settings page
        self.pages.addWidget(
            SettingsPage(
                get_settings=lambda: self.settings,
                save_settings=lambda s: save_settings(SETTINGS_FILE, s),
                apply_font=lambda ff, fs: self._apply_font_live(ff, fs),
                set_tray_enabled=lambda enabled: self._set_tray_enabled_live(enabled),
                toggle_autostart=lambda on: self._toggle_autostart_live(on),
            )
        )

        # Теперь подключаем обработчик и выбираем первую страницу
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.nav.setCurrentRow(0)

        root_layout.addWidget(self.nav)
        root_layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        # Status bar
        sb = QStatusBar()
        sb.showMessage("Готово")
        self.setStatusBar(sb)

        # Apply font per settings
        self._apply_font()

        # Tray icon
        self.tray = None
        if bool(settings.get("tray_enabled", True)):
            self._init_tray()

        # Autostart
        if os.name == "nt":
            want = bool(settings.get("autostart_enabled", True))
            current = _windows_autostart_get()
            if want != current:
                _windows_autostart_set(want)

        # Notifications scheduler (Meridian/MKL)
        self._scheduler = {"snoozed_until": None, "mkl_snoozed_until": None}
        self._timer = QTimer(self)
        self._timer.setInterval(60_000)  # 1 minute
        self._timer.timeout.connect(self._check_and_notify)
        # First check shortly after start
        QTimer.singleShot(3_000, self._check_and_notify)
        self._timer.start()

    def _apply_font(self):
        try:
            ff = self.settings.get("font_family", "Segoe UI")
            size_pt = int(self.settings.get("font_size_base_pt", 12))
            font = QFont(ff, pointSize=size_pt)
            QApplication.instance().setFont(font)
        except Exception:
            pass

    def _apply_font_live(self, ff: str, fs: int):
        # Update settings and apply font immediately
        try:
            self.settings["font_family"] = ff
            self.settings["font_size_base_pt"] = int(fs)
            font = QFont(ff, pointSize=int(fs))
            QApplication.instance().setFont(font)
        except Exception:
            pass

    def _apply_icon(self):
        # Try to use an icon from assets if available; otherwise default
        candidates = [
            os.path.join("app", "assets", "favicon.ico"),
            os.path.join("app", "assets", "logo.png"),
            os.path.join("app", "assets", "apple-touch-icon.png"),
        ]
        icon = None
        for p in candidates:
            try:
                if os.path.isfile(p):
                    icon = QIcon(p)
                    break
            except Exception:
                continue
        if icon is None:
            icon = QIcon()  # empty icon fallback
        self.setWindowIcon(icon)

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        tray_icon = self.windowIcon() if not self.windowIcon().isNull() else QIcon()
        tray = QSystemTrayIcon(tray_icon, self)
        menu = QMenu()

        act_open = QAction("Открыть", self)
        act_open.triggered.connect(self._show_main)
        menu.addAction(act_open)

        self.act_autostart = QAction("Автозапуск", self)
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(bool(self.settings.get("autostart_enabled", True)))
        self.act_autostart.triggered.connect(self._toggle_autostart)
        menu.addAction(self.act_autostart)

        act_export_folder = QAction("Выбрать папку экспорта…", self)
        act_export_folder.triggered.connect(self._choose_export_folder)
        menu.addAction(act_export_folder)

        menu.addSeparator()
        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        tray.setContextMenu(menu)
        tray.setToolTip("УссурОЧки.рф")
        tray.activated.connect(self._tray_activated)
        tray.show()
        self.tray = tray

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            # Left click: show window
            self._show_main()

    def _show_main(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _toggle_autostart(self, checked: bool):
        ok = _windows_autostart_set(checked)
        if ok:
            self.settings["autostart_enabled"] = checked
            save_settings(SETTINGS_FILE, self.settings)
        else:
            QMessageBox.warning(self, "Автозапуск", "Не удалось изменить настройку автозапуска.")

    def _toggle_autostart_live(self, on: bool) -> bool:
        # Called from settings page
        ok = _windows_autostart_set(on)
        if ok:
            self.settings["autostart_enabled"] = bool(on)
        return ok

    def _choose_export_folder(self):
        start_dir = self.settings.get("export_path") or _desktop_path()
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку экспорта", start_dir)
        if folder:
            self.settings["export_path"] = folder
            save_settings(SETTINGS_FILE, self.settings)
            self.statusBar().showMessage(f"Папка экспорта: {folder}", 3000)

    def _set_tray_enabled_live(self, enabled: bool):
        # Enable/disable tray icon at runtime
        try:
            if enabled and self.tray is None:
                self._init_tray()
            elif not enabled and self.tray is not None:
                self.tray.hide()
                self.tray = None
            self.settings["tray_enabled"] = bool(enabled)
        except Exception:
            pass

    def closeEvent(self, event):
        if bool(self.settings.get("tray_enabled", True)) and bool(self.settings.get("minimize_to_tray", True)):
            event.ignore()
            self.hide()
            if self.tray:
                self.tray.showMessage("УссурОЧки.рф", "Приложение свернуто в трей.", QSystemTrayIcon.Information, 2000)
        else:
            super().closeEvent(event)

    def _quit_app(self):
        # Сохранить настройки при выходе, корректно завершить приложение
        try:
            save_settings(SETTINGS_FILE, self.settings)
        except Exception:
            pass
        try:
            QApplication.instance().quit()
        except Exception:
            os._exit(0)

    def _on_nav_changed(self, row: int):
        # Guard against early signal before pages are initialized
        try:
            if hasattr(self, "pages") and self.pages is not None:
                self.pages.setCurrentIndex(max(0, int(row)))
        except Exception:
            pass

    def _reveal_from_tray(self):
        # Bring window to front
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _parse_notify_time(self, s: str):
        try:
            parts = (s or "").strip().split(":")
            hh = int(parts[0])
            mm = int(parts[1]) if len(parts) > 1 else 0
            return max(0, min(23, hh)), max(0, min(59, mm))
        except Exception:
            return 9, 0

    def _should_notify_meridian(self, now_dt):
        s = self.settings
        if not bool(s.get("notify_enabled", False)):
            return False
        days = s.get("notify_days") or []
        try:
            wday = now_dt.weekday()  # Monday=0
        except Exception:
            wday = -1
        if wday not in days:
            return False
        hh, mm = self._parse_notify_time(s.get("notify_time", "09:00"))
        return (now_dt.hour == hh and now_dt.minute == mm)

    def _play_notify_sound(self):
        try:
            s = self.settings
            if not bool(s.get("notify_sound_enabled", True)):
                return
            if os.name == "nt":
                import winsound
                mode = (s.get("notify_sound_mode") or "alias")
                if mode == "file":
                    wav = (s.get("notify_sound_file") or "").strip()
                    if wav:
                        try:
                            winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        except Exception:
                            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                else:
                    alias = (s.get("notify_sound_alias") or "SystemAsterisk")
                    try:
                        winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
                    except Exception:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                # Fallback bell
                QApplication.beep()
        except Exception:
            pass

    def _check_and_notify(self):
        from datetime import datetime, timedelta

        now = datetime.now()

        # Meridian snooze
        until = self._scheduler.get("snoozed_until")
        if not (until and now < until):
            if self._should_notify_meridian(now):
                try:
                    orders = self.db.list_meridian_orders()
                    pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан"]
                except Exception:
                    pending = []
                if pending:
                    self._reveal_from_tray()
                    self._play_notify_sound()
                    if self.tray:
                        self.tray.showMessage(
                            "УссурОЧки.рф",
                            f"Есть заказы «Меридиан» со статусом «Не заказан»: {len(pending)}",
                            QSystemTrayIcon.Information,
                            3000,
                        )
                    try:
                        from app.qt.notify import show_meridian_notification

                        def on_snooze(minutes: int):
                            self._scheduler["snoozed_until"] = now + timedelta(minutes=minutes)

                        def on_mark_ordered():
                            try:
                                for o in pending:
                                    self.db.update_meridian_order(
                                        o["id"],
                                        {"status": "Заказан", "date": datetime.now().strftime("%Y-%m-%d %H:%M")},
                                    )
                            except Exception:
                                pass

                        show_meridian_notification(self, pending, on_snooze=on_snooze, on_mark_ordered=on_mark_ordered)
                    except Exception:
                        pass

        # MKL notifications: daily check with age threshold
        try:
            s = self.settings
            if bool(s.get("mkl_notify_enabled", False)):
                hh, mm = self._parse_notify_time(s.get("mkl_notify_time", "09:00"))
                if now.hour == hh and now.minute == mm:
                    mkl_until = self._scheduler.get("mkl_snoozed_until")
                    if not (mkl_until and now < mkl_until):
                        days = int(s.get("mkl_notify_after_days", 3))
                        threshold = now - timedelta(days=max(0, days))
                        try:
                            mkl_orders = self.db.list_mkl_orders()
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
            self._reveal_from_tray()
            self._play_notify_sound()
            if self.tray:
                self.tray.showMessage(
                    "УссурОЧки.рф",
                    f"Есть просроченные заказы МКЛ со статусом «Не заказан»: {len(aged_pending)}",
                    QSystemTrayIcon.Information,
                    3000,
                )
            try:
                from app.qt.notify import show_mkl_notification

                def on_snooze_days(d: int):
                    self._scheduler["mkl_snoozed_until"] = now + timedelta(days=d)

                def on_mark_ordered_mkl():
                    try:
                        for o in aged_pending:
                            self.db.update_mkl_order(
                                o["id"],
                                {"status": "Заказан", "date": datetime.now().strftime("%Y-%m-%d %H:%M")},
                            )
                    except Exception:
                        pass

                show_mkl_notification(
                    self, aged_pending, on_snooze_days=on_snooze_days, on_mark_ordered=on_mark_ordered_mkl
                )
            except Exception:
                pass

                                show_mkl_notification(
                                    self, aged_pending, on_snooze_days=on_snooze_days, on_mark_ordered=on_mark_ordered_mkl
                                )
                            except Exception:
                                pass
        except Exception:
            pass


def main():
    # Rely on Qt 6 default DPI awareness (Per-Monitor v2)
    app = QApplication(sys.argv)

    # Qt 6 уже включает HighDPIHiDPI-пиксмапы по умолчанию.
    # Дополнительных установок атрибутов не требуется.

    settings = load_settings(SETTINGS_FILE)

    # Use scale_percent if needed in future; for now we stick to base font and Qt auto-scaling
    win = MainWindow(settings)

    # Start in tray or normal
    if bool(settings.get("tray_enabled", True)) and bool(settings.get("start_in_tray", False)):
        win.hide()
    else:
        win.show()

    # Ensure clean exit tasks
    def _cleanup():
        # placeholder for DB cleanup when integrated
        pass

    atexit.register(_cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()