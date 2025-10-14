import tkinter as tk
from tkinter import ttk, messagebox

from db import AppDB
from utils import set_initial_geometry


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("УссурОЧки.рф — Заказ линз")

        # Geometry
        set_initial_geometry(self.root, min_w=900, min_h=600)

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
        top.pack(side="top", fill="x", padx=12, pady=8)

        self.clients_count_var = tk.StringVar(value="Клиенты: 0")
        self.products_count_var = tk.StringVar(value="Товары: 0")
        self.mkl_count_var = tk.StringVar(value="MKL-заказы: 0")
        self.meridian_count_var = tk.StringVar(value="Meridian-заказы: 0")

        for var in (
            self.clients_count_var,
            self.products_count_var,
            self.mkl_count_var,
            self.meridian_count_var,
        ):
            ttk.Label(top, textvariable=var).pack(side="left", padx=8)

        ttk.Button(top, text="Обновить", command=self._refresh_stats).pack(
            side="right"
        )

        # Tabs placeholder
        tabs = ttk.Notebook(container)
        tabs.pack(fill="both", expand=True, padx=12, pady=8)

        # Simple tab: quick add client
        tab_clients = ttk.Frame(tabs)
        tabs.add(tab_clients, text="Клиенты")

        form = ttk.Frame(tab_clients)
        form.pack(side="top", fill="x", padx=12, pady=12)

        ttk.Label(form, text="ФИО:").grid(row=0, column=0, sticky="w")
        self.fio_entry = ttk.Entry(form, width=40)
        self.fio_entry.grid(row=0, column=1, sticky="we", padx=8)

        ttk.Label(form, text="Телефон:").grid(row=1, column=0, sticky="w")
        self.phone_entry = ttk.Entry(form, width=20)
        self.phone_entry.grid(row=1, column=1, sticky="we", padx=8)

        ttk.Button(form, text="Добавить клиента", command=self._add_client).grid(
            row=0, column=2, rowspan=2, padx=8
        )

        form.columnconfigure(1, weight=1)

        # Listbox for clients
        list_frame = ttk.Frame(tab_clients)
        list_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.clients_list = tk.Listbox(list_frame)
        self.clients_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.clients_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.clients_list.configure(yscrollcommand=scrollbar.set)

        # Products tab placeholder
        tab_products = ttk.Frame(tabs)
        tabs.add(tab_products, text="Товары")

        prod_top = ttk.Frame(tab_products)
        prod_top.pack(side="top", fill="x", padx=12, pady=12)
        ttk.Label(prod_top, text="Наименование:").pack(side="left")
        self.product_entry = ttk.Entry(prod_top, width=40)
        self.product_entry.pack(side="left", padx=8)
        ttk.Button(prod_top, text="Добавить товар", command=self._add_product).pack(side="left")

        self.products_list = tk.Listbox(tab_products)
        self.products_list.pack(fill="both", expand=True, padx=12, pady=8)

    def _refresh_stats(self):
        db = self.root.db
        clients = db.list_clients()
        products = db.list_products()
        mkl = db.list_mkl_orders()
        mer = db.list_meridian_orders()

        self.clients_count_var.set(f"Клиенты: {len(clients)}")
        self.products_count_var.set(f"Товары: {len(products)}")
        self.mkl_count_var.set(f"MKL-заказы: {len(mkl)}")
        self.meridian_count_var.set(f"Meridian-заказы: {len(mer)}")

        # populate lists
        self.clients_list.delete(0, "end")
        for c in clients:
            self.clients_list.insert("end", f"{c['fio']} | {c['phone']}")

        self.products_list.delete(0, "end")
        for p in products:
            self.products_list.insert("end", p["name"])

    def _add_client(self):
        fio = self.fio_entry.get().strip()
        phone = self.phone_entry.get().strip()
        if not fio:
            messagebox.showwarning("Пустое ФИО", "Введите ФИО клиента")
            return
        self.root.db.add_client(fio, phone)
        self.fio_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self._refresh_stats()

    def _add_product(self):
        name = self.product_entry.get().strip()
        if not name:
            messagebox.showwarning("Пустое имя", "Введите наименование товара")
            return
        self.root.db.add_product(name)
        self.product_entry.delete(0, "end")
        self._refresh_stats()