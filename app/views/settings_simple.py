import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


SETTINGS_FILE = "settings.json"


class SettingsWindow(tk.Toplevel):
    """Простое окно настроек без кастомных стилей, чтобы гарантированно отображалось."""

    def __init__(self, master: tk.Misc, on_close=None):
        super().__init__(master)
        self.title("Настройки")
        self.transient(master)
        self.grab_set()
        try:
            self.configure(bg="#f0f0f0")
        except Exception:
            pass

        # link root settings dict if exists
        self.settings = getattr(master, "app_settings", {}) or {}

        self.columnconfigure(0, weight=1)
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        # UI scale
        ttk.Label(frm, text="Масштаб интерфейса").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.ui_scale_var = tk.DoubleVar(value=float(self.settings.get("ui_scale", 1.25)))
        ttk.Spinbox(frm, from_=0.8, to=2.0, increment=0.05, textvariable=self.ui_scale_var, width=10).grid(row=0, column=1, sticky="w")

        # Font size
        ttk.Label(frm, text="Размер шрифта").grid(row=1, column=0, sticky="w", pady=(8, 4))
        self.ui_font_size_var = tk.IntVar(value=int(self.settings.get("ui_font_size", 17)))
        ttk.Spinbox(frm, from_=12, to=28, textvariable=self.ui_font_size_var, width=10).grid(row=1, column=1, sticky="w")

        # Export path
        ttk.Separator(frm).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(frm, text="Папка экспорта TXT").grid(row=3, column=0, sticky="w", pady=(0, 4))
        self.export_var = tk.StringVar(value=self.settings.get("export_path") or "")
        export_row = ttk.Frame(frm)
        export_row.grid(row=3, column=1, sticky="ew")
        export_row.columnconfigure(0, weight=1)
        ttk.Entry(export_row, textvariable=self.export_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(export_row, text="Обзор…", command=self._choose_export).grid(row=0, column=1, padx=(8, 0))

        # Tray/autostart
        ttk.Separator(frm).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(frm, text="Трей и автозапуск").grid(row=5, column=0, sticky="w")
        self.tray_enabled_var = tk.BooleanVar(value=bool(self.settings.get("tray_enabled", True)))
        ttk.Checkbutton(frm, text="Включить системный трей", variable=self.tray_enabled_var).grid(row=5, column=1, sticky="w")

        self.minimize_to_tray_var = tk.BooleanVar(value=bool(self.settings.get("minimize_to_tray", True)))
        ttk.Checkbutton(frm, text="Сворачивать в трей (закрыть/свернуть)", variable=self.minimize_to_tray_var).grid(row=6, column=1, sticky="w")

        self.start_in_tray_var = tk.BooleanVar(value=bool(self.settings.get("start_in_tray", True)))
        ttk.Checkbutton(frm, text="Запускать в трее (при старте)", variable=self.start_in_tray_var).grid(row=7, column=1, sticky="w")

        self.autostart_var = tk.BooleanVar(value=bool(self.settings.get("autostart_enabled", False)))
        ttk.Checkbutton(frm, text="Автозапуск с Windows", variable=self.autostart_var).grid(row=8, column=1, sticky="w")

        # Notifications
        ttk.Separator(frm).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(frm, text="Уведомления Меридиан (статус 'Не заказан')").grid(row=10, column=0, sticky="w")
        self.notify_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_enabled", False)))
        ttk.Checkbutton(frm, text="Включить уведомления", variable=self.notify_enabled_var).grid(row=10, column=1, sticky="w")

        ttk.Label(frm, text="Дни недели (Пн=0 … Вс=6)").grid(row=11, column=0, sticky="w", pady=(4, 0))
        days_frame = ttk.Frame(frm)
        days_frame.grid(row=11, column=1, sticky="w")
        self.notify_days_vars = []
        labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        current_days = set(self.settings.get("notify_days") or [])
        for i, lbl in enumerate(labels):
            var = tk.BooleanVar(value=(i in current_days))
            self.notify_days_vars.append(var)
            ttk.Checkbutton(days_frame, text=lbl, variable=var).pack(side="left")

        ttk.Label(frm, text="Время (чч:мм)").grid(row=12, column=0, sticky="w", pady=(4, 0))
        self.notify_time_var = tk.StringVar(value=self.settings.get("notify_time") or "09:00")
        ttk.Entry(frm, textvariable=self.notify_time_var, width=10).grid(row=12, column=1, sticky="w")

        # Sound
        ttk.Separator(frm).grid(row=13, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(frm, text="Звук уведомления (Windows)").grid(row=14, column=0, sticky="w")
        self.notify_sound_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_sound_enabled", True)))
        ttk.Checkbutton(frm, text="Включить звук", variable=self.notify_sound_enabled_var).grid(row=14, column=1, sticky="w")

        ttk.Label(frm, text="Режим звука").grid(row=15, column=0, sticky="w", pady=(4, 0))
        self.notify_sound_mode_var = tk.StringVar(value=self.settings.get("notify_sound_mode") or "alias")
        mode_row = ttk.Frame(frm)
        mode_row.grid(row=15, column=1, sticky="w")
        ttk.Radiobutton(mode_row, text="Системный", value="alias", variable=self.notify_sound_mode_var).pack(side="left")
        ttk.Radiobutton(mode_row, text="Файл WAV", value="file", variable=self.notify_sound_mode_var).pack(side="left", padx=(8, 0))

        ttk.Label(frm, text="Системный звук").grid(row=16, column=0, sticky="w", pady=(4, 0))
        self.sound_alias_combo = ttk.Combobox(frm, values=["SystemAsterisk","SystemExclamation","SystemDefault","SystemHand","SystemQuestion"], state="readonly")
        try:
            self.sound_alias_combo.set(self.settings.get("notify_sound_alias") or "SystemAsterisk")
        except Exception:
            pass
        self.sound_alias_combo.grid(row=16, column=1, sticky="w")

        ttk.Label(frm, text="Файл WAV").grid(row=17, column=0, sticky="w", pady=(4, 0))
        self.notify_sound_file_var = tk.StringVar(value=self.settings.get("notify_sound_file") or "")
        file_row = ttk.Frame(frm)
        file_row.grid(row=17, column=1, sticky="ew")
        file_row.columnconfigure(0, weight=1)
        ttk.Entry(file_row, textvariable=self.notify_sound_file_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(file_row, text="Обзор…", command=self._choose_sound_file).grid(row=0, column=1, padx=(8, 0))

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=18, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Применить", command=self._apply).pack(side="right")
        ttk.Button(btns, text="Сохранить", command=self._save).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Закрыть", command=self._close).pack(side="right", padx=(8, 0))

        # Resize min size
        try:
            self.update_idletasks()
            self.minsize(780, 520)
        except Exception:
            pass

        self._on_close = on_close

        # Enable/disable fields by mode
        self._update_sound_controls()
        try:
            self.notify_sound_mode_var.trace_add("write", lambda *_: self._update_sound_controls())
        except Exception:
            pass

    def _update_sound_controls(self):
        mode = self.notify_sound_mode_var.get()
        try:
            self.sound_alias_combo.configure(state=("readonly" if mode == "alias" else "disabled"))
        except Exception:
            pass
        # file fields
        state = ("normal" if mode == "file" else "disabled")
        try:
            # find entry from row (grid slaves)
            # rely on variable-based enable/disable is sufficient in most cases
            pass
        except Exception:
            pass

    def _choose_export(self):
        path = filedialog.askdirectory(title="Выберите папку экспорта")
        if path:
            self.export_var.set(path)

    def _choose_sound_file(self):
        path = filedialog.askopenfilename(title="Выберите WAV файл", filetypes=[("WAV files","*.wav;*.wave"), ("Все файлы", "*.*")])
        if path:
            self.notify_sound_file_var.set(path)

    def _apply(self):
        # apply into master settings (in-memory)
        s = self._collect()
        try:
            self.master.app_settings = s
        except Exception:
            pass
        messagebox.showinfo("Настройки", "Изменения применены.")

    def _save(self):
        s = self._collect()
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, ensure_ascii=False, indent=2)
            try:
                self.master.app_settings = s
            except Exception:
                pass
            # Apply autostart immediately (Windows)
            try:
                if os.name == "nt":
                    from app.tray import _windows_autostart_set
                    _windows_autostart_set(bool(s.get("autostart_enabled", False)))
            except Exception:
                pass
            messagebox.showinfo("Настройки", "Сохранено.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось сохранить:\n{e}")

    def _collect(self) -> dict:
        s = dict(self.settings)
        s["ui_scale"] = float(self.ui_scale_var.get())
        s["ui_font_size"] = int(self.ui_font_size_var.get())
        s["export_path"] = self.export_var.get().strip()
        s["tray_enabled"] = bool(self.tray_enabled_var.get())
        s["minimize_to_tray"] = bool(self.minimize_to_tray_var.get())
        s["start_in_tray"] = bool(self.start_in_tray_var.get())
        s["autostart_enabled"] = bool(self.autostart_var.get())
        s["notify_enabled"] = bool(self.notify_enabled_var.get())
        s["notify_days"] = [i for i, v in enumerate(self.notify_days_vars) if bool(v.get())]
        s["notify_time"] = (self.notify_time_var.get() or "09:00").strip()
        s["notify_sound_enabled"] = bool(self.notify_sound_enabled_var.get())
        s["notify_sound_mode"] = (self.notify_sound_mode_var.get() or "alias")
        s["notify_sound_alias"] = (self.sound_alias_combo.get() or "SystemAsterisk")
        s["notify_sound_file"] = (self.notify_sound_file_var.get() or "").strip()
        return s

    def _close(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "_on_close", None)
            if callable(cb):
                cb()