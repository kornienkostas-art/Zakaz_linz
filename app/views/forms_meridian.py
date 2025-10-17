import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.utils import set_initial_geometry
from app.utils import create_tooltip


class MeridianProductPickerInline(ttk.Frame):
    """Встроенная панель выбора товара с группами + свободный ввод имени и корзиной позиций."""
    def __init__(self, master, db, on_done, on_cancel=None):
        super().__init__(master, style="Card.TFrame", padding=12)
        self.db = db
        self.on_done = on_done
        self.on_cancel = on_cancel
        self._basket: list[dict] = []
        self._build_ui()
        self._load_tree()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(3, weight=1)

        # Search + free product entry
        top = ttk.Frame(self, style="Card.TFrame")
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Поиск:", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ent_search = ttk.Entry(top, textvariable=self.search_var)
        ent_search.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        ent_search.bind("<KeyRelease>", lambda e: self._load_tree())

        ttk.Label(top, text="Свободный ввод товара:", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.free_name_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.free_name_var).grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(8, 0))

        # Tree
        self.tree = ttk.Treeview(self, show="tree", style="Data.Treeview")
        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=(0, 8))
        y_scroll.grid(row=1, column=0, rowspan=3, sticky="nse")
        self.tree.bind("<Double-1>", self._on_tree_dbl)

        # Right panel params
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="ew")
        right.columnconfigure(1, weight=1)
        right.columnconfigure(3, weight=1)

        self.sel_product_var = tk.StringVar(value="")
        row_sel = ttk.Frame(right, style="Card.TFrame")
        row_sel.grid(row=0, column=0, columnspan=4, sticky="ew")
        ttk.Label(row_sel, text="Выбранный товар:", style="Subtitle.TLabel").pack(side="left")
        self.sel_label = ttk.Label(row_sel, text="", style="TLabel")
        self.sel_label.pack(side="left", padx=(8, 0))

        # Variables
        self.sph_var = tk.StringVar()
        self.cyl_var = tk.StringVar()
        self.ax_var = tk.StringVar()
        self.d_var = tk.StringVar()
        self.qty_var = tk.IntVar(value=1)

        def _nudge(var: tk.StringVar, min_v: float, max_v: float, step: float, direction: int):
            txt = (var.get() or "").replace(",", ".").strip()
            if txt == "":
                cur = 0.0
            else:
                try:
                    cur = float(txt)
                except ValueError:
                    cur = 0.0 if (min_v <= 0.0 <= max_v) else min_v
            cur += step * (1 if direction >= 0 else -1)
            cur = max(min_v, min(max_v, cur))
            steps = round((cur - min_v) / step)
            snapped = min_v + steps * step
            snapped = max(min_v, min(max_v, snapped))
            var.set(f"{snapped:.2f}")

        ttk.Label(right, text="SPH (−30…+30, 0.25)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        sph_row = ttk.Frame(right); sph_row.grid(row=1, column=1, sticky="ew", pady=(6, 0)); sph_row.columnconfigure(1, weight=1)
        ttk.Button(sph_row, text="−", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, -1)).grid(row=0, column=0)
        ttk.Entry(sph_row, textvariable=self.sph_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(sph_row, text="+", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, +1)).grid(row=0, column=2)

        ttk.Label(right, text="CYL (−10…+10, 0.25)").grid(row=1, column=2, sticky="w", pady=(6, 0))
        cyl_row = ttk.Frame(right); cyl_row.grid(row=1, column=3, sticky="ew", pady=(6, 0)); cyl_row.columnconfigure(1, weight=1)
        ttk.Button(cyl_row, text="−", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, -1)).grid(row=0, column=0)
        ttk.Entry(cyl_row, textvariable=self.cyl_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(cyl_row, text="+", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, +1)).grid(row=0, column=2)

        ttk.Label(right, text="AX (0…180)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(right, textvariable=self.ax_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))
        ttk.Label(right, text="D (40…90, шаг 5)").grid(row=2, column=2, sticky="w", pady=(6, 0))
        ttk.Entry(right, textvariable=self.d_var).grid(row=2, column=3, sticky="ew", pady=(6, 0))
        ttk.Label(right, text="Количество (1…20)").grid(row=2, column=4, sticky="w", padx=(12, 0), pady=(6, 0))
        ttk.Spinbox(right, from_=1, to=20, textvariable=self.qty_var, width=7).grid(row=2, column=5, sticky="w", pady=(6, 0))

        # Basket controls
        ctl = ttk.Frame(self, style="Card.TFrame")
        ctl.grid(row=2, column=1, sticky="ew", pady=(8, 4))
        ttk.Button(ctl, text="Добавить в список", style="Menu.TButton", command=self._add_to_basket).pack(side="left")
        ttk.Button(ctl, text="Очистить список", style="Menu.TButton", command=self._clear_basket).pack(side="left", padx=(8, 0))

        # Basket table
        cols = ("product", "sph", "cyl", "ax", "d", "qty")
        self.basket = ttk.Treeview(self, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "d": "D (мм)", "qty": "Кол-во"}
        widths = {"product": 360, "sph": 70, "cyl": 70, "ax": 60, "d": 70, "qty": 70}
        for c in cols:
            self.basket.heading(c, text=headers[c], anchor="w")
            self.basket.column(c, width=widths[c], anchor="w", stretch=True)
        y2 = ttk.Scrollbar(self, orient="vertical", command=self.basket.yview)
        self.basket.configure(yscroll=y2.set)
        self.basket.grid(row=3, column=1, sticky="nsew")
        y2.grid(row=3, column=1, sticky="nse")

        # Footer
        foot = ttk.Frame(self, style="Card.TFrame")
        foot.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(foot, text="Добавить в заказ", style="Menu.TButton", command=self._done).pack(side="right")
        ttk.Button(foot, text="Отмена", style="Menu.TButton", command=self._cancel).pack(side="right", padx=(8, 0))

    def _load_tree(self):
        term = (self.search_var.get() or "").strip().lower()
        self.tree.delete(*self.tree.get_children())
        try:
            groups = self.db.list_product_groups_meridian()
        except Exception:
            groups = []
        if not groups:
            # Показываем плоский список всех товаров
            try:
                all_prods = self.db.list_products_meridian()
            except Exception:
                all_prods = []
            root = self.tree.insert("", "end", text="Все товары", open=True, tags=("group", "gid:None"))
            for p in all_prods:
                name = p.get("name", "")
                if term and term not in (name or "").lower():
                    continue
                self.tree.insert(root, "end", text=name, tags=("product", f"pid:{p.get('id')}", "gid:None"))
            return

        for g in groups:
            node = self.tree.insert("", "end", text=g["name"], open=False, tags=("group", f"gid:{g['id']}"))
            try:
                prods = self.db.list_products_meridian_by_group(g["id"])
            except Exception:
                prods = []
            any_added = False
            for p in prods:
                name = p["name"]
                if term and term not in name.lower():
                    continue
                self.tree.insert(node, "end", text=name, tags=("product", f"pid:{p['id']}", f"gid:{g['id']}"))
                any_added = True
            # Если по фильтру в группе нет элементов — скрывать группу не будем, просто останется пустой

    def _on_tree_dbl(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        tags = set(self.tree.item(item, "tags") or [])
        text = self.tree.item(item, "text") or ""
        if "group" in tags:
            is_open = self.tree.item(item, "open")
            self.tree.item(item, open=not is_open)
            return
        if "product" in tags:
            self.sel_product_var.set(text)
            self.sel_label.configure(text=text)

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = 0.0
        v = max(min_v, min(max_v, v))
        steps = round((v - min_v) / step)
        snapped = min_v + steps * step
        snapped = max(min_v, min(max_v, snapped))
        return f"{snapped:.2f}"

    @staticmethod
    def _snap_int(value_str: str, min_v: int, max_v: int, allow_empty: bool = False) -> str:
        text = (value_str or "").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = int(float(text.replace(",", ".")))
        except ValueError:
            v = min_v
        v = max(min_v, min(max_v, v))
        return str(v)

    def _effective_product_name(self) -> str:
        free = (self.free_name_var.get() or "").strip()
        if free:
            return free
        return (self.sel_product_var.get() or "").strip()

    def _add_to_basket(self):
        product = self._effective_product_name()
        if not product:
            messagebox.showinfo("Выбор", "Введите название товара или выберите его слева.")
            return
        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        d = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
        if d != "":
            try:
                iv = int(d)
                iv = int(round(iv / 5.0) * 5)
                d = str(iv)
            except Exception:
                pass
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)

        item = {"product": product, "sph": sph, "cyl": cyl, "ax": ax, "d": d, "qty": qty}
        self._basket.append(item)
        self._refresh_basket()

    def _refresh_basket(self):
        for i in self.basket.get_children():
            self.basket.delete(i)
        for idx, it in enumerate(self._basket):
            self.basket.insert("", "end", iid=str(idx), values=(it["product"], it["sph"], it["cyl"], it["ax"], it["d"], it["qty"]))

    def _clear_basket(self):
        if not self._basket:
            return
        if messagebox.askyesno("Очистить", "Очистить список?"):
            self._basket.clear()
            self._refresh_basket()

    def _done(self):
        if callable(self.on_done):
            try:
                self.on_done(list(self._basket))
            except Exception:
                pass
        self._basket.clear()
        self._refresh_basket()
        # Скрываем панель после переноса
        if callable(self.on_cancel):
            self.on_cancel()

    def _cancel(self):
        # Закрыть панель без добавления
        if callable(self.on_cancel):
            self.on_cancel()


class MeridianOrderForm(tk.Toplevel):
    """Форма создания/редактирования заказа Меридиан (с несколькими позициями)."""
    def __init__(self, master, on_save=None, initial: dict | None = None):
        super().__init__(master)
        self.title("Редактирование заказа" if initial else "Новый заказ")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=900, min_h=700, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        self.statuses = ["Не заказан", "Заказан"]
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.is_new = initial is None

        self.items: list[dict] = []
        for it in (initial or {}).get("items", []):
            self.items.append(it.copy())

        self._build_ui()

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        self._card = card
        self._picker_panel = None
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        if not self.is_new:
            header = ttk.Frame(card, style="Card.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            ttk.Label(header, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Combobox(header, textvariable=self.status_var, values=self.statuses, height=4).grid(row=1, column=0, sticky="ew")
            header.columnconfigure(0, weight=1)

        ttk.Separator(card).grid(row=1, column=0, sticky="ew", pady=(12, 12))

        items_frame = ttk.Frame(card, style="Card.TFrame")
        items_frame.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(2, weight=1)

        cols = ("product", "sph", "cyl", "ax", "d", "qty")
        self.items_tree = ttk.Treeview(items_frame, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 240, "sph": 90, "cyl": 90, "ax": 90, "d": 90, "qty": 120}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y_scroll.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(0, weight=1)

        items_toolbar = ttk.Frame(card, style="Card.TFrame")
        items_toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(items_toolbar, text="Добавить позицию", style="Menu.TButton", command=self._add_item).pack(side="left")
        ttk.Button(items_toolbar, text="Редактировать позицию", style="Menu.TButton", command=self._edit_item).pack(side="left", padx=(8, 0))
        ttk.Button(items_toolbar, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left", padx=(8, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        self._refresh_items_view()

    def _refresh_items_view(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, it in enumerate(self.items):
            values = (it.get("product", ""), it.get("sph", ""), it.get("cyl", ""), it.get("ax", ""), it.get("d", ""), it.get("qty", ""))
            self.items_tree.insert("", "end", iid=str(idx), values=values)

    def _selected_item_index(self):
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите позицию.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _find_db(self):
        node = self
        while node is not None:
            db = getattr(node, "db", None)
            if db:
                return db
            node = getattr(node, "master", None)
        return None

    def _close_picker(self):
        try:
            if self._picker_panel is not None:
                self._picker_panel.destroy()
        except Exception:
            pass
        self._picker_panel = None

    def _show_picker_inline(self, db):
        self._close_picker()
        panel = MeridianProductPickerInline(self._card, db, on_done=lambda items: (self.items.extend(items), self._refresh_items_view(), self._close_picker()), on_cancel=self._close_picker)
        # Размещаем панель под кнопками, чтобы не ломать существующую компоновку
        try:
            panel.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
            self._card.rowconfigure(5, weight=1)
        except Exception:
            panel.pack(fill="both", expand=True, pady=(8, 0))
        self._picker_panel = panel

    def _add_item(self):
        db = self._find_db()
        if db:
            self._show_picker_inline(db)
            return
        # Fallback: simple item form
        MeridianItemForm(self, products=[], on_save=lambda it: (self.items.append(it), self._refresh_items_view()))

    def _edit_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        current = self.items[idx].copy()
        products = []
        try:
            if hasattr(self, "db") and self.db:
                products = self.db.list_products()
        except Exception:
            products = []
        MeridianItemForm(self, products=products, initial=current, on_save=lambda it: (self._apply_item_update(idx, it), self._refresh_items_view()))

    def _apply_item_update(self, idx: int, it: dict):
        self.items[idx] = it

    def _delete_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        if messagebox.askyesno("Удалить", "Удалить выбранную позицию?"):
            self.items.pop(idx)
            self._refresh_items_view()

    def _save(self):
        status = (self.status_var.get() or "Не заказан").strip()
        order = {
            "title": "",
            "status": status,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": self.items.copy(),
        }
        if self.on_save:
            self.on_save(order)
        self.destroy()


class MeridianItemForm(tk.Toplevel):
    """Форма позиции товара для Меридиан с выбором товара из списка."""
    def __init__(self, master, products: list[dict] | None = None, on_save=None, initial: dict | None = None):
        super().__init__(master)
        self.title("Позиция товара")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=600, min_h=420, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        self.products = products or []
        self.product_var = tk.StringVar(value=(initial or {}).get("product", ""))
        # По умолчанию поля пустые; при открытии списка подсветим 0.00 (для SPH/CYL)
        self.sph_var = tk.StringVar(value=(initial or {}).get("sph", ""))
        self.cyl_var = tk.StringVar(value=(initial or {}).get("cyl", ""))
        self.ax_var = tk.StringVar(value=(initial or {}).get("ax", ""))
        self.d_var = tk.StringVar(value=(initial or {}).get("d", ""))
        self.qty_var = tk.IntVar(value=int((initial or {}).get("qty", 1)) or 1)

        self._build_ui()

    def _product_values(self) -> list[str]:
        return [p.get("name", "") for p in self.products]

    def _filter_products(self):
        term = (self.product_var.get() or "").strip().lower()
        values = self._product_values()
        if term:
            values = [v for v in values if term in v.lower()]
        self.product_combo["values"] = values

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        # Combobox for product selection with autocomplete
        self.product_combo = ttk.Combobox(card, textvariable=self.product_var, values=self._product_values(), height=10)
        self.product_combo.grid(row=1, column=0, sticky="ew")
        self.product_combo.bind("<KeyRelease>", lambda e: self._filter_products())

        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Local nudge function for +/- buttons
        def _nudge(var: tk.StringVar, min_v: float, max_v: float, step: float, direction: int):
            txt = (var.get() or "").replace(",", ".").strip()
            if txt == "":
                cur = 0.0
            else:
                try:
                    cur = float(txt)
                except ValueError:
                    cur = 0.0 if (min_v <= 0.0 <= max_v) else min_v
            cur += step * (1 if direction >= 0 else -1)
            cur = max(min_v, min(max_v, cur))
            steps = round((cur - min_v) / step)
            snapped = min_v + steps * step
            snapped = max(min_v, min(max_v, snapped))
            var.set(f"{snapped:.2f}")

        # SPH row with − / +
        sph_row = ttk.Frame(card, style="Card.TFrame")
        sph_row.grid(row=3, column=0, sticky="ew")
        sph_row.columnconfigure(1, weight=1)
        btn_sph_dec = ttk.Button(sph_row, text="−", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, -1))
        btn_sph_dec.grid(row=0, column=0, sticky="w")
        self.sph_entry = ttk.Entry(sph_row, textvariable=self.sph_var)
        self.sph_entry.grid(row=0, column=1, sticky="ew", padx=4)
        btn_sph_inc = ttk.Button(sph_row, text="+", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, +1))
        btn_sph_inc.grid(row=0, column=2, sticky="e")
        try:
            create_tooltip(btn_sph_dec, "SPH: уменьшить на 0.25. Диапазон: −30.00…+30.00")
            create_tooltip(btn_sph_inc, "SPH: увеличить на 0.25. Диапазон: −30.00…+30.00")
        except Exception:
            pass
        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))

        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=2, column=1, sticky="w", pady=(8, 0))
        # CYL row with − / +
        cyl_row = ttk.Frame(card, style="Card.TFrame")
        cyl_row.grid(row=3, column=1, sticky="ew")
        cyl_row.columnconfigure(1, weight=1)
        btn_cyl_dec = ttk.Button(cyl_row, text="−", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, -1))
        btn_cyl_dec.grid(row=0, column=0, sticky="w")
        self.cyl_entry = ttk.Entry(cyl_row, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=0, column=1, sticky="ew", padx=4)
        btn_cyl_inc = ttk.Button(cyl_row, text="+", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, +1))
        btn_cyl_inc.grid(row=0, column=2, sticky="e")
        try:
            create_tooltip(btn_cyl_dec, "CYL: уменьшить на 0.25. Диапазон: −10.00…+10.00")
            create_tooltip(btn_cyl_inc, "CYL: увеличить на 0.25. Диапазон: −10.00…+10.00")
        except Exception:
            pass
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=5, column=0, sticky="ew")
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))

        ttk.Label(card, text="D (40…90, шаг 5) — в экспорте добавляется 'мм'", style="Subtitle.TLabel").grid(row=4, column=1, sticky="w", pady=(8, 0))
        self.d_entry = ttk.Entry(card, textvariable=self.d_var)
        self.d_entry.grid(row=5, column=1, sticky="ew")
        d_vcmd = (self.register(self._vc_int_relaxed), "%P")
        self.d_entry.configure(validate="key", validatecommand=d_vcmd)
        self.d_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("d"))

        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=7, column=0, sticky="w")

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить позицию", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    # Validation helpers
    def _vc_decimal(self, new_value: str, min_v: float, max_v: float) -> bool:
        v = (new_value or "").replace(",", ".")
        if v == "":
            return True
        if v in {"+", "-", ".", "-.", "+.", ",", "-,", "+,"}:
            return True
        try:
            num = float(v)
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _vc_int(self, new_value: str, min_v: int, max_v: int) -> bool:
        v = (new_value or "").strip()
        if v == "":
            return True
        if v in {"+", "-"}:
            return True
        try:
            num = int(float(v.replace(",", ".")))
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _vc_int_relaxed(self, new_value: str) -> bool:
        v = (new_value or "").strip()
        if v == "":
            return True
        if v in {"+", "-"}:
            return True
        return v.isdigit()

    def _apply_snap_for(self, field: str):
        if field == "sph":
            self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True))
        elif field == "cyl":
            self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True))
        elif field == "ax":
            self.ax_var.set(self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True))
        elif field == "d":
            v = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
            if v != "":
                try:
                    iv = int(v)
                except Exception:
                    iv = 40
                iv = max(40, min(90, iv))
                iv = int(round(iv / 5.0) * 5)
                self.d_var.set(str(iv))
            else:
                self.d_var.set("")

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = min_v
        v = max(min_v, min(max_v, v))
        steps = round((v - min_v) / step)
        snapped = min_v + steps * step
        snapped = max(min_v, min(max_v, snapped))
        return f"{snapped:.2f}"

    @staticmethod
    def _snap_int(value_str: str, min_v: int, max_v: int, allow_empty: bool = False) -> str:
        text = (value_str or "").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = int(float(text.replace(",", ".")))
        except ValueError:
            v = min_v
        v = max(min_v, min(max_v, v))
        return str(v)

    def _save(self):
        product = (self.product_var.get() or "").strip()
        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        d = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
        if d != "":
            try:
                iv = int(d)
                iv = int(round(iv / 5.0) * 5)
                d = str(iv)
            except Exception:
                pass
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)

        if not product:
            messagebox.showinfo("Проверка", "Введите название товара.")
            return

        item = {"product": product, "sph": sph, "cyl": cyl, "ax": ax, "d": d, "qty": qty}
        if self.on_save:
            self.on_save(item)
        self.destroy()


class MeridianOrderEditorView(ttk.Frame):
    """Встроенный редактор заказа 'Меридиан' внутри главного окна."""
    STATUSES = ["Не заказан", "Заказан"]

    def __init__(self, master: tk.Tk, db, on_back, on_save, initial: dict | None = None):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back
        self.on_save = on_save
        self.is_new = initial is None

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.items: list[dict] = []
        for it in (initial or {}).get("items", []):
            self.items.append(it.copy())

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        self._card = card
        self._picker_panel = None
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        if not self.is_new:
            header = ttk.Frame(card, style="Card.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            ttk.Label(header, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Combobox(header, textvariable=self.status_var, values=self.STATUSES, height=4).grid(row=1, column=0, sticky="ew")
            header.columnconfigure(0, weight=1)

        ttk.Separator(card).grid(row=1, column=0, sticky="ew", pady=(12, 12))

        items_frame = ttk.Frame(card, style="Card.TFrame")
        items_frame.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(2, weight=1)

        cols = ("product", "sph", "cyl", "ax", "d", "qty")
        self.items_tree = ttk.Treeview(items_frame, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 240, "sph": 90, "cyl": 90, "ax": 90, "d": 90, "qty": 120}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y_scroll.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(0, weight=1)

        items_toolbar = ttk.Frame(card, style="Card.TFrame")
        items_toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(items_toolbar, text="Добавить позицию", style="Menu.TButton", command=self._add_item).pack(side="left")
        ttk.Button(items_toolbar, text="Редактировать позицию", style="Menu.TButton", command=self._edit_item).pack(side="left", padx=(8, 0))
        ttk.Button(items_toolbar, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left", padx=(8, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self._go_back).pack(side="right", padx=(8, 0))

        self._refresh_items_view()

    def _go_back(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "on_back", None)
            if callable(cb):
                cb()

    def _refresh_items_view(self):
        try:
            for i in self.items_tree.get_children():
                self.items_tree.delete(i)
            for idx, it in enumerate(self.items):
                values = (it.get("product", ""), it.get("sph", ""), it.get("cyl", ""), it.get("ax", ""), it.get("d", ""), it.get("qty", ""))
                self.items_tree.insert("", "end", iid=str(idx), values=values)
        except Exception:
            pass

    def _selected_item_index(self):
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите позицию.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _add_item(self):
        if self.db:
            # Встроенная панель выбора вместо нового окна
            def _cancel():
                try:
                    if self._picker_panel is not None:
                        self._picker_panel.destroy()
                except Exception:
                    pass
                self._picker_panel = None
            def on_done(items):
                self.items.extend(items)
                self._refresh_items_view()
                _cancel()
            # Показать/создать панель
            try:
                if self._picker_panel is not None:
                    self._picker_panel.destroy()
            except Exception:
                pass
            self._picker_panel = MeridianProductPickerInline(self._card, self.db, on_done=on_done, on_cancel=_cancel)
            try:
                self._picker_panel.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
                self._card.rowconfigure(5, weight=1)
            except Exception:
                self._picker_panel.pack(fill="both", expand=True, pady=(8, 0))
            return
        MeridianItemForm(self, products=[], on_save=lambda it: (self.items.append(it), self._refresh_items_view()))

    def _edit_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        current = self.items[idx].copy()
        products = []
        try:
            if self.db:
                products = self.db.list_products_meridian()
        except Exception:
            products = []
        MeridianItemForm(self, products=products, initial=current, on_save=lambda it: (self._apply_item_update(idx, it), self._refresh_items_view()))

    def _apply_item_update(self, idx: int, it: dict):
        try:
            self.items[idx] = it
        except Exception:
            pass

    def _delete_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        if messagebox.askyesno("Удалить", "Удалить выбранную позицию?"):
            try:
                self.items.pop(idx)
            except Exception:
                pass
            self._refresh_items_view()

    def _save(self):
        status = (self.status_var.get() or "Не заказан").strip()
        order = {
            "title": "",
            "status": status if not self.is_new else "Не заказан",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": self.items.copy(),
        }
        cb = getattr(self, "on_save", None)
        if callable(cb):
            try:
                cb(order)
            except Exception as e:
                messagebox.showerror("Сохранение", f"Не удалось сохранить заказ:\n{e}")
        self._go_back()