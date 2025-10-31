import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class MeridianOrderEditorView(ttk.Frame):
    """Редактор заказа 'Меридиан' с каталогом/поиском, снэпом параметров и таблицей позиций."""

    STATUSES = ["Не заказан", "Заказан"]

    def __init__(self, master: tk.Tk, db, on_back, on_save, initial: dict | None = None):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back
        self.on_save = on_save

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # Данные
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.items: list[dict] = [it.copy() for it in (initial or {}).get("items", [])]

        # Текущее состояние поиска
        self.search_var = tk.StringVar()

        self._build_ui()
        self._load_tree()
        self._refresh_items_view()

    # ---------- UI ----------

    def _build_ui(self):
        # Верхняя панель
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")
        ttk.Button(toolbar, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")

        # Центральная область
        body = ttk.Frame(self, style="Card.TFrame", padding=12)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(2, weight=1)

        # Левая колонка: Поиск + дерево каталога
        left = ttk.Frame(body, style="Card.TFrame")
        left.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="Поиск", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ent = ttk.Entry(left, textvariable=self.search_var)
        ent.grid(row=1, column=0, sticky="ew", pady=(2, 8))
        ent.bind("<KeyRelease>", lambda e: self._load_tree())

        self.tree = ttk.Treeview(left, columns=("name",), show="tree", style="Data.Treeview")
        self.tree.grid(row=2, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        y_scroll.grid(row=2, column=1, sticky="ns")
        left.rowconfigure(2, weight=1)
        self.tree.bind("<Double-1>", self._on_tree_double)

        # Правая колонка: статус и форма ввода позиции
        ttk.Label(body, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Combobox(body, textvariable=self.status_var, values=self.STATUSES, height=4, width=18).grid(row=1, column=1, sticky="w")

        form = ttk.Frame(body, style="Card.TFrame")
        form.grid(row=2, column=1, sticky="new", pady=(12, 8))
        for i in range(14):
            form.columnconfigure(i, weight=0)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Товар").grid(row=0, column=0, sticky="w")
        self.product_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.product_var).grid(row=0, column=1, sticky="ew", padx=(6, 12))

        # SPH
        ttk.Label(form, text="SPH").grid(row=0, column=2, sticky="w", padx=(6, 0))
        self.sph_var = tk.StringVar()
        sph_e = ttk.Entry(form, textvariable=self.sph_var, width=10)
        sph_e.grid(row=0, column=3, sticky="w")
        ttk.Button(form, text="−", width=2, command=lambda: self._nudge(self.sph_var, -0.25, -30, 30, 0.25, True)).grid(row=0, column=4, padx=(4, 0))
        ttk.Button(form, text="+", width=2, command=lambda: self._nudge(self.sph_var, +0.25, -30, 30, 0.25, True)).grid(row=0, column=5, padx=(2, 8))
        sph_e.bind("<FocusOut>", lambda e: self._snap(self.sph_var, -30, 30, 0.25, True))

        # CYL
        ttk.Label(form, text="CYL").grid(row=0, column=6, sticky="w")
        self.cyl_var = tk.StringVar()
        cyl_e = ttk.Entry(form, textvariable=self.cyl_var, width=10)
        cyl_e.grid(row=0, column=7, sticky="w")
        ttk.Button(form, text="−", width=2, command=lambda: self._nudge(self.cyl_var, -0.25, -10, 10, 0.25, True)).grid(row=0, column=8, padx=(4, 0))
        ttk.Button(form, text="+", width=2, command=lambda: self._nudge(self.cyl_var, +0.25, -10, 10, 0.25, True)).grid(row=0, column=9, padx=(2, 8))
        cyl_e.bind("<FocusOut>", lambda e: self._snap(self.cyl_var, -10, 10, 0.25, True))

        # AX
        ttk.Label(form, text="AX").grid(row=0, column=10, sticky="w")
        self.ax_var = tk.StringVar()
        ax_e = ttk.Entry(form, textvariable=self.ax_var, width=6)
        ax_e.grid(row=0, column=11, sticky="w", padx=(4, 12))
        ax_e.bind("<FocusOut>", lambda e: self._snap_int(self.ax_var, 0, 180))

        # ADD
        ttk.Label(form, text="ADD").grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(8, 0))
        self.add_var = tk.StringVar()
        add_e = ttk.Entry(form, textvariable=self.add_var, width=10)
        add_e.grid(row=1, column=3, sticky="w", pady=(8, 0))
        ttk.Button(form, text="−", width=2, command=lambda: self._nudge(self.add_var, -0.25, 0, 10, 0.25, False)).grid(row=1, column=4, padx=(4, 0), pady=(8, 0))
        ttk.Button(form, text="+", width=2, command=lambda: self._nudge(self.add_var, +0.25, 0, 10, 0.25, False)).grid(row=1, column=5, padx=(2, 8), pady=(8, 0))
        add_e.bind("<FocusOut>", lambda e: self._snap(self.add_var, 0, 10, 0.25, False))

        # D и Количество
        ttk.Label(form, text="D (мм)").grid(row=1, column=6, sticky="w", pady=(8, 0))
        self.d_var = tk.StringVar()
        d_e = ttk.Entry(form, textvariable=self.d_var, width=8)
        d_e.grid(row=1, column=7, sticky="w", padx=(4, 12), pady=(8, 0))
        d_e.bind("<FocusOut>", lambda e: self._snap(self.d_var, 40, 90, 5.0, False))

        ttk.Label(form, text="Кол-во").grid(row=1, column=10, sticky="w", pady=(8, 0))
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=99, textvariable=self.qty_var, width=6).grid(row=1, column=11, sticky="w", padx=(4, 0), pady=(8, 0))

        ttk.Button(body, text="Добавить позицию", style="Menu.TButton", command=self._add_item).grid(row=3, column=1, sticky="w", pady=(8, 8))

        # Таблица позиций
        table = ttk.Frame(body, style="Card.TFrame")
        table.grid(row=4, column=0, columnspan=2, sticky="nsew")
        body.rowconfigure(4, weight=1)

        cols = ("product", "sph", "cyl", "ax", "add", "d", "qty")
        self.items_tree = ttk.Treeview(table, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "add": "ADD", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 360, "sph": 90, "cyl": 90, "ax": 80, "add": 90, "d": 90, "qty": 110}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)

        y2 = ttk.Scrollbar(table, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y2.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y2.grid(row=0, column=1, sticky="ns")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)

        btns = ttk.Frame(body, style="Card.TFrame")
        btns.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(btns, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left")

    # ---------- Catalog/tree ----------

    def _load_tree(self):
        try:
            self.tree.delete(*self.tree.get_children())
            q = (self.search_var.get() or "").strip().lower()

            # Загружаем группы и товары
            groups_by_parent: dict[object, list] = {}
            def fetch(pid):
                try:
                    rows = self.db.list_product_groups_meridian_by_parent(pid) if self.db else []
                except Exception:
                    rows = []
                groups_by_parent[pid] = rows
                for g in rows:
                    fetch(g["id"])
            fetch(None)

            def add_group(parent_node, gid):
                # Товары без группы
                if gid is None:
                    try:
                        ungrouped = self.db.list_products_meridian_by_group(None)
                    except Exception:
                        ungrouped = []
                    if ungrouped:
                        node = self.tree.insert(parent_node, "end", text="Без группы", open=True, tags=("group", "gid:None"))
                        for p in ungrouped:
                            name = p["name"]
                            if q and q not in name.lower():
                                continue
                            self.tree.insert(node, "end", text=name, tags=("product", f"pid:{p['id']}"))
                # Дочерние группы
                for g in groups_by_parent.get(gid, []):
                    name = g["name"]
                    node = self.tree.insert(parent_node, "end", text=name, open=False, tags=("group", f"gid:{g['id']}"))
                    # Товары этой группы
                    try:
                        prods = self.db.list_products_meridian_by_group(g["id"])
                    except Exception:
                        prods = []
                    for p in prods:
                        name = p["name"]
                        if q and q not in name.lower():
                            continue
                        self.tree.insert(node, "end", text=name, tags=("product", f"pid:{p['id']}"))
                    add_group(node, g["id"])

            add_group("", None)
        except Exception:
            pass

    def _on_tree_double(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return
            tags = set(self.tree.item(item, "tags") or [])
            if "product" in tags:
                name = self.tree.item(item, "text")
                self.product_var.set(name)
        except Exception:
            pass

    # ---------- Snapping/validation ----------

    @staticmethod
    def _snap(var: tk.StringVar, min_v: float, max_v: float, step: float, allow_sign: bool):
        s = (var.get() or "").strip().replace(",", ".")
        if s == "":
            return
        try:
            x = float(s)
        except ValueError:
            var.set("")
            return
        x = max(min_v, min(max_v, x))
        # к ближайшему шагу
        k = round(x / step)
        x = k * step
        if allow_sign:
            var.set(f"{x:.2f}")
        else:
            var.set(f"{x:.2f}".lstrip("+"))

    @staticmethod
    def _snap_int(var: tk.StringVar, min_v: int, max_v: int):
        s = (var.get() or "").strip()
        if s == "":
            return
        try:
            x = int(round(float(s)))
        except ValueError:
            var.set("")
            return
        x = max(min_v, min(max_v, x))
        var.set(str(x))

    def _nudge(self, var: tk.StringVar, delta: float, min_v: float, max_v: float, step: float, allow_sign: bool):
        s = (var.get() or "").strip().replace(",", ".")
        if s == "":
            s = "0"
        try:
            x = float(s)
        except ValueError:
            x = 0.0
        x += delta
        x = max(min_v, min(max_v, x))
        k = round(x / step)
        x = k * step
        if allow_sign:
            var.set(f"{x:.2f}")
        else:
            var.set(f"{x:.2f}".lstrip("+"))

    # ---------- Items table ----------

    def _refresh_items_view(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, it in enumerate(self.items):
            values = (
                it.get("product", ""),
                it.get("sph", ""),
                it.get("cyl", ""),
                it.get("ax", ""),
                it.get("add", ""),
                it.get("d", ""),
                it.get("qty", ""),
            )
            self.items_tree.insert("", "end", iid=str(idx), values=values)

    def _add_item(self):
        name = (self.product_var.get() or "").strip()
        if not name:
            messagebox.showinfo("Позиция", "Выберите товар или введите название.")
            return
        def norm(v): return (v or "").strip()
        item = {
            "product": name,
            "sph": norm(self.sph_var.get()),
            "cyl": norm(self.cyl_var.get()),
            "ax": norm(self.ax_var.get()),
            "add": norm(self.add_var.get()),
            "d": norm(self.d_var.get()),
            "qty": str(max(1, int(self.qty_var.get() or 1))),
        }
        # Объединение одинаковых позиций (по всем параметрам, кроме qty)
        for it in self.items:
            same = all((it.get(k, "") or "") == item.get(k, "") for k in ("product", "sph", "cyl", "ax", "add", "d"))
            if same:
                try:
                    it["qty"] = str(int(it.get("qty", "1") or "1") + int(item["qty"]))
                except Exception:
                    it["qty"] = item["qty"]
                break
        else:
            self.items.append(item)
        self._refresh_items_view()

    def _delete_item(self):
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showinfo("Удалить", "Выберите позицию.")
            return
        try:
            idx = int(sel[0])
        except Exception:
            return
        if 0 <= idx < len(self.items):
            del self.items[idx]
            self._refresh_items_view()

    # ---------- Save/Back ----------

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _save(self):
        order = {
            "status": (self.status_var.get() or "Не заказан").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": self.items.copy(),
        }
        if callable(self.on_save):
            try:
                self.on_save(order)
            except Exception as e:
                messagebox.showerror("Сохранение", f"Не удалось сохранить заказ:\n{e}")
        self._go_back()
