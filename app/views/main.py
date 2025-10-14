import tkinter as tk
from tkinter import ttk

from app.db import AppDB
from app.utils import set_initial_geometry, fade_transition


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("УссурОЧки.рф — Заказ линз")

        # Geometry
        set_initial_geometry(self.root, min_w=1024, min_h=700)

        # Ensure DB exists on root (created in main.py), but allow fallback
        if not hasattr(self.root, "db") or not isinstance(self.root.db, AppDB):
            self.root.db = AppDB("data.db")

        self._build_ui()
        self._refresh_stats()

    def _build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Top bar with stats
        top = ttk.Frame(container)
        top.pack(side="top", fill="x", padx=16, pady=12)

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
            ttk.Label(top, textvariable=var).pack(side="left", padx=8)

        ttk.Button(top, text="Обновить", command=self._refresh_stats).pack(side="right")

        # Main menu cards
        menu = ttk.Frame(container)
        menu.pack(fill="both", expand=True, padx=32, pady=24)

        # Two rows of buttons
        row1 = ttk.Frame(menu)
        row1.pack(pady=12)
        row2 = ttk.Frame(menu)
        row2.pack(pady=12)

        ttk.Button(row1, text="Клиенты", width=24, command=self._open_clients).pack(side="left", padx=8)
        ttk.Button(row1, text="Товары", width=24, command=self._open_products).pack(side="left", padx=8)

        ttk.Button(row2, text="Заказы МКЛ", width=24, command=self._open_mkl).pack(side="left", padx=8)
        ttk.Button(row2, text="Заказы Меридиан", width=24, command=self._open_meridian).pack(side="left", padx=8)

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
            try:
                # Remove current main menu
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.destroy()
            except Exception:
                pass
            from app.views.clients import ClientsView
            ClientsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_products(self):
        def swap():
            try:
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.destroy()
            except Exception:
                pass
            from app.views.products import ProductsView
            ProductsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_mkl(self):
        def swap():
            try:
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.destroy()
            except Exception:
                pass
            from app.views.orders_mkl import MKLOrdersView
            MKLOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_meridian(self):
        def swap():
            try:
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        child.destroy()
            except Exception:
                pass
            from app.views.orders_meridian import MeridianOrdersView
            MeridianOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)