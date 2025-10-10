import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

from app.db import AppDB
from app.utils import set_initial_geometry, fade_transition, play_notification_sound
from app.tray import _start_tray, _stop_tray, _windows_autostart_set


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=24)
        self.master = master
        self._configure_root()
        self._setup_style()
        self._build_layout()

    # Window and grid configuration
    def _configure_root(self):
        self.master.title("УссурОЧки.рф")
        set_initial_geometry(self.master, min_w=800, min_h=520)
        self.master.configure(bg="#f8fafc")  # light background

        # Init app settings with defaults and load from JSON if exists
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            default_export = desktop if os.path.isdir(desktop) else os.getcwd()
        except Exception:
            default_export = None

        defaults = {
            "export_path": default_export,
            "autostart_enabled": True,
            "minimize_to_tray": True,
            "tray_logo_path": "",
            # Notifications (Meridian)
            "notify_days": [0],         # [0=Понедельник ... 6=Воскресенье]
            "notify_time": "09:00",     # HH:MM
            "notify_snooze_minutes": 30,
            "notify_snooze_until": "",  # epoch seconds as string, empty if none
            "notify_last_date": "",     # YYYY-MM-DD when notified last
        }

        def _settings_path():
            try:
                return os.path.join(os.getcwd(), "settings.json")
            except Exception:
                return "settings.json"

        data = {}
        try:
            sp = _settings_path()
            if os.path.isfile(sp):
                with open(sp, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
        except Exception:
            data = {}
        # Merge defaults
        settings = {**defaults, **data}

        # Attach to root
        self.master.app_settings = settings

        # Apply autostart on Windows
        try:
            if os.name == "nt":
                _windows_autostart_set(bool(self.master.app_settings.get("autostart_enabled", True)))
        except Exception:
            pass

        # Init SQLite DB once and attach to root
        try:
            db_file = os.path.join(os.getcwd(), "data.db")
            self.master.db = AppDB(db_file)
        except Exception as e:
            messagebox.showerror("База данных", f"Ошибка инициализации БД:\n{e}")
            self.master.db = None

        # Handle close to minimize to tray
        def on_close():
            try:
                if bool(self.master.app_settings.get("minimize_to_tray", True)):
                    # Lazy import to avoid circulars
                    try:
                        from app.tray import pystray, Image
                    except Exception:
                        pystray = None
                        Image = None
                    if pystray is not None and Image is not None:
                        self.master.withdraw()
                        _start_tray(self.master)
                        return
                try:
                    _stop_tray(self.master)
                except Exception:
                    pass
                self.master.destroy()
            except Exception:
                try:
                    _stop_tray(self.master)
                except Exception:
                    pass
                self.master.destroy()

        self.master.protocol("WM_DELETE_WINDOW", on_close)

        # Minimize-to-tray on clicking the taskbar minimize button
        def on_unmap(event=None):
            try:
                if self.master.state() == "iconic":
                    try:
                        from app.tray import pystray, Image
                    except Exception:
                        pystray = None
                        Image = None
                    if bool(self.master.app_settings.get("minimize_to_tray", True)) and pystray is not None and Image is not None:
                        self.master.withdraw()
                        _start_tray(self.master)
            except Exception:
                pass

        try:
            self.master.bind("<Unmap>", on_unmap)
        except Exception:
            pass

        # Make the frame fill the window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)

    # Modern, readable style
    def _setup_style(self):
        self.style = ttk.Style(self.master)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # Base colors (light theme)
        bg = "#f8fafc"
        card_bg = "#ffffff"
        accent = "#3b82f6"
        text_primary = "#111827"
        text_muted = "#6b7280"
        button_bg = "#e5e7eb"
        button_hover = "#d1d5db"
        border = "#e5e7eb"

        self.style.configure(".", background=bg)
        self.style.configure("Card.TFrame", background=card_bg, borderwidth=1, relief="solid")
        self.style.configure("Title.TLabel", background=card_bg, foreground=text_primary, font=("Segoe UI", 20, "bold"))
        self.style.configure("Subtitle.TLabel", background=card_bg, foreground=text_muted, font=("Segoe UI", 11))
        self.style.configure(
            "Menu.TButton", background=button_bg, foreground=text_primary, font=("Segoe UI", 12, "bold"), padding=(16, 12), borderwidth=1
        )
        self.style.map("Menu.TButton", background=[("active", button_hover)], relief=[("pressed", "sunken"), ("!pressed", "flat")])
        accent_hover = "#2563eb"
        self.style.configure("Accent.TButton", background=accent, foreground="#ffffff", font=("Segoe UI", 12, "bold"), padding=(16, 12), borderwidth=1)
        self.style.map("Accent.TButton", background=[("active", accent_hover)], foreground=[("disabled", "#ffffff"), ("!disabled", "#ffffff")])
        self.style.configure("TSeparator", background=border)
        self.style.configure("Data.Treeview", background=card_bg, fieldbackground=card_bg, foreground=text_primary, rowheight=28, bordercolor=border, borderwidth=1)
        self.style.configure("Data.Treeview.Heading", background="#f3f4f6", foreground=text_primary, font=("Segoe UI", 11, "bold"), bordercolor=border, borderwidth=1)

    def _build_layout(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=24)
        card.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)

        title = ttk.Label(card, text="УссурОЧки.рф", style="Title.TLabel")
        subtitle = ttk.Label(card, text="Главное меню • Выберите раздел", style="Subtitle.TLabel")
        title.grid(row=0, column=0, sticky="w")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 12))
        ttk.Separator(card).grid(row=2, column=0, sticky="ew", pady=(8, 16))

        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=3, column=0, sticky="nsew")
        buttons.columnconfigure(0, weight=1)

        btn_mkl = ttk.Button(buttons, text="Заказ МКЛ", style="Menu.TButton", command=self._on_order_mkl)
        btn_meridian = ttk.Button(buttons, text="Заказ Меридиан", style="Menu.TButton", command=self._on_order_meridian)
        btn_settings = ttk.Button(buttons, text="Настройки", style="Menu.TButton", command=self._on_settings)

        btn_mkl.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        btn_meridian.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        btn_settings.grid(row=2, column=0, sticky="ew")

        footer = ttk.Label(card, text="Локальная база данных будет добавлена позже. Начинаем с меню.", style="Subtitle.TLabel")
        footer.grid(row=4, column=0, sticky="w", pady=(20, 0))

    def _setup_notifications(self):
        """Periodic check for Meridian 'Не заказан' orders and show a notification based on schedule."""
        import time
        from datetime import datetime as dt

        def parse_time_str(s: str) -> tuple[int, int]:
            try:
                parts = (s or "09:00").split(":")
                return int(parts[0]), int(parts[1])
            except Exception:
                return 9, 0

        def should_notify(now: dt) -> bool:
            s = self.master.app_settings
            # Snooze check
            snooze_until = s.get("notify_snooze_until") or ""
            if snooze_until:
                try:
                    ts = float(snooze_until)
                    if time.time() < ts:
                        return False
                except Exception:
                    s["notify_snooze_until"] = ""
            # Day/time check
            days = s.get("notify_days")
            if not days:
                legacy_day = s.get("notify_day")
                try:
                    days = [int(legacy_day)] if legacy_day is not None else [0]
                except Exception:
                    days = [0]
            try:
                days = [int(d) for d in days]
            except Exception:
                days = [0]
            hh, mm = parse_time_str(s.get("notify_time", "09:00"))
            # In Python, Monday=0..Sunday=6
            if now.weekday() not in days:
                return False
            if now.hour < hh or (now.hour == hh and now.minute < mm):
                return False
            # Avoid multiple notifications same day
            last_date = (s.get("notify_last_date") or "").strip()
            today = now.strftime("%Y-%m-%d")
            if last_date == today:
                return False
            return True

        def show_notification():
            db = getattr(self.master, "db", None)
            if not db:
                return
            try:
                orders = db.list_meridian_orders()
            except Exception:
                orders = []
            pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан" and int(o.get("notify_enabled", 1) or 1) == 1]
            if not pending:
                return

            # Play sound
            try:
                play_notification_sound(self.master)
            except Exception:
                pass

            # Build dialog
            dialog = tk.Toplevel(self.master)
            dialog.title("Напоминание: заказы Меридиан")
            dialog.configure(bg="#f8fafc")
            dialog.transient(self.master)
            dialog.grab_set()

            frame = ttk.Frame(dialog, style="Card.TFrame", padding=16)
            frame.pack(fill="both", expand=True)
            ttk.Label(frame, text="Есть заказы Меридиан со статусом 'Не заказан'", style="Title.TLabel").pack(anchor="w")
            ttk.Label(frame, text="Откройте список заказов или отложите напоминание.", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 8))

            # List
            tree = ttk.Treeview(frame, columns=("title", "date"), show="headings", style="Data.Treeview")
            tree.heading("title", text="Название", anchor="w")
            tree.heading("date", text="Дата", anchor="w")
            tree.column("title", width=380, anchor="w")
            tree.column("date", width=160, anchor="w")
            for o in pending:
                tree.insert("", "end", values=(o.get("title", ""), o.get("date", "")))
            tree.pack(fill="both", expand=True)

            btns = ttk.Frame(frame, style="Card.TFrame")
            btns.pack(fill="x", pady=(12, 0))
            def open_meridian():
                dialog.destroy()
                from app.views.orders_meridian import MeridianOrdersView
                from app.views.main import MainWindow
                MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))
            ttk.Button(btns, text="Открыть 'Заказ Меридиан'", style="Menu.TButton", command=open_meridian).pack(side="right")

            def snooze():
                minutes = int(self.master.app_settings.get("notify_snooze_minutes", 30) or 30)
                until = time.time() + minutes * 60
                self.master.app_settings["notify_snooze_until"] = str(until)
                dialog.destroy()
            ttk.Button(btns, text="Отложить", style="Menu.TButton", command=snooze).pack(side="right", padx=(8, 0))

            ttk.Button(btns, text="Закрыть", style="Menu.TButton", command=dialog.destroy).pack(side="right", padx=(8, 0))

            # Mark notified for today
            self.master.app_settings["notify_last_date"] = dt.now().strftime("%Y-%m-%d")
            try:
                sp = os.path.join(os.getcwd(), "settings.json")
                with open(sp, "w", encoding="utf-8") as f:
                    json.dump(self.master.app_settings, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        def tick():
            try:
                now = dt.now()
                if should_notify(now):
                    show_notification()
            except Exception:
                pass
            finally:
                try:
                    self.master.after(60000, tick)  # check each minute
                except Exception:
                    pass

        # Start ticking
        self.master.after(1000, tick)

    # Actions
    def _on_order_mkl(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            # Lazy import to avoid circulars
            from app.views.orders_mkl import MKLOrdersView
            MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master))
        fade_transition(self.master, swap)

    def _on_order_meridian(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            from app.views.orders_meridian import MeridianOrdersView
            MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))
        fade_transition(self.master, swap)

    def _on_settings(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            # SettingsView is defined in this module; import not required
            SettingsView(self.master, on_back=lambda: MainWindow(self.master))
        fade_transition(self.master, swap)


class SettingsView(ttk.Frame):
    """Настройки внутри главного окна с кнопкой 'Назад'."""
    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self.app_settings = getattr(master, "app_settings", {"export_path": None, "autostart_enabled": True, "minimize_to_tray": True, "tray_logo_path": ""})
        current_path = self.app_settings.get("export_path") or ""

        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Главное меню", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        header = ttk.Label(card, text="Настройки", style="Title.TLabel")
        header.grid(row=0, column=0, sticky="w", columnspan=3)
        ttk.Separator(card).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 12))

        ttk.Label(card, text="Путь сохранения экспорта (по умолчанию)", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", columnspan=3)
        self.path_var = tk.StringVar(value=current_path)
        ttk.Label(card, text="Папка:", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        entry = ttk.Entry(card, textvariable=self.path_var)
        entry.grid(row=3, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(card, text="Обзор…", style="Menu.TButton", command=self._browse_dir).grid(row=3, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Separator(card).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 12))
        self.autostart_var = tk.BooleanVar(value=bool(self.app_settings.get("autostart_enabled", True)))
        self.tray_var = tk.BooleanVar(value=bool(self.app_settings.get("minimize_to_tray", True)))
        self.logo_var = tk.StringVar(value=self.app_settings.get("tray_logo_path") or "")

        ttk.Checkbutton(card, text="Запускать с Windows", variable=self.autostart_var).grid(row=5, column=0, sticky="w")
        ttk.Checkbutton(card, text="Сворачивать в системный трей при закрытии", variable=self.tray_var).grid(row=6, column=0, sticky="w", pady=(8, 0))

        ttk.Label(card, text="Логотип для значка в трее (PNG/ICO)", style="Subtitle.TLabel").grid(row=7, column=0, sticky="w", pady=(12, 0))
        logo_entry = ttk.Entry(card, textvariable=self.logo_var)
        logo_entry.grid(row=8, column=0, sticky="ew")
        ttk.Button(card, text="Выбрать файл…", style="Menu.TButton", command=self._browse_logo).grid(row=8, column=1, sticky="w", padx=(8, 0))

        ttk.Separator(card).grid(row=9, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        # Notifications settings (Meridian)
        ttk.Label(card, text="Напоминания для заказов 'Меридиан' со статусом 'Не заказан'", style="Subtitle.TLabel").grid(row=10, column=0, sticky="w", columnspan=3)
        days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
        selected_days = self.app_settings.get("notify_days")
        if not selected_days:
            legacy_day = self.app_settings.get("notify_day")
            if legacy_day is not None:
                try:
                    selected_days = [int(legacy_day)]
                except Exception:
                    selected_days = [0]
            else:
                selected_days = [0]
        self.notify_day_vars = []
        ttk.Label(card, text="Дни недели:", style="Subtitle.TLabel").grid(row=11, column=0, sticky="nw", padx=(0, 8), pady=(8, 0))
        days_frame = ttk.Frame(card, style="Card.TFrame")
        days_frame.grid(row=11, column=1, sticky="w", pady=(8, 0))
        for i, name in enumerate(days):
            var = tk.BooleanVar(value=(i in selected_days))
            self.notify_day_vars.append(var)
            ttk.Checkbutton(days_frame, text=name, variable=var).grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 12), pady=(2, 2))

        # Time controls: hour/minute spinboxes with auto-correction
        def _split_time(s: str) -> tuple[int, int]:
            try:
                hh, mm = (s or "09:00").split(":")
                return max(0, min(23, int(hh))), max(0, min(59, int(mm)))
            except Exception:
                return 9, 0
        init_h, init_m = _split_time(self.app_settings.get("notify_time", "09:00"))
        self.notify_hour_var = tk.IntVar(value=init_h)
        self.notify_min_var = tk.IntVar(value=init_m)

        ttk.Label(card, text="Время:", style="Subtitle.TLabel").grid(row=12, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        hour_spin = ttk.Spinbox(card, from_=0, to=23, increment=1, width=5, textvariable=self.notify_hour_var)
        min_spin = ttk.Spinbox(card, from_=0, to=59, increment=1, width=5, textvariable=self.notify_min_var)
        hour_spin.grid(row=12, column=1, sticky="w", pady=(8, 0))
        ttk.Label(card, text=":", style="Subtitle.TLabel").grid(row=12, column=2, sticky="w", padx=(4, 4), pady=(8, 0))
        min_spin.grid(row=12, column=3, sticky="w", pady=(8, 0))

        def _auto_parse(text: str):
            digits = "".join(ch for ch in (text or "") if ch.isdigit())
            if len(digits) in (3, 4):
                try:
                    if len(digits) == 3:
                        h = int(digits[:1])
                        m = int(digits[1:])
                    else:
                        h = int(digits[:2])
                        m = int(digits[2:])
                    h = max(0, min(23, h))
                    m = max(0, min(59, m))
                    self.notify_hour_var.set(h)
                    self.notify_min_var.set(m)
                except Exception:
                    pass

        # Auto-correct when user types 1053 etc. in either spinbox
        hour_spin.bind("<FocusOut>", lambda e: _auto_parse(hour_spin.get()))
        min_spin.bind("<FocusOut>", lambda e: _auto_parse(min_spin.get()))

        self.notify_snooze_var = tk.IntVar(value=int(self.app_settings.get("notify_snooze_minutes", 30) or 30))
        ttk.Label(card, text="Отложить на (минут):", style="Subtitle.TLabel").grid(row=13, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Spinbox(card, from_=5, to=180, increment=5, textvariable=self.notify_snooze_var, width=8).grid(row=13, column=1, sticky="w", pady=(8, 0))

        # Hint on per-order notify
        ttk.Label(card, text="В списке 'Меридиан' для каждого заказа есть колонка 'Напоминание' и переключатель в контекстном меню.", style="Subtitle.TLabel").grid(row=14, column=0, columnspan=3, sticky="w", pady=(8, 0))

        ttk.Separator(card).grid(row=15, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=16, column=0, columnspan=3, sticky="e")
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _browse_dir(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Выберите папку для сохранения экспорта")
        if path:
            self.path_var.set(path)

    def _browse_logo(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Выберите файл логотипа (PNG/ICO)", filetypes=[("PNG/ICO", "*.png *.ico"), ("Все файлы", "*.*")])
        if path:
            self.logo_var.set(path)

    def _save(self):
        path = self.path_var.get().strip()
        logo_path = self.logo_var.get().strip()
        autostart_enabled = bool(self.autostart_var.get())
        tray_enabled = bool(self.tray_var.get())

        if not path:
            messagebox.showinfo("Настройки", "Укажите папку для сохранения.")
            return
        try:
            if not os.path.isdir(path):
                messagebox.showinfo("Настройки", "Указанный путь не существует.")
                return

            # Validate time
            tval = (self.notify_time_var.get() or "09:00").strip()
            try:
                hh, mm = tval.split(":")
                hh_i = int(hh); mm_i = int(mm)
                if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
                    raise ValueError
            except Exception:
                messagebox.showinfo("Настройки", "Время должно быть в формате HH:MM (00–23:00–59).")
                return

            # Collect selected days (multiple)
            selected_days = []
            for i, var in enumerate(getattr(self, "notify_day_vars", [])):
                try:
                    if bool(var.get()):
                        selected_days.append(i)
                except Exception:
                    pass
            if not selected_days:
                selected_days = [0]

            snooze_minutes = int(self.notify_snooze_var.get() or 30)
            if snooze_minutes < 5:
                snooze_minutes = 5

            s = self.master.app_settings
            s["export_path"] = path
            s["tray_logo_path"] = logo_path
            s["autostart_enabled"] = autostart_enabled
            s["minimize_to_tray"] = tray_enabled

            # Notification settings
            s["notify_days"] = selected_days
            s["notify_time"] = f"{hh_i:02d}:{mm_i:02d}"
            s["notify_snooze_minutes"] = snooze_minutes

            try:
                sp = os.path.join(os.getcwd(), "settings.json")
                with open(sp, "w", encoding="utf-8") as f:
                    json.dump(s, f, ensure_ascii=False, indent=2)
            except Exception as e:
                messagebox.showwarning("Настройки", f"Не удалось сохранить настройки в файл:\n{e}")

            if os.name == "nt":
                try:
                    _windows_autostart_set(autostart_enabled)
                except Exception as e:
                    messagebox.showerror("Автозапуск", f"Не удалось применить автозапуск:\n{e}")

            try:
                if getattr(self.master, "tray_icon", None):
                    _stop_tray(self.master)
                    if tray_enabled:
                        from app.tray import pystray
                        if pystray is not None:
                            _start_tray(self.master)
            except Exception:
                pass

            messagebox.showinfo("Настройки", "Сохранено.")
            self._go_back()
        except Exception as e:
            messagebox.showerror("Настройки", f"Ошибка сохранения:\n{e}")