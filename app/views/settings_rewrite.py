import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

SETTINGS_FILE = "settings.json"


class SettingsRewriteWindow(tk.Toplevel):
    """
    Полностью переписанные настройки:
    - Надёжное отдельное окно (Toplevel)
    - Простой ttk без кастомных стилей
    - Прокручиваемое содержимое (если экран маленький)
    """

    def __init__(self, master: tk.Misc, on_close=None):
        super().__init__(master)
        self.title("Настройки")
        self.geometry("920x700")
        self.minsize(780, 560)
        self.transient(master)
        self.grab_set()

        # Ссылка на словарь настроек приложения
        self.settings = getattr(master, "app_settings", {}) or {}
        self._on_close = on_close

        # Верхний контейнер с прокруткой
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Содержимое
        self._build_content(self.inner)

        # События колёсика для прокрутки
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Обработчик закрытия
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _on_mousewheel(self, event):
        try:
            delta = -1 * int(event.delta / 120)
            self.canvas.yview_scroll(delta, "units")
        except Exception:
            pass

    def _build_content(self, root):
        row = 0

        header = ttk.Label(root, text="Общие", font=("Segoe UI", 12, "bold"))
        header.grid(row=row, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6))
        row += 1

        # UI scale
        ttk.Label(root, text="Масштаб интерфейса").grid(row=row, column=0, sticky="w", padx=12)
        self.ui_scale_var = tk.DoubleVar(value=float(self.settings.get("ui_scale", 1.25)))
        ttk.Spinbox(root, from_=0.8, to=2.0, increment=0.05, textvariable=self.ui_scale_var, width=10).grid(row=row, column=1, sticky="w", padx=12)
        row += 1

        # Font size
        ttk.Label(root, text="Размер шрифта").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 0))
        self.ui_font_size_var = tk.IntVar(value=int(self.settings.get("ui_font_size", 17)))
        ttk.Spinbox(root, from_=12, to=28, textvariable=self.ui_font_size_var, width=10).grid(row=row, column=1, sticky="w", padx=12, pady=(6, 0))
        row += 1

        # Export path
        ttk.Label(root, text="Папка экспорта TXT").grid(row=row, column=0, sticky="w", padx=12, pady=(12, 0))
        self.export_var = tk.StringVar(value=(self.settings.get("export_path") or ""))
        exp_row = ttk.Frame(root)
        exp_row.grid(row=row, column=1, sticky="ew", padx=12, pady=(12, 0))
        exp_row.columnconfigure(0, weight=1)
        ttk.Entry(exp_row, textvariable=self.export_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(exp_row, text="Обзор…", command=self._choose_export_path).grid(row=0, column=1, padx=(8, 0))
        row += 1

        ttk.Separator(root).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 12))
        row += 1

        # Tray / autostart
        ttk.Label(root, text="Трей и автозапуск", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.tray_enabled_var = tk.BooleanVar(value=bool(self.settings.get("tray_enabled", True)))
        ttk.Checkbutton(root, text="Включить системный трей", variable=self.tray_enabled_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.minimize_to_tray_var = tk.BooleanVar(value=bool(self.settings.get("minimize_to_tray", True)))
        ttk.Checkbutton(root, text="Сворачивать в трей (закрыть/свернуть)", variable=self.minimize_to_tray_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.start_in_tray_var = tk.BooleanVar(value=bool(self.settings.get("start_in_tray", True)))
        ttk.Checkbutton(root, text="Запускать в трее (при старте)", variable=self.start_in_tray_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.autostart_var = tk.BooleanVar(value=bool(self.settings.get("autostart_enabled", False)))
        ttk.Checkbutton(root, text="Автозапуск с Windows", variable=self.autostart_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        ttk.Separator(root).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 12))
        row += 1

        # Meridian notifications
        ttk.Label(root, text="Уведомления — Меридиан (статус «Не заказан»)", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.notify_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_enabled", False)))
        ttk.Checkbutton(root, text="Включить уведомления", variable=self.notify_enabled_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        ttk.Label(root, text="Дни недели (Пн=0…Вс=6)").grid(row=row, column=0, sticky="w", padx=12)
        days_row = ttk.Frame(root)
        days_row.grid(row=row, column=1, sticky="w", padx=12)
        self.notify_days_vars = []
        labels = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
        current_days = set(self.settings.get("notify_days") or [])
        for i, lbl in enumerate(labels):
            var = tk.BooleanVar(value=(i in current_days))
            self.notify_days_vars.append(var)
            ttk.Checkbutton(days_row, text=lbl, variable=var).pack(side="left", padx=(0, 6))
        row += 1

        ttk.Label(root, text="Время (чч:мм)").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 0))
        self.notify_time_var = tk.StringVar(value=(self.settings.get("notify_time") or "09:00"))
        ttk.Entry(root, textvariable=self.notify_time_var, width=10).grid(row=row, column=1, sticky="w", padx=12, pady=(6, 0))
        row += 1

        

        ttk.Separator(root).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 12))
        row += 1

        # MKL notifications
        ttk.Label(root, text="Уведомления — МКЛ (статус «Не заказан», по возрасту)", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.mkl_notify_enabled_var = tk.BooleanVar(value=bool(self.settings.get("mkl_notify_enabled", False)))
        ttk.Checkbutton(root, text="Включить уведомления", variable=self.mkl_notify_enabled_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        ttk.Label(root, text="Напоминать через (дней)").grid(row=row, column=0, sticky="w", padx=12)
        self.mkl_notify_days_var = tk.IntVar(value=int(self.settings.get("mkl_notify_after_days", 3)))
        ttk.Spinbox(root, from_=1, to=60, textvariable=self.mkl_notify_days_var, width=10).grid(row=row, column=1, sticky="w", padx=12)
        row += 1

        ttk.Label(root, text="Время (чч:мм)").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 0))
        self.mkl_notify_time_var = tk.StringVar(value=(self.settings.get("mkl_notify_time") or "09:00"))
        ttk.Entry(root, textvariable=self.mkl_notify_time_var, width=10).grid(row=row, column=1, sticky="w", padx=12, pady=(6, 0))
        row += 1

        # Test MKL
        ttk.Button(root, text="Проверить уведомление МКЛ", command=self._test_mkl).grid(row=row, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 0))
        row += 1

        ttk.Separator(root).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 12))
        row += 1

        # Sound (shared)
        ttk.Label(root, text="Звук уведомления (общий для МКЛ и Меридиан)", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        self.notify_sound_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_sound_enabled", True)))
        ttk.Checkbutton(root, text="Включить звук (Windows)", variable=self.notify_sound_enabled_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=12)
        row += 1

        ttk.Label(root, text="Режим звука").grid(row=row, column=0, sticky="w", padx=12)
        self.notify_sound_mode_var = tk.StringVar(value=(self.settings.get("notify_sound_mode") or "alias"))
        mode_row = ttk.Frame(root)
        mode_row.grid(row=row, column=1, sticky="w", padx=12)
        ttk.Radiobutton(mode_row, text="Системный", value="alias", variable=self.notify_sound_mode_var).pack(side="left")
        ttk.Radiobutton(mode_row, text="Файл WAV", value="file", variable=self.notify_sound_mode_var).pack(side="left", padx=(8, 0))
        row += 1

        ttk.Label(root, text="Системный звук").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 0))
        self.notify_sound_alias_var = tk.StringVar(value=(self.settings.get("notify_sound_alias") or "SystemAsterisk"))
        alias_combo = ttk.Combobox(root, values=["SystemAsterisk","SystemExclamation","SystemDefault","SystemHand","SystemQuestion"], state="readonly")
        alias_combo.set(self.notify_sound_alias_var.get())
        alias_combo.grid(row=row, column=1, sticky="w", padx=12, pady=(6, 0))
        self._alias_combo = alias_combo
        row += 1

        ttk.Label(root, text="Файл WAV").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 0))
        self.notify_sound_file_var = tk.StringVar(value=(self.settings.get("notify_sound_file") or ""))
        file_row = ttk.Frame(root)
        file_row.grid(row=row, column=1, sticky="ew", padx=12, pady=(6, 0))
        file_row.columnconfigure(0, weight=1)
        file_entry = ttk.Entry(file_row, textvariable=self.notify_sound_file_var)
        file_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(file_row, text="Обзор…", command=self._choose_sound_file).grid(row=0, column=1, padx=(8, 0))
        row += 1

        # Enable/disable controls by mode
        def _update_sound_controls(*_):
            mode = self.notify_sound_mode_var.get()
            try:
                alias_combo.configure(state=("readonly" if mode == "alias" else "disabled"))
            except Exception:
                pass
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

        ttk.Separator(root).grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 12))
        row += 1

        # Action buttons
        actions = ttk.Frame(root)
        actions.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        ttk.Button(actions, text="Сохранить", command=self._save).pack(side="right")
        ttk.Button(actions, text="Применить", command=self._apply).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Закрыть", command=self._close).pack(side="right", padx=(8, 0))

        # Expand grid columns
        for c in (0, 1):
            root.grid_columnconfigure(c, weight=1)

    def _choose_export_path(self):
        path = filedialog.askdirectory(title="Выберите папку экспорта")
        if path:
            self.export_var.set(path)

    def _choose_sound_file(self):
        path = filedialog.askopenfilename(title="Выберите WAV файл", filetypes=[("WAV files","*.wav;*.wave"),("Все файлы","*.*")])
        if path:
            self.notify_sound_file_var.set(path)

    def _collect(self) -> dict:
        s = dict(self.settings)
        # Base
        s["ui_scale"] = float(self.ui_scale_var.get())
        s["ui_font_size"] = int(self.ui_font_size_var.get())
        s["export_path"] = self.export_var.get().strip()
        # Tray
        s["tray_enabled"] = bool(self.tray_enabled_var.get())
        s["minimize_to_tray"] = bool(self.minimize_to_tray_var.get())
        s["start_in_tray"] = bool(self.start_in_tray_var.get())
        s["autostart_enabled"] = bool(self.autostart_var.get())
        # Meridian
        s["notify_enabled"] = bool(self.notify_enabled_var.get())
        s["notify_days"] = [i for i, v in enumerate(self.notify_days_vars) if bool(v.get())]
        s["notify_time"] = (self.notify_time_var.get() or "09:00").strip()
        # MKL
        s["mkl_notify_enabled"] = bool(self.mkl_notify_enabled_var.get())
        s["mkl_notify_after_days"] = int(self.mkl_notify_days_var.get())
        s["mkl_notify_time"] = (self.mkl_notify_time_var.get() or "09:00").strip()
        # Sound
        s["notify_sound_enabled"] = bool(self.notify_sound_enabled_var.get())
        s["notify_sound_mode"] = (self.notify_sound_mode_var.get() or "alias")
        # alias from combo
        try:
            s["notify_sound_alias"] = self._alias_combo.get() or "SystemAsterisk"
        except Exception:
            s["notify_sound_alias"] = self.settings.get("notify_sound_alias") or "SystemAsterisk"
        s["notify_sound_file"] = (self.notify_sound_file_var.get() or "").strip()
        return s

    def _apply(self):
        s = self._collect()
        # apply to root immediately
        try:
            self.master.app_settings = s
        except Exception:
            pass
        # scaling and fonts
        try:
            self.master.tk.call("tk", "scaling", float(s.get("ui_scale", 1.25)))
        except Exception:
            pass
        messagebox.showinfo("Настройки", "Изменения применены.")

    def _save(self):
        s = self._collect()
        # persist
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, ensure_ascii=False, indent=2)
            # autostart on Windows
            try:
                if os.name == "nt":
                    from app.tray import _windows_autostart_set
                    _windows_autostart_set(bool(s.get("autostart_enabled", False)))
            except Exception:
                pass
            # update root
            try:
                self.master.app_settings = s
            except Exception:
                pass
            messagebox.showinfo("Настройки", "Сохранено.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось сохранить:\n{e}")

    def _close(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "_on_close", None)
            if callable(cb):
                try:
                    cb()
                except Exception:
                    pass

    # Test notification buttons
    def _test_meridian(self):
        try:
            db = getattr(self.master, "db", None)
            orders = db.list_meridian_orders() if db else []
            pending = [o for o in orders if (o.get("status","") or "").strip() == "Не заказан"]
            if not pending:
                messagebox.showinfo("Уведомление", "Нет заказов Меридиан со статусом 'Не заказан'.")
                return
            from app.views.notify import show_meridian_notification
            def on_snooze(m): messagebox.showinfo("Уведомление", f"Отложено на {m} мин.")
            def on_mark(): 
                try:
                    for o in pending: db.update_meridian_order(o["id"], {"status":"Заказан"})
                    messagebox.showinfo("Уведомление", "Статус заказов изменён на 'Заказан'.")
                except Exception as e:
                    messagebox.showerror("Уведомление", f"Не удалось изменить статус:\n{e}")
            show_meridian_notification(self.master, pending, on_snooze=on_snooze, on_mark_ordered=on_mark)
        except Exception as e:
            messagebox.showerror("Уведомление", f"Ошибка проверки:\n{e}")

    def _test_mkl(self):
        try:
            from datetime import datetime, timedelta
            db = getattr(self.master, "db", None)
            orders = db.list_mkl_orders() if db else []
            days = int(self.mkl_notify_days_var.get() or 3)
            threshold = datetime.now() - timedelta(days=max(0, days))
            aged = []
            for o in orders:
                try:
                    if (o.get("status","") or "").strip() != "Не заказан": continue
                    ds = (o.get("date","") or "").strip()
                    dt = None
                    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
                        try:
                            dt = datetime.strptime(ds, fmt); break
                        except Exception: continue
                    if dt and dt <= threshold: aged.append(o)
                except Exception: continue
            if not aged:
                messagebox.showinfo("Уведомление МКЛ", "Нет просроченных заказов МКЛ со статусом 'Не заказан'.")
                return
            from app.views.notify import show_mkl_notification
            def on_snooze_days(d): messagebox.showinfo("Уведомление МКЛ", f"Отложено на {d} дн.")
            def on_mark():
                try:
                    for o in aged: db.update_mkl_order(o["id"], {"status":"Заказан"})
                    messagebox.showinfo("Уведомление МКЛ", "Статус заказов изменён на 'Заказан'.")
                except Exception as e:
                    messagebox.showerror("Уведомление МКЛ", f"Не удалось изменить статус:\n{e}")
            show_mkl_notification(self.master, aged, on_snooze_days=on_snooze_days, on_mark_ordered=on_mark)
        except Exception as e:
            messagebox.showerror("Уведомление МКЛ", f"Ошибка проверки:\n{e}")