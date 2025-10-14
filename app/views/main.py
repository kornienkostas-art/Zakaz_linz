import tkinter as tk
from tkinter import ttk, filedialog

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
        self._schedule_notifications()

    def _build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Top bar with stats
        top = ttk.Frame(container)
        top.pack(side="top", fill="x", padx=20, pady=16)

        self.clients_count_var = tk.StringVar(value="Клиенты: 0")
        self.products_count_var = tk.StringVar(value="Товары: 0")
        self.mkl_count_var = tk.StringVar(value="МКЛ: 0")
        self.meridian_count_var = tk.StringVar(value="Меридиан: 0")

        for var in (
            self.clients_count_var,
            self.products_count_var,
            self.mkl_count_var,
            self.meridian_count_var,
        ):
            ttk.Label(top, textvariable=var).pack(side="left", padx=12)

        ttk.Button(top, text="Обновить", command=self._refresh_stats).pack(side="right", padx=8)

        # Settings quick info
        info = ttk.Frame(container)
        info.pack(fill="x", padx=20)
        export_path = (self.app_settings.get("export_path") or "").strip()
        ttk.Label(info, text=f"Папка экспорта: {export_path or 'не задана'}").pack(side="left", padx=12)
        ttk.Button(info, text="Настройки…", command=self._open_settings).pack(side="right", padx=8)

        # Main menu buttons - larger
        menu = ttk.Frame(container)
        menu.pack(fill="both", expand=True, padx=36, pady=28)

        row1 = ttk.Frame(menu)
        row1.pack(pady=16)
        row2 = ttk.Frame(menu)
        row2.pack(pady=16)

        btn_opts = dict(width=32)
        ttk.Button(row1, text="Клиенты", command=self._open_clients, **btn_opts).pack(side="left", padx=12, ipady=10)
        ttk.Button(row1, text="Товары", command=self._open_products, **btn_opts).pack(side="left", padx=12, ipady=10)

        ttk.Button(row2, text="Заказы МКЛ", command=self._open_mkl, **btn_opts).pack(side="left", padx=12, ipady=10)
        ttk.Button(row2, text="Заказы Меридиан", command=self._open_meridian, **btn_opts).pack(side="left", padx=12, ipady=10)

    def _refresh_stats(self):
        db = self.root.db
        try:
            clients = db.list_clients()
            products = db.list_products()
            mkl = db.list_mkl_orders()
            mer = db.list_meridian_orders()
        except Exception:
            clients, products, mkl, mer = [], [], [], []

        self.clients_count_var.set(f"Клиенты: {len(clients)}")
        self.products_count_var.set(f"Товары: {len(products)}")
        self.mkl_count_var.set(f"МКЛ: {len(mkl)}")
        self.meridian_count_var.set(f"Меридиан: {len(mer)}")

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

    def _open_settings(self):
        def swap():
            self._clear_root_frames()
            from app.views.settings import SettingsView
            SettingsView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _clear_root_frames(self):
        try:
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    child.destroy()
        except Exception:
            pass

    # Notifications
    def _schedule_notifications(self):
        settings = getattr(self.root, "app_settings", {}) or {}
        enabled = bool(settings.get("notify_enabled", True))
        interval_min = int(settings.get("notify_interval_minutes", 10))
        if not enabled:
            return
        # Schedule next check
        self.root.after(max(1, interval_min) * 60 * 1000, self._check_and_notify)

    def _check_and_notify(self):
        import datetime
        settings = getattr(self.root, "app_settings", {}) or {}
        enabled = bool(settings.get("notify_enabled", True))
        interval_min = int(settings.get("notify_interval_minutes", 10))
        age_hours = int(settings.get("notify_age_hours", 24))
        if not enabled:
            return

        cutoff = datetime.datetime.now() - datetime.timedelta(hours=age_hours)
        stale_mkl = []
        stale_mer = []
        try:
            for o in self.root.db.list_mkl_orders():
                # Notify for 'Заказан' older than cutoff and not yet 'Вручен'
                if (o.get("status") == "Заказан"):
                    # parse date
                    try:
                        dt = datetime.datetime.strptime(o.get("date", ""), "%Y-%m-%d %H:%M")
                        if dt <= cutoff:
                            stale_mkl.append(o)
                    except Exception:
                        pass
            for o in self.root.db.list_meridian_orders():
                if (o.get("status") == "Заказан"):
                    try:
                        dt = datetime.datetime.strptime(o.get("date", ""), "%Y-%m-%d %H:%M")
                        if dt <= cutoff:
                            stale_mer.append(o)
                    except Exception:
                        pass
        except Exception:
            pass

        if stale_mkl or stale_mer:
            lines = []
            if stale_mkl:
                lines.append(f"МКЛ: просрочено {len(stale_mkl)} заказ(ов).")
                for o in stale_mkl[:5]:
                    lines.append(f"- {o.get('fio','')} • {o.get('product','')} • дата: {o.get('date','')}")
            if stale_mer:
                lines.append(f"Меридиан: просрочено {len(stale_mer)} заказ(ов).")
                for o in stale_mer[:5]:
                    lines.append(f"- {o.get('title','')} • дата: {o.get('date','')}")
            try:
                from tkinter import messagebox
                messagebox.showinfo("Напоминание по заказам", "\n".join(lines))
            except Exception:
                pass

        # Reschedule next check
        try:
            self.root.after(max(1, interval_min) * 60 * 1000, self._check_and_notify)
        except Exception:
            pass