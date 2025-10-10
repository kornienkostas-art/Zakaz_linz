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
            from app.views.settings import SettingsView
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

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=10, column=0, columnspan=3, sticky="e")
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

            s = self.master.app_settings
            s["export_path"] = path
            s["tray_logo_path"] = logo_path
            s["autostart_enabled"] = autostart_enabled
            s["minimize_to_tray"] = tray_enabled

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