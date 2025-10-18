import tkinter as tk
from tkinter import ttk
from datetime import datetime

from app.utils import fade_transition
from app.utils import create_tooltip
from app.utils import format_phone_mask
from app.utils import set_initial_geometry


class SelectClientDialog(tk.Toplevel):
    """Диалог выбора клиента (ФИО + телефон) с поиском."""
    def __init__(self, master, clients: list[dict], on_select):
        super().__init__(master)
        self.title("Выбор клиента")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=520, min_h=420, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._clients = clients[:]
        self._on_select = on_select

        card = ttk.Frame(self, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Поиск", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(card, textvariable=self.search_var)
        ent.grid(row=1, column=0, sticky="ew")
        ent.bind("<KeyRelease>", lambda e: self._filter())

        self.listbox = tk.Listbox(card)
        self.listbox.grid(row=2, column=0, sticky="nsew", pady=(8, 8))
        y = ttk.Scrollbar(card, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=y.set)
        y.grid(row=2, column=0, sticky="nse")
        card.rowconfigure(2, weight=1)

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="e")
        ttk.Button(btns, text="ОК", style="Menu.TButton", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Back.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        self.listbox.bind("<Double-Button-1>", lambda e: self._ok())
        self._reload(self._clients)

    def _format_item(self, c: dict) -> str:
        fio = (c.get("fio", "") or "").strip()
        phone = format_phone_mask(c.get("phone", "") or "")
        return f"{fio} — {phone}".strip(" —")

    def _reload(self, clients: list[dict]):
        self.listbox.delete(0, "end")
        for c in clients:
            self.listbox.insert("end", self._format_item(c))

    def _filter(self):
        term = (self.search_var.get() or "").strip().lower()
        if not term:
            self._reload(self._clients)
            return
        filtered = []
        for c in self._clients:
            merged = f"{c.get('fio','')} {c.get('phone','')}".lower()
            if term in merged:
                filtered.append(c)
        self._reload(filtered)

    def _ok(self):
        try:
            idxs = self.listbox.curselection()
            if not idxs:
                return
            text = self.listbox.get(idxs[0])
            # naive parse: split on em dash to extract phone
            if "—" in text:
                fio, phone_mask = text.split("—", 1)
                fio = fio.strip()
                phone_mask = phone_mask.strip()
            else:
                fio = text.strip()
                phone_mask = ""
            if callable(self._on_select):
                self._on_select(fio, phone_mask)
        finally:
            self.destroy()


class SelectProductDialog(tk.Toplevel):
    """Диалог выбора товара МКЛ с группами (Treeview) и поиском."""
    def __init__(self, master, db, on_select):
        super().__init__(master)
        self.title("Выбор товара")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=560, min_h=480, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._db = db
        self._on_select = on_select

        card = ttk.Frame(self, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Поиск", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(card, textvariable=self.search_var)
        ent.grid(row=1, column=0, sticky="ew")
        ent.bind("<KeyRelease>", lambda e: self._reload_tree())

        # Tree with groups and products
        self.tree = ttk.Treeview(card, show="tree")
        self.tree.grid(row=2, column=0, sticky="nsew", pady=(8, 8))
        y = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y.set)
        y.grid(row=2, column=0, sticky="nse")
        card.rowconfigure(2, weight=1)

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="e")
        ttk.Button(btns, text="ОК", style="Menu.TButton", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Back.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        self.tree.bind("<Double-Button-1>", self._on_dbl_click)
        self._reload_tree()

    def _reload_tree(self):
        term = (self.search_var.get() or "").strip().lower()
        # Clear
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        groups = []
        try:
            groups = self._db.list_product_groups_mkl()
        except Exception:
            groups = []
        # Ungrouped first
        ungrouped = []
        try:
            ungrouped = self._db.list_products_mkl_by_group(None)
        except Exception:
            ungrouped = []
        # If no groups at all, show flat list under a single root
        if not groups:
            root = self.tree.insert("", "end", text="Все товары", open=True, tags=("group", "gid:None"))
            any_found = False
            for p in ungrouped:
                name = (p.get("name", "") or "")
                if term and term not in name.lower():
                    continue
                any_found = True
                self.tree.insert(root, "end", text=name, tags=("product", f"pid:{p.get('id')}", "gid:None"))
            if term and not any_found:
                self.tree.insert(root, "end", text="(Ничего не найдено)", tags=("info",))
            return

        # Ungrouped section
        if ungrouped:
            node = self.tree.insert("", "end", text="Без группы", open=bool(term), tags=("group", "gid:None"))
            for p in ungrouped:
                name = (p.get("name", "") or "")
                if term and term not in name.lower():
                    continue
                self.tree.insert(node, "end", text=name, tags=("product", f"pid:{p.get('id')}", "gid:None"))

        # Groups section
        any_found = False
        for g in groups:
            try:
                prods = self._db.list_products_mkl_by_group(g["id"])
            except Exception:
                prods = []
            matched = []
            if term:
                for p in prods:
                    n = (p.get("name", "") or "")
                    if term in n.lower():
                        matched.append(p)
            else:
                matched = prods
            # If searching, only show groups with matches
            if term and not matched:
                continue
            node = self.tree.insert("", "end", text=g["name"], open=bool(term), tags=("group", f"gid:{g['id']}"))
            for p in matched:
                name = (p.get("name", "") or "")
                self.tree.insert(node, "end", text=name, tags=("product", f"pid:{p['id']}", f"gid:{g['id']}"))
                any_found = True
        if term and not any_found and not ungrouped:
            self.tree.insert("", "end", text="(Ничего не найдено)", tags=("info",))

    def _on_dbl_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        tags = set(self.tree.item(item, "tags") or [])
        text = self.tree.item(item, "text") or ""
        if "group" in tags:
            # Toggle expand/collapse
            is_open = self.tree.item(item, "open")
            self.tree.item(item, open=not is_open)
            return
        if "product" in tags:
            if callable(self._on_select):
                self._on_select(text)
            self.destroy()

    def _ok(self):
        # Select currently focused product if any
        item = self.tree.focus()
        if not item:
            return
        tags = set(self.tree.item(item, "tags") or [])
        text = self.tree.item(item, "text") or ""
        if "product" in tags and callable(self._on_select):
            self._on_select(text)
            self.destroy()


class NewMKLOrderView(ttk.Frame):
    """Полноэкранная форма нового заказа МКЛ внутри приложения."""
    def __init__(self, master: tk.Tk, db, on_back, on_submit):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back
        self.on_submit = on_submit

        # Fill window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # Data
        self.clients = self.db.list_clients() if self.db else []
        self.products = self.db.list_products_mkl() if self.db else []

        # Vars
        self.fio_var = tk.StringVar()
        self.phone_var = tk.StringVar()

        self._safe_build_ui()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Back.TButton", command=self._go_back).pack(side="left")
        ttk.Label(toolbar, text="Новый заказ МКЛ", style="Title.TLabel").pack(side="left", padx=(12, 0))

        # Content
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        for i in range(2):
            card.columnconfigure(i, weight=1)

        # Client section
        ttk.Label(card, text="Клиент", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", columnspan=2)
        row = ttk.Frame(card, style="Card.TFrame")
        row.grid(row=1, column=0, columnspan=2, sticky="ew")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ttk.Label(row, text="ФИО", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.fio_entry = ttk.Entry(row, textvariable=self.fio_var)
        self.fio_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(row, text="Телефон", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        self.phone_entry = ttk.Entry(row, textvariable=self.phone_var)
        self.phone_entry.grid(row=1, column=1, sticky="ew")

        pick_row = ttk.Frame(card, style="Card.TFrame")
        pick_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(pick_row, text="Выбрать клиента", style="Menu.TButton", command=self._pick_client).pack(side="left")

        # Product section
        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", columnspan=2, pady=(12, 0))
        prow = ttk.Frame(card, style="Card.TFrame")
        prow.grid(row=4, column=0, columnspan=2, sticky="ew")
        prow.columnconfigure(0, weight=1)

        self.product_var = tk.StringVar()
        self.product_entry = ttk.Entry(prow, textvariable=self.product_var)
        self.product_entry.grid(row=0, column=0, sticky="ew")

        # Footer actions
        ttk.Separator(card).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 12))
        actions = ttk.Frame(card, style="Card.TFrame")
        actions.grid(row=6, column=0, columnspan=2, sticky="ew")
        # Bottom-left: pick product
        ttk.Button(actions, text="Выбрать товар", style="Menu.TButton", command=self._pick_product).pack(side="left")
        # Bottom-right: proceed/cancel
        ttk.Button(actions, text="Продолжить", style="Menu.TButton", command=self._submit).pack(side="right")
        ttk.Button(actions, text="Отмена", style="Back.TButton", command=self._go_back).pack(side="right", padx=(8, 0))

    def _safe_build_ui(self):
        try:
            self._build_ui()
        except Exception as e:
            # Fallback content to avoid blank screen
            holder = ttk.Frame(self, padding=16)
            holder.pack(fill="both", expand=True)
            ttk.Label(holder, text="Ошибка при построении формы нового заказа.", anchor="w").pack(anchor="w")
            ttk.Label(holder, text=f"{e}", anchor="w", foreground="#7f1d1d").pack(anchor="w", pady=(4, 12))
            ttk.Button(holder, text="← Назад", command=self._go_back).pack(anchor="w")

    def _pick_client(self):
        def on_select(fio, phone_mask):
            self.fio_var.set(fio)
            self.phone_var.set(phone_mask)
        SelectClientDialog(self, self.clients, on_select=on_select)

    def _go_back(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "on_back", None)
            if callable(cb):
                cb()

    def _pick_product(self):
        def on_select(name: str):
            self.product_var.set(name)
        SelectProductDialog(self, self.db, on_select=on_select)

    def _submit(self):
        fio = (self.fio_var.get() or "").strip()
        phone = (self.phone_var.get() or "").strip()
        product = (self.product_var.get() or "").strip()
        if not fio and not phone:
            try:
                from tkinter import messagebox
                messagebox.showinfo("Проверка", "Введите клиента или выберите из списка.")
            except Exception:
                pass
            return
        if not product:
            try:
                from tkinter import messagebox
                messagebox.showinfo("Проверка", "Введите товар или выберите из списка.")
            except Exception:
                pass
            return
        payload = {
            "fio": fio,
            "phone": phone,
            "product": product,
        }
        cb = getattr(self, "on_submit", None)
        if callable(cb):
            cb(payload)
        self._go_back()


