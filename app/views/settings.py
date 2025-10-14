import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from app.utils import set_initial_geometry


class SettingsView(ttk.Frame):
    """Экран настроек: масштаб интерфейса, папка экспорта, автозапуск и трей."""

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back

        # Attach settings dict from root
        self.settings = getattr(self.master, "app_settings", {}) or {}

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Back.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        # UI scale
        ttk.Label(card, text="Масштаб интерфейса (tk scaling)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.ui_scale_var = tk.DoubleVar(value=float(self.settings.get("ui_scale", 1.25)))
        self.ui_scale_spin = ttk.Spinbox(card, from_=0.8, to=2.0, increment=0.05, textvariable=self.ui_scale_var, width=10)
        self.ui_scale_spin.grid(row=0, column=1, sticky="w", padx=(8, 0))

        # Export path
        ttk.Label(card, text="Папка экспорта TXT", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 4))
        self.export_var = tk.StringVar(value=(self.settings.get("export_path") or ""))
        export_row = ttk.Frame(card, style="Card.TFrame")
        export_row.grid(row=1, column=1, sticky="ew")
        entry = ttk.Entry(export_row, textvariable=self.export_var)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(export_row, text="Обзор…", command=self._choose_export_path).pack(side="left", padx=(8, 0))

        ttk.Separator(card).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Global font size
        ttk.Label(card, text="Размер шрифта (по всему приложению)", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w")
        self.ui_font_size_var = tk.IntVar(value=int(self.settings.get("ui_font_size", 17)))
        ttk.Spinbox(card, from_=12, to=28, textvariable=self.ui_font_size_var, width=10).grid(row=3, column=1, sticky="w", padx=(8, 0))

        ttk.Separator(card).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Tray and autostart settings
        ttk.Label(card, text="Трей и автозапуск", style="Title.TLabel").grid(row=5, column=0, sticky="w")
        self.tray_enabled_var = tk.BooleanVar(value=bool(self.settings.get("tray_enabled", True)))
        ttk.Checkbutton(card, text="Включить системный трей", variable=self.tray_enabled_var).grid(row=5, column=1, sticky="w")

        self.minimize_to_tray_var = tk.BooleanVar(value=bool(self.settings.get("minimize_to_tray", True)))
        ttk.Checkbutton(card, text="Сворачивать в трей (закрыть/свернуть)", variable=self.minimize_to_tray_var).grid(row=6, column=1, sticky="w")

        self.start_in_tray_var = tk.BooleanVar(value=bool(self.settings.get("start_in_tray", True)))
        ttk.Checkbutton(card, text="Запускать в трее (при старте)", variable=self.start_in_tray_var).grid(row=7, column=1, sticky="w")

        self.autostart_var = tk.BooleanVar(value=bool(self.settings.get("autostart_enabled", False)))
        ttk.Checkbutton(card, text="Автозапуск с Windows", variable=self.autostart_var).grid(row=8, column=1, sticky="w")

        ttk.Separator(card).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Meridian notifications
        ttk.Label(card, text="Уведомления по заказам Меридиан (статус 'Не заказан')", style="Title.TLabel").grid(row=10, column=0, sticky="w")
        self.notify_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_enabled", False)))
        ttk.Checkbutton(card, text="Включить уведомления", variable=self.notify_enabled_var).grid(row=10, column=1, sticky="w")

        ttk.Label(card, text="Дни недели", style="Subtitle.TLabel").grid(row=11, column=0, sticky="w", pady=(8, 0))
        days_frame = ttk.Frame(card, style="Card.TFrame")
        days_frame.grid(row=11, column=1, sticky="w")
        self.notify_days_vars = []
        days_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        current_days = set(self.settings.get("notify_days") or [])
        for i, lbl in enumerate(days_labels):
            var = tk.BooleanVar(value=(i in current_days))
            self.notify_days_vars.append(var)
            ttk.Checkbutton(days_frame, text=lbl, variable=var).pack(side="left", padx=(0, 6))

        ttk.Label(card, text="Время (чч:мм)", style="Subtitle.TLabel").grid(row=12, column=0, sticky="w", pady=(8, 0))
        self.notify_time_var = tk.StringVar(value=(self.settings.get("notify_time") or "09:00"))
        ttk.Entry(card, textvariable=self.notify_time_var, width=10).grid(row=12, column=1, sticky="w")

        ttk.Separator(card).grid(row=13, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Sound enable
        ttk.Label(card, text="Звук уведомления", style="Subtitle.TLabel").grid(row=14, column=0, sticky="w", pady=(8, 0))
        self.notify_sound_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_sound_enabled", True)))
        ttk.Checkbutton(card, text="Включить звук (Windows)", variable=self.notify_sound_enabled_var).grid(row=14, column=1, sticky="w")

        ttk.Label(card, text="Тип звука (Windows)", style="Subtitle.TLabel").grid(row=15, column=0, sticky="w", pady=(8, 0))
        # Map display labels to winsound aliases
        sound_options = [
            ("Стандартный", "SystemAsterisk"),
            ("Предупреждение", "SystemExclamation"),
            ("Информация", "SystemDefault"),
            ("Ошибка", "SystemHand"),
            ("Вопрос", "SystemQuestion"),
        ]
        self.notify_sound_alias_var = tk.StringVar(value=(self.settings.get("notify_sound_alias") or "SystemAsterisk"))
        sound_combo = ttk.Combobox(card, values=[opt[0] for opt in sound_options], state="readonly")
        # Set initial selection by alias
        try:
            alias = self.notify_sound_alias_var.get()
            for i, (_, a) in enumerate(sound_options):
                if a == alias:
                    sound_combo.current(i)
                    break
        except Exception:
            pass
        sound_combo.grid(row=15, column=1, sticky="w")

        # Sound mode: system alias vs custom WAV file
        ttk.Label(card, text="Режим звука", style="Subtitle.TLabel").grid(row=16, column=0, sticky="w", pady=(8, 0))
        self.notify_sound_mode_var = tk.StringVar(value=(self.settings.get("notify_sound_mode") or "alias"))
        mode_row = ttk.Frame(card, style="Card.TFrame")
        mode_row.grid(row=16, column=1, sticky="w")
        ttk.Radiobutton(mode_row, text="Системный звук", value="alias", variable=self.notify_sound_mode_var).pack(side="left")
        ttk.Radiobutton(mode_row, text="Файл WAV", value="file", variable=self.notify_sound_mode_var).pack(side="left", padx=(8, 0))

        ttk.Label(card, text="Файл WAV", style="Subtitle.TLabel").grid(row=17, column=0, sticky="w", pady=(8, 0))
        self.notify_sound_file_var = tk.StringVar(value=(self.settings.get("notify_sound_file") or ""))
        file_row = ttk.Frame(card, style="Card.TFrame")
        file_row.grid(row=17, column=1, sticky="ew")
        file_entry = ttk.Entry(file_row, textvariable=self.notify_sound_file_var)
        file_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(file_row, text="Обзор…", command=self._choose_sound_file).pack(side="left", padx=(8, 0))

        # Enable/disable controls based on mode
        def _update_sound_controls(*args):
            mode = self.notify_sound_mode_var.get()
            # alias combo enabled only in alias mode
            try:
                sound_combo.configure(state=("readonly" if mode == "alias" else "disabled"))
            except Exception:
                pass
            # file entry/browse enabled only in file mode
            try:
                state = ("normal" if mode == "file" else "disabled")
                file_entry.configure(state=state)
            except Exception:
                pass
        try:
            self.notify_sound_mode_var.trace_add("write", _update_sound_controls)
        except Exception:
            pass
        _update_sound_controls()

        ttk.Separator(card).grid(row=18, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Actions
        actions = ttk.Frame(card, style="Card.TFrame")
        actions.grid(row=19, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(actions, text="Применить", style="Menu.TButton", command=self._apply).pack(side="right", padx=(8, 0))

        # Helper to map selected label to alias during save/apply
        self._sound_options = sound_options
        self._sound_combo = sound_combo

    def _choose_export_path(self):
        path = filedialog.askdirectory(title="Выберите папку экспорта")
        if path:
            self.export_var.set(path)

    def _choose_sound_file(self):
        path = filedialog.askopenfilename(
            title="Выберите WAV файл",
            filetypes=[("WAV files", "*.wav;*.wave"), ("Все файлы", "*.*")],
        )
        if path:
            self.notify_sound_file_var.set(path)

    def _save(self):
        data = dict(self.settings)
        data["ui_scale"] = float(self.ui_scale_var.get())
        data["export_path"] = self.export_var.get().strip()
        data["ui_font_size"] = int(self.ui_font_size_var.get())
        data["tray_enabled"] = bool(self.tray_enabled_var.get())
        data["minimize_to_tray"] = bool(self.minimize_to_tray_var.get())
        data["start_in_tray"] = bool(self.start_in_tray_var.get())
        data["autostart_enabled"] = bool(self.autostart_var.get())
        # Notifications
        data["notify_enabled"] = bool(self.notify_enabled_var.get())
        data["notify_days"] = [i for i, v in enumerate(self.notify_days_vars) if bool(v.get())]
        data["notify_time"] = (self.notify_time_var.get() or "09:00").strip()
        data["notify_sound_enabled"] = bool(self.notify_sound_enabled_var.get())
        data["notify_sound_mode"] = (self.notify_sound_mode_var.get() or "alias")
        data["notify_sound_file"] = (self.notify_sound_file_var.get() or "").strip()
        # Map selection to alias
        try:
            sel = self._sound_combo.get()
            for label, alias in self._sound_options:
                if label == sel:
                    data["notify_sound_alias"] = alias
                    break
            else:
                data["notify_sound_alias"] = (self.settings.get("notify_sound_alias") or "SystemAsterisk")
        except Exception:
            data["notify_sound_alias"] = (self.settings.get("notify_sound_alias") or "SystemAsterisk")

        # Persist to settings.json at project root
        try:
            import json
            SETTINGS_FILE = "settings.json"
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Update root
            self.master.app_settings = data

            # Apply autostart setting immediately (Windows)
            try:
                from app.tray import _windows_autostart_set
                if os.name == "nt":
                    _windows_autostart_set(bool(self.autostart_var.get()))
            except Exception:
                pass

            messagebox.showinfo("Настройки", "Сохранено.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось сохранить:\n{e}")

    def _apply(self):
        # Apply scaling and global font size immediately
        try:
            scale = float(self.ui_scale_var.get())
            self.master.tk.call("tk", "scaling", scale)
            self.settings["ui_scale"] = scale

            size = int(self.ui_font_size_var.get())
            self.settings["ui_font_size"] = size

            # Apply fonts via helper defined in main.py
            try:
                from tkinter import ttk as _ttk
                from tkinter import font as _tkfont
                # Update Tk named fonts
                for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont"):
                    try:
                        f = _tkfont.nametofont(name)
                        f.configure(size=size)
                        f.configure(weight="normal")
                    except Exception:
                        pass
                # Treeview row height and headings; buttons and labels fonts
                try:
                    style = _ttk.Style(self.master)
                    style.configure("Treeview", rowheight=size + 12)
                    style.configure("Treeview.Heading", font=(None, size))
                    style.configure("TButton", font=(None, size))
                    style.configure("TLabel", font=(None, size))
                except Exception:
                    pass
            except Exception:
                pass

            # Update tray/autostart settings in-memory
            self.settings["tray_enabled"] = bool(self.tray_enabled_var.get())
            self.settings["minimize_to_tray"] = bool(self.minimize_to_tray_var.get())
            self.settings["start_in_tray"] = bool(self.start_in_tray_var.get())
            self.settings["autostart_enabled"] = bool(self.autostart_var.get())

            # Notifications
            self.settings["notify_enabled"] = bool(self.notify_enabled_var.get())
            self.settings["notify_days"] = [i for i, v in enumerate(self.notify_days_vars) if bool(v.get())]
            self.settings["notify_time"] = (self.notify_time_var.get() or "09:00").strip()
            self.settings["notify_sound_enabled"] = bool(self.notify_sound_enabled_var.get())
            self.settings["notify_sound_mode"] = (self.notify_sound_mode_var.get() or "alias")
            self.settings["notify_sound_file"] = (self.notify_sound_file_var.get() or "").strip()
            # Map selection to alias
            try:
                sel = self._sound_combo.get()
                for label, alias in self._sound_options:
                    if label == sel:
                        self.settings["notify_sound_alias"] = alias
                        break
                else:
                    self.settings["notify_sound_alias"] = (self.settings.get("notify_sound_alias") or "SystemAsterisk")
            except Exception:
                self.settings["notify_sound_alias"] = (self.settings.get("notify_sound_alias") or "SystemAsterisk")
            self.settings["notify_days"] = [i for i, v in enumerate(self.notify_days_vars) if bool(v.get())]
            self.settings["notify_time"] = (self.notify_time_var.get() or "09:00").strip()
            self.settings["notify_sound_enabled"] = bool(self.notify_sound_enabled_var.get())
            # Map selection to alias
            try:
                sel = self._sound_combo.get()
                for label, alias in self._sound_options:
                    if label == sel:
                        self.settings["notify_sound_alias"] = alias
                        break
                else:
                    self
            # Apply autostart immediately (Windows)
            try:
                from app.tray import _windows_autostart_set
                if os.name == "nt":
                    _windows_autostart_set(bool(self.autostart_var.get()))
            except Exception:
                pass

            messagebox.showinfo("Настройки", "Изменения применены.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось применить:\n{e}")

    def _test_notify(self):
        try:
            # Collect pending meridian 'Не заказан' orders
            db = getattr(self.master, "db", None)
            orders = db.list_meridian_orders() if db else []
            pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан"]
            if not pending:
                messagebox.showinfo("Уведомление", "Нет заказов Меридиан со статусом 'Не заказан'.")
                return
            from app.views.notify import show_meridian_notification
            def on_snooze(minutes):
                messagebox.showinfo("Уведомление", f"Отложено на {minutes} минут.")
            def on_mark_ordered():
                try:
                    for o in pending:
                        db.update_meridian_order(o["id"], {"status": "Заказан"})
                    messagebox.showinfo("Уведомление", "Статус заказов изменён на 'Заказан'.")
                except Exception as e:
                    messagebox.showerror("Уведомление", f"Не удалось изменить статус:\n{e}")
            show_meridian_notification(self.master, pending, on_snooze=on_snooze, on_mark_ordered=on_mark_ordered)
        except Exception as e:
            messagebox.showerror("Уведомление", f"Ошибка проверки:\n{e}")

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()