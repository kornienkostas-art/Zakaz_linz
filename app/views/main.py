import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

from app.db import AppDB
from app.utils import set_initial_geometry, fade_transition
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
            "notify_days": [0],        # [0..6] Пн..Вс
            "notify_time": "09:00",    # HH:MM
            "notify_snooze_until": "", # epoch seconds as string
            "notify_last_ts": 0,       # epoch seconds (anti-spam window)
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

        # Setup notifications (Meridian)
        try:
            self._setup_notifications()
        except Exception:
            pass

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

        

    

    def _setup_notifications(self):
        """Периодическая проверка и показ уведомления для 'Меридиан'."""
        import time
        from datetime import datetime as dt

        def parse_time(s: str) -> tuple[int, int]:
            try:
                hh, mm = (s or "09:00").split(":")
                return max(0, min(23, int(hh))), max(0, min(59, int(mm)))
            except Exception:
                return 9, 0

        def should_notify(now: dt) -> bool:
            s = self.master.app_settings
            snooze_until = s.get("notify_snooze_until") or ""
            if snooze_until:
                try:
                    if time.time() < float(snooze_until):
                        return False
                except Exception:
                    s["notify_snooze_until"] = ""
            days = s.get("notify_days") or [0]
            try:
                days = [int(d) for d in days]
            except Exception:
                days = [0]
            hh, mm = parse_time(s.get("notify_time", "09:00"))
            if now.weekday() not in days:
                return False
            # Fire once when time passed
            import datetime as _dt
            scheduled = _dt.datetime(now.year, now.month, now.day, hh, mm).timestamp()
            if time.time() + 1 < scheduled:
                return False
            # Anti-spam: 10 min window
            last_ts = float(s.get("notify_last_ts") or 0)
            if last_ts and (time.time() - last_ts) < 600:
                return False
            return True

        def show_dialog():
            # Gather pending
            db = getattr(self.master, "db", None)
            if not db:
                return
            try:
                orders = db.list_meridian_orders()
            except Exception:
                orders = []
            pending = [o for o in orders if (o.get("status", "") or "").strip() == "Не заказан"]
            if not pending:
                return

            # Sound
            try:
                import os
                if os.name == "nt":
                    import winsound
                    # Play custom WAV if provided, else Beep
                    wav_path = (self.master.app_settings.get("notify_sound_path") or "").strip()
                    if wav_path:
                        winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                        winsound.Beep(800, 180)
                        winsound.Beep(920, 180)
                else:
                    self.master.bell()
            except Exception:
                try:
                    self.master.bell()
                except Exception:
                    pass

            # Dialog
            dialog = tk.Toplevel(self.master)
            dialog.title("Напоминание: Меридиан")
            dialog.configure(bg="#f8fafc")
            dialog.transient(self.master)
            dialog.grab_set()

            frame = ttk.Frame(dialog, style="Card.TFrame", padding=16)
            frame.pack(fill="both", expand=True)
            ttk.Label(frame, text="Нужно заказать: заказы 'Меридиан'", style="Title.TLabel").pack(anchor="w")
            ttk.Label(frame, text="Есть заказы со статусом 'Не заказан'. Выберите действие.", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 8))

            btns = ttk.Frame(frame, style="Card.TFrame")
            btns.pack(fill="x", pady=(12, 0))

            def open_meridian():
                dialog.destroy()
                from app.views.orders_meridian import MeridianOrdersView
                from app.views.main import MainWindow
                MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))

            def mark_all_ordered():
                db2 = getattr(self.master, "db", None)
                if not db2:
                    return
                now_str = dt.now().strftime("%Y-%m-%d %H:%M")
                try:
                    for o in pending:
                        oid = o.get("id")
                        if oid:
                            db2.update_meridian_order(oid, {"status": "Заказан", "date": now_str})
                    messagebox.showinfo("Статус", "Статус всех 'Не заказан' изменён на 'Заказан'.")
                except Exception as e:
                    messagebox.showerror("Статус", f"Ошибка изменения статуса:\n{e}")
                finally:
                    dialog.destroy()

            import time as _t
            def snooze(mins: int):
                until = _t.time() + mins * 60
                self.master.app_settings["notify_snooze_until"] = str(until)
                try:
                    sp = os.path.join(os.getcwd(), "settings.json")
                    with open(sp, "w", encoding="utf-8") as f:
                        json.dump(self.master.app_settings, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                dialog.destroy()

            ttk.Button(btns, text="Открыть 'Заказ Меридиан'", style="Menu.TButton", command=open_meridian).pack(side="right")
            ttk.Button(btns, text="Заказано", style="Menu.TButton", command=mark_all_ordered).pack(side="right", padx=(8, 0))
            ttk.Button(btns, text="Отложить на 30 мин", style="Menu.TButton", command=lambda: snooze(30)).pack(side="right", padx=(8, 0))
            ttk.Button(btns, text="Отложить на 15 мин", style="Menu.TButton", command=lambda: snooze(15)).pack(side="right", padx=(8, 0))
            ttk.Button(btns, text="Закрыть", style="Menu.TButton", command=dialog.destroy).pack(side="right", padx=(8, 0))

            # Anti-spam mark
            self.master.app_settings["notify_last_ts"] = time.time()
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
                    show_dialog()
            finally:
                try:
                    self.master.after(60000, tick)
                except Exception:
                    pass

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

        # Notifications (Meridian)
        ttk.Label(card, text="Уведомления для заказов 'Меридиан' со статусом 'Не заказан'", style="Subtitle.TLabel").grid(row=10, column=0, sticky="w", columnspan=3)
        days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
        selected_days = self.app_settings.get("notify_days") or [0]
        self.notify_day_vars = []
        ttk.Label(card, text="Дни недели:", style="Subtitle.TLabel").grid(row=11, column=0, sticky="nw", padx=(0, 8), pady=(8, 0))
        days_frame = ttk.Frame(card, style="Card.TFrame")
        days_frame.grid(row=11, column=1, sticky="w", pady=(8, 0))
        for i, name in enumerate(days):
            var = tk.BooleanVar(value=(i in selected_days))
            self.notify_day_vars.append(var)
            ttk.Checkbutton(days_frame, text=name, variable=var).grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 12), pady=(2, 2))

        # Time controls HH:MM
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
        time_frame = ttk.Frame(card, style="Card.TFrame")
        time_frame.grid(row=12, column=1, sticky="w", pady=(8, 0))
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, increment=1, width=5, textvariable=self.notify_hour_var)
        sep_label = ttk.Label(time_frame, text=":", style="Subtitle.TLabel")
        min_spin = ttk.Spinbox(time_frame, from_=0, to=59, increment=1, width=5, textvariable=self.notify_min_var)
        preview = ttk.Label(time_frame, text=f"(Текущее: {init_h:02d}:{init_m:02d})", style="Subtitle.TLabel")
        hour_spin.pack(side="left")
        sep_label.pack(side="left", padx=(4, 4))
        min_spin.pack(side="left")
        preview.pack(side="left", padx=(12, 0))

        def _update_preview():
            try:
                h = int(self.notify_hour_var.get())
            except Exception:
                h = init_h
            try:
                m = int(self.notify_min_var.get())
            except Exception:
                m = init_m
            h = max(0, min(23, h))
            m = max(0, min(59, m))
            preview.configure(text=f"(Текущее: {h:02d}:{m:02d})")

        def _auto_parse(text: str):
            digits = "".join(ch for ch in (text or "") if ch.isdigit())
            if len(digits) in (3, 4):
                try:
                    if len(digits) == 3:
                        h = int(digits[:1]); m = int(digits[1:])
                    else:
                        h = int(digits[:2]); m = int(digits[2:])
                    h = max(0, min(23, h)); m = max(0, min(59, m))
                    self.notify_hour_var.set(h); self.notify_min_var.set(m)
                except Exception:
                    pass
            _update_preview()
        for w in (hour_spin, min_spin):
            w.bind("<FocusOut>", lambda e, wid=w: (_auto_parse(wid.get())))
            w.bind("<KeyRelease>", lambda e, wid=w: (_auto_parse(wid.get())))

        # Custom WAV sound (Windows)
        ttk.Label(card, text="Файл звука уведомления (WAV, Windows)", style="Subtitle.TLabel").grid(row=13, column=0, sticky="w", pady=(12, 0))
        self.sound_var = tk.StringVar(value=self.app_settings.get("notify_sound_path") or "")
        sound_entry = ttk.Entry(card, textvariable=self.sound_var)
        sound_entry.grid(row=14, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(card, text="Выбрать WAV…", style="Menu.TButton", command=self._browse_sound).grid(row=14, column=1, sticky="w", padx=(8, 0))

        ttk.Separator(card).grid(row=15, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=16, column=0, columnspan=3, sticky="e")
        ttk.Button(btns, text="Проверить уведомление сейчас", style="Menu.TButton", command=self._test_notify_now).pack(side="left")
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

    def _browse_sound(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Выберите WAV-файл для звука уведомления (Windows)", filetypes=[("WAV", "*.wav"), ("Все файлы", "*.*")])
        if path:
            self.sound_var.set(path)

    def _save(self):
        path = self.path_var.get().strip()
        logo_path = self.logo_var.get().strip()
        autostart_enabled = bool(self.autostart_var.get())
        tray_enabled = bool(self.tray_var.get())
        sound_path = (self.sound_var.get() or "").strip()

        if not path:
            messagebox.showinfo("Настройки", "Укажите папку для сохранения.")
            return
        try:
            if not os.path.isdir(path):
                messagebox.showinfo("Настройки", "Указанный путь не существует.")
                return

            # Collect notification settings
            selected_days = []
            for i, var in enumerate(getattr(self, "notify_day_vars", [])):
                try:
                    if bool(var.get()):
                        selected_days.append(i)
                except Exception:
                    pass
            if not selected_days:
                selected_days = [0]

            try:
                hh_i = int(self.notify_hour_var.get()); mm_i = int(self.notify_min_var.get())
            except Exception:
                hh_i, mm_i = 9, 0
            hh_i = max(0, min(23, hh_i)); mm_i = max(0, min(59, mm_i))

            s = self.master.app_settings
            s["export_path"] = path
            s["tray_logo_path"] = logo_path
            s["autostart_enabled"] = autostart_enabled
            s["minimize_to_tray"] = tray_enabled
            s["notify_days"] = selected_days
            s["notify_time"] = f"{hh_i:02d}:{mm_i:02d}"
            s["notify_sound_path"] = sound_path

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