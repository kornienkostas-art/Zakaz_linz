import tkinter as tk
from tkinter import ttk, filedialog, font

from app.db import AppDB
from app.utils import set_initial_geometry, fade_transition


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("УссурОЧки.рф — Заказ линз")

        # Geometry
        set_initial_geometry(self.root, min_w=1100, min_h=760)

        # Ensure DB exists on root (created in main.py), but allow fallback
        if not hasattr(self.root, "db") or not isinstance(self.root.db, AppDB):
            self.root.db = AppDB("data.db")

        # Load settings dict (set in main.py)
        self.app_settings = getattr(self.root, "app_settings", {})

        self._build_ui()
        self._refresh_stats()

    def _build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Configure large button style for better visibility
        try:
            style = ttk.Style(self.root)
            # Base font bold, aligned with global default size 15
            big_font = ("Segoe UI", 15, "bold")
            # Fallback: if Segoe UI not available, Tk will substitute
            style.configure("Big.TButton", font=big_font, padding=(24, 16))
        except Exception:
            pass

        # Main menu - vertical stack: MKL, Meridian, Prices, Astig Calc, Settings
        menu = ttk.Frame(container)
        menu.pack(fill="both", expand=True, padx=48, pady=48)

        btn_opts = dict(width=30, style="Big.TButton")
        ttk.Button(menu, text="Заказы МКЛ", command=self._open_mkl, **btn_opts).pack(fill="x", pady=10)
        ttk.Button(menu, text="Заказы Меридиан", command=self._open_meridian, **btn_opts).pack(fill="x", pady=10)
        ttk.Button(menu, text="Прайсы", command=self._open_prices, **btn_opts).pack(fill="x", pady=10)
        ttk.Button(menu, text="Пересчёт астигматических линз", command=self._open_astig, **btn_opts).pack(fill="x", pady=10)
        ttk.Button(menu, text="Настройки…", command=self._open_settings, **btn_opts).pack(fill="x", pady=10)

    def _refresh_stats(self):
        # На главном экране счётчики скрыты; оставим заглушку для совместимости.
        try:
            _ = self.root.db
        except Exception:
            pass

    # Navigation
    def _open_clients(self):
        def swap():
            self._clear_root_frames()
            from app.views.clients import ClientsView
            ClientsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_products(self):
        def swap():
            self._clear_root_frames()
            from app.views.products import ProductsView
            ProductsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_mkl(self):
        def swap():
            self._clear_root_frames()
            from app.views.orders_mkl import MKLOrdersView
            MKLOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_meridian(self):
        def swap():
            self._clear_root_frames()
            from app.views.orders_meridian import MeridianOrdersView
            MeridianOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_prices(self):
        def swap():
            self._clear_root_frames()
            from app.views.prices import PricesView
            PricesView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_astig(self):
        def swap():
            self._clear_root_frames()
            from app.views.astig_calc import AstigCalcView
            AstigCalcView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_settings(self):
        # Открывать настройки во встроенном виде (не отдельным окном)
        def swap():
            self._clear_root_frames()
            from app.views.settings import SettingsView
            SettingsView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _clear_root_frames(self):
        try:
            for child in self.root.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    