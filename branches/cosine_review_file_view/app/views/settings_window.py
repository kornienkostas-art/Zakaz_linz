import json
import tkinter as tk
from tkinter import ttk

from app.views.settings import SettingsView

class StyledSettingsWindow(tk.Toplevel):
    """Отдельное окно 'красивых' настроек с сохранением/восстановлением геометрии."""

    SETTINGS_GEOMETRY_KEY = "settings_geometry"

    def __init__(self, master: tk.Misc, on_close=None):
        super().__init__(master)
        self.title("Настройки")
        try:
            self.configure(bg="#f8fafc")
        except Exception:
            pass

        # поделиться словарем настроек приложения
        self.app_settings = getattr(master, "app_settings", {}) or {}
        self._on_close = on_close

        # восстановить геометрию окна, если сохранена
        try:
            geom = self.app_settings.get(self.SETTINGS_GEOMETRY_KEY)
            if isinstance(geom, str) and geom:
                self.geometry(geom)
        except Exception:
            pass

        # поведение закрытия
        try:
            self.protocol("WM_DELETE_WINDOW", self._close)
        except Exception:
            pass

        # встраиваем существующее представление настроек
        SettingsView(self, on_back=self._close)

        # делаем окно модальным
        try:
            self.transient(master)
            self.grab_set()
        except Exception:
            pass

        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _close(self):
        # сохранить геометрию окна в настройки
        try:
            geom = self.geometry()
            self.app_settings[self.SETTINGS_GEOMETRY_KEY] = geom
            # записать на диск без изменения прочих полей
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data[self.SETTINGS_GEOMETRY_KEY] = geom
                with open("settings.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:
            self.destroy()
        finally:
            cb = getattr(self, "_on_close", None)
            if callable(cb):
                try:
                    cb()
                except Exception:
                    pass