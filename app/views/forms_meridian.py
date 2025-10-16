import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.utils import set_initial_geometry


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

    def _add_item(self):
        # Load product list from DB if available
        products = []
        try:
            if hasattr(self, "db") and self.db:
                products = self.db.list_products()
        except Exception:
            products = []
        MeridianItemForm(self, products=products, on_save=lambda it: (self.items.append(it), self._refresh_items_view()))

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
        def _centered_signed_values(max_abs: float) -> list[str]:
            step = 0.25
            neg = [-(i * step) for i in range(1, int(max_abs / step) + 1)]
            pos = [(i * step) for i in range(1, int(max_abs / step) + 1)]
            return [f"{v:+.2f}" for v in neg] + ["+0.00"] + [f"{v:+.2f}" for v in pos]
        self.sph_entry = ttk.Combobox(
            card,
            textvariable=self.sph_var,
            values=_centered_signed_values(30.0),
        )
        self.sph_entry.grid(row=3, column=0, sticky="ew")
        self.sph_entry.configure(postcommand=lambda: (self.sph_entry.set("+0.00") if (self.sph_var.get() or "").strip()=="" else None))
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))

        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=2, column=1, sticky="w", pady=(8, 0))
        self.cyl_entry = ttk.Combobox(
            card,
            textvariable=self.cyl_var,
            values=_centered_signed_values(10.0),
        )
        self.cyl_entry.grid(row=3, column=1, sticky="ew")
        self.cyl_entry.configure(postcommand=lambda: (self.cyl_entry.set("+0.00") if (self.cyl_var.get() or "").strip()=="" else None))
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=5, column=0, sticky="ew")
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))

        ttk.Label(card, text="D (40…90, шаг 5) — в экспорте добавляется 'мм'", style="Subtitle.TLabel").grid(row=4, column=1, sticky="w", pady=(8, 0))
        self.d_entry = ttk.Combobox(
            card,
            textvariable=self.d_var,
            values=[str(v) for v in range(40, 91, 5)],
        )
        self.d_entry.grid(row=5, column=1, sticky="ew")
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
        products = []
        try:
            if self.db:
                products = self.db.list_products_meridian()
        except Exception:
            products = []
        MeridianItemForm(self, products=products, on_save=lambda it: (self.items.append(it), self._refresh_items_view()))

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