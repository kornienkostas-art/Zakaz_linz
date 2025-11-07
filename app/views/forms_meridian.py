import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from datetime import datetime

from app.utils import set_initial_geometry
from app.utils import create_tooltip


class MeridianProductPickerInline(ttk.Frame):
    """Встроенная панель выбора товара с группами + свободный ввод имени и корзиной позиций."""
    def __init__(self, master, db, on_done, on_cancel=None, initial_item: dict | None = None):
        super().__init__(master, style="Card.TFrame", padding=12)
        self.db = db
        self.on_done = on_done
        self.on_cancel = on_cancel
        self._basket: list[dict] = []
        self._build_ui()
        try:
            self._ensure_seed()
        except Exception:
            pass
        if initial_item:
            try:
                name = (initial_item.get("product", "") or "").strip()
                self.free_name_var.set(name)
                self.sel_product_var.set(name)
                self.sel_label.configure(text=name)
                self.sph_var.set(initial_item.get("sph", ""))
                self.cyl_var.set(initial_item.get("cyl", ""))
                self.ax_var.set(initial_item.get("ax", ""))
                self.add_var.set(initial_item.get("add", ""))
                self.d_var.set(initial_item.get("d", ""))
                try:
                    self.qty_var.set(int(initial_item.get("qty", 1)))
                except Exception:
                    self.qty_var.set(1)
                self._basket = [initial_item.copy()]
            except Exception:
                pass
        self._load_tree()
        try:
            self._refresh_basket()
        except Exception:
            pass
        try:
            self._autosize_tree_column()
        except Exception:
            pass
        try:
            self._autosize_basket_columns()
        except Exception:
            pass

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
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

        # Tree (groups/products)
        self.tree = ttk.Treeview(self, show="tree", style="Data.Treeview")
        self.tree.column("#0", width=600, stretch=False)
        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)
        self.tree.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=(0, 8))
        y_scroll.grid(row=1, column=0, rowspan=3, sticky="nse")
        x_scroll.grid(row=4, column=0, sticky="ew", padx=(0, 8))
        self.tree.bind("<Double-1>", self._on_tree_dbl)
        try:
            self.tree.bind("<Configure>", lambda e: self._autosize_tree_column())
            self.bind("<Configure>", lambda e: self._autosize_tree_column())
        except Exception:
            pass

        # Right panel params
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="ew")
        right.columnconfigure(1, weight=0)
        right.columnconfigure(3, weight=0)

        self.sel_product_var = tk.StringVar(value="")
        row_sel = ttk.Frame(right, style="Card.TFrame")
        row_sel.grid(row=0, column=0, columnspan=8, sticky="ew")
        ttk.Label(row_sel, text="Выбранный товар:", style="Subtitle.TLabel").pack(side="left")
        self.sel_label = ttk.Label(row_sel, text="", style="TLabel")
        self.sel_label.pack(side="left", padx=(8, 0))

        # Variables
        self.sph_var = tk.StringVar()
        self.cyl_var = tk.StringVar()
        self.ax_var = tk.StringVar()
        self.add_var = tk.StringVar()
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

        def _nudge_int_step(var: tk.StringVar, min_v: int, max_v: int, step: int, direction: int):
            txt = (var.get() or "").replace(",", ".").strip()
            if txt == "":
                cur = min_v
            else:
                try:
                    cur = int(float(txt))
                except ValueError:
                    cur = min_v
            cur += step * (1 if direction >= 0 else -1)
            cur = max(min_v, min(max_v, cur))
            cur = int(round(cur / float(step)) * step)
            cur = max(min_v, min(max_v, cur))
            var.set(str(cur))

        # Replace comma with dot in decimal entries
        def _normalize_decimal(var: tk.StringVar):
            try:
                txt = (var.get() or "")
                if "," in txt:
                    var.set(txt.replace(",", "."))
            except Exception:
                pass

        # SPH row (− / input / +)
        ttk.Label(right, text="SPH (−30…+30, 0.25)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        sph_row = ttk.Frame(right); sph_row.grid(row=1, column=1, sticky="w", pady=(6, 0))
        ttk.Button(sph_row, text="−", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, -1)).grid(row=0, column=0)
        sph_entry = ttk.Entry(sph_row, textvariable=self.sph_var, width=6, justify="center")
        sph_entry.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(sph_row, text="+", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, +1)).grid(row=0, column=2)
        # Normalize comma to dot on typing and snap to 0.25 on focus out
        sph_entry.bind("<KeyRelease>", lambda e: _normalize_decimal(self.sph_var))
        sph_entry.bind("<FocusOut>", lambda e: self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True)))

        # CYL row (− / input / +)
        ttk.Label(right, text="CYL (−10…+10, 0.25)").grid(row=1, column=2, sticky="w", pady=(6, 0))
        cyl_row = ttk.Frame(right); cyl_row.grid(row=1, column=3, sticky="w", pady=(6, 0))
        ttk.Button(cyl_row, text="−", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, -1)).grid(row=0, column=0)
        cyl_entry = ttk.Entry(cyl_row, textvariable=self.cyl_var, width=6, justify="center")
        cyl_entry.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(cyl_row, text="+", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, +1)).grid(row=0, column=2)
        cyl_entry.bind("<KeyRelease>", lambda e: _normalize_decimal(self.cyl_var))
        cyl_entry.bind("<FocusOut>", lambda e: self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)))

        # AX row adjacent to label
        ax_row = ttk.Frame(right); ax_row.grid(row=1, column=4, sticky="w", pady=(6, 0))
        ttk.Label(ax_row, text="AX (0…180)").pack(side="left")
        ttk.Entry(ax_row, textvariable=self.ax_var, width=6, justify="center").pack(side="left", padx=(4, 0))

        # Second line: ADD (−/+/input) then D (−/+/input), then qty
        ttk.Label(right, text="ADD (0…10, шаг 0.25)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        add_row = ttk.Frame(right); add_row.grid(row=2, column=1, sticky="w", pady=(6, 0))
        ttk.Button(add_row, text="−", width=3, command=lambda: _nudge(self.add_var, 0.0, 10.0, 0.25, -1)).grid(row=0, column=0)
        ttk.Entry(add_row, textvariable=self.add_var, width=6, justify="center").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(add_row, text="+", width=3, command=lambda: _nudge(self.add_var, 0.0, 10.0, 0.25, +1)).grid(row=0, column=2)

        ttk.Label(right, text="D (40…90, шаг 5)").grid(row=2, column=2, sticky="w", pady=(6, 0))
        d_row = ttk.Frame(right); d_row.grid(row=2, column=3, sticky="w", pady=(6, 0))
        ttk.Button(d_row, text="−", width=3, command=lambda: _nudge_int_step(self.d_var, 40, 90, 5, -1)).grid(row=0, column=0)
        ttk.Entry(d_row, textvariable=self.d_var, width=6, justify="center").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(d_row, text="+", width=3, command=lambda: _nudge_int_step(self.d_var, 40, 90, 5, +1)).grid(row=0, column=2)

        ttk.Label(right, text="Количество (1…20)").grid(row=2, column=4, sticky="w", padx=(12, 0), pady=(6, 0))
        ttk.Spinbox(right, from_=1, to=20, textvariable=self.qty_var, width=7).grid(row=2, column=5, sticky="w", pady=(6, 0))

        # Basket controls
        ctl = ttk.Frame(self, style="Card.TFrame")
        ctl.grid(row=2, column=1, sticky="ew", pady=(8, 4))
        ttk.Button(ctl, text="Добавить в список", style="Accent.TButton", command=self._add_to_basket).pack(side="left")
        ttk.Button(ctl, text="Удалить выбранное", style="Menu.TButton", command=self._remove_selected).pack(side="left", padx=(8, 0))
        ttk.Button(ctl, text="Очистить список", style="Menu.TButton", command=self._clear_basket).pack(side="left", padx=(8, 0))

        # Basket table
        cols = ("product", "sph", "cyl", "ax", "add", "d", "qty")
        self.basket = ttk.Treeview(self, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "add": "ADD", "d": "D (мм)", "qty": "Кол-во"}
        widths = {"product": 340, "sph": 70, "cyl": 70, "ax": 60, "add": 70, "d": 70, "qty": 70}
        for c in cols:
            self.basket.heading(c, text=headers[c], anchor="w")
            self.basket.column(c, width=widths[c], anchor="w", stretch=True)
        y2 = ttk.Scrollbar(self, orient="vertical", command=self.basket.yview)
        self.basket.configure(yscroll=y2.set)
        self.basket.grid(row=3, column=1, sticky="nsew")
        y2.grid(row=3, column=1, sticky="nse")
        try:
            self.basket.bind("<Configure>", lambda e: self._autosize_basket_columns())
        except Exception:
            pass

        # Footer
        foot = ttk.Frame(self, style="Card.TFrame")
        foot.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(foot, text="Добавить в заказ", style="Menu.TButton", command=self._done).pack(side="right")
        ttk.Button(foot, text="Отмена", style="Menu.TButton", command=self._cancel).pack(side="right", padx=(8, 0))

    def _ensure_seed(self):
        try:
            groups = self.db.list_product_groups_meridian()
            prods = self.db.list_products_meridian()
        except Exception:
            return
        if groups or prods:
            return

        def clean(s: str) -> str:
            return " ".join((s or "").split())

        seed = [
            ("ПОЛИМЕРНЫЕ ЛИНЗЫ", ["1.49 SPH", "1.56 HI-MAX HMC"]),
            ("МИНЕРАЛЬНЫЕ ЛИНЗЫ", ["1.523 GLASS GREY", "1.523 GLASS BROWN"]),
        ]
        for gname, items in seed:
            gid = self.db.add_product_group_meridian(clean(gname))
            for nm in items:
                self.db.add_product_meridian(clean(nm), gid)

    def _load_tree(self):
        term = (self.search_var.get() or "").strip().lower()
        self.tree.delete(*self.tree.get_children())

        # Fetch groups and build parent->children map
        try:
            groups = self.db.list_product_groups_meridian()
        except Exception:
            groups = []
        try:
            all_products = self.db.list_products_meridian()
        except Exception:
            all_products = []

        if not groups:
            # Fallback: flat list of all products
            root = self.tree.insert("", "end", text="Все товары", open=True, tags=("group", "gid:None"))
            any_found = False
            for p in all_products:
                name = p.get("name", "") or ""
                if term and term not in name.lower():
                    continue
                any_found = True
                self.tree.insert(root, "end", text=name, tags=("product", f"pid:{p.get('id')}", "gid:None"))
            if term and not any_found:
                self.tree.insert(root, "end", text="(Ничего не найдено)", tags=("info",))
            try:
                self._autosize_tree_column()
            except Exception:
                pass
            return

        # Build group tree
        children_map: dict[int | None, list[dict]] = {}
        for g in groups:
            children_map.setdefault(g.get("parent_id"), []).append(g)
        # Sort siblings by sort_order then name
        for k in list(children_map.keys()):
            children_map[k].sort(key=lambda x: (x.get("sort_order", 0), (x.get("name", "") or "").lower()))

        # Helper to insert group nodes recursively; returns True if any match added
        def add_group_node(parent_iid: str, g: dict) -> bool:
            gid = g["id"]
            node_iid = self.tree.insert(parent_iid, "end", text=g["name"], open=bool(term), tags=("group", f"gid:{gid}"))
            any_added = False

            # Insert child groups first
            for child in children_map.get(gid, []):
                if add_group_node(node_iid, child):
                    any_added = True

            # Then insert products of this group
            try:
                prods = self.db.list_products_meridian_by_group(gid)
            except Exception:
                prods = []
            for p in prods:
                name = (p.get("name", "") or "")
                if term and term not in name.lower():
                    continue
                self.tree.insert(node_iid, "end", text=name, tags=("product", f"pid:{p['id']}", f"gid:{gid}"))
                any_added = True

            # If nothing added and term is set, remove empty branch
            if term and not any_added:
                try:
                    self.tree.delete(node_iid)
                except Exception:
                    pass
                return False
            return True

        any_found_total = False
        # Create a virtual root container to hold top-level groups
        for top in children_map.get(None, []):
            if add_group_node("", top):
                any_found_total = True

        if term and not any_found_total:
            self.tree.insert("", "end", text="(Ничего не найдено)", tags=("info",))
        try:
            self._autosize_tree_column()
        except Exception:
            pass

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
        add = self._snap(self.add_var.get(), 0.0, 10.0, 0.25, allow_empty=True)
        d = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
        if d != "":
            try:
                iv = int(d)
                iv = int(round(iv / 5.0) * 5)
                d = str(iv)
            except Exception:
                pass
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)

        merged = False
        for it in self._basket:
            if it["product"] == product and it["sph"] == sph and it["cyl"] == cyl and it["ax"] == ax and (it.get("add","") == add) and it["d"] == d:
                try:
                    it["qty"] = str(int(it.get("qty", "0")) + int(qty))
                except Exception:
                    it["qty"] = str(qty)
                merged = True
                break
        if not merged:
            item = {"product": product, "sph": sph, "cyl": cyl, "ax": ax, "add": add, "d": d, "qty": qty}
            self._basket.append(item)
        self._refresh_basket()

        # Reset inputs
        try:
            self.sph_var.set("")
            self.cyl_var.set("")
            self.ax_var.set("")
            self.add_var.set("")
            self.d_var.set("")
            self.qty_var.set(1)
        except Exception:
            pass

    def _refresh_basket(self):
        for i in self.basket.get_children():
            self.basket.delete(i)
        for idx, it in enumerate(self._basket):
            try:
                from app.utils import format_signed
                sph = format_signed(it.get("sph",""))
                cyl = format_signed(it.get("cyl",""))
                add = format_signed(it.get("add",""))
            except Exception:
                sph = it.get("sph",""); cyl = it.get("cyl",""); add = it.get("add","")
            self.basket.insert("", "end", iid=str(idx), values=(it["product"], sph, cyl, it["ax"], add, it["d"], it["qty"]))
        try:
            self._autosize_basket_columns()
        except Exception:
            pass

    def _remove_selected(self):
        sel = self.basket.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите позицию в списке.")
            return
        try:
            idx = int(sel[0])
        except Exception:
            return
        if idx < 0 or idx >= len(self._basket):
            return
        del self._basket[idx]
        self._refresh_basket()

    def _clear_basket(self):
        if not self._basket:
            return
        if messagebox.askyesno("Очистить", "Очистить список?"):
            self._basket.clear()
            self._refresh_basket()

    # Autosize helpers
    def _autosize_tree_column(self):
        try:
            f = tkfont.nametofont("TkDefaultFont")
        except Exception:
            f = tkfont.Font()
        padding = 32
        maxw = f.measure("Группы / Товары") + padding
        try:
            for iid in self.tree.get_children(""):
                text = str(self.tree.item(iid, "text") or "")
                w = f.measure(text) + padding
                if w > maxw:
                    maxw = w
                for child in self.tree.get_children(iid):
                    t = str(self.tree.item(child, "text") or "")
                    w2 = f.measure(t) + padding + 24
                    if w2 > maxw:
                        maxw = w2
        except Exception:
            pass
        width = max(240, int(maxw))
        try:
            self.tree.column("#0", width=width, minwidth=width, stretch=False)
        except Exception:
            pass
        try:
            self.columnconfigure(0, minsize=width + 16)
        except Exception:
            pass

    def _autosize_basket_columns(self):
        try:
            f = tkfont.nametofont("TkDefaultFont")
        except Exception:
            f = tkfont.Font()
        padding = 24
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "add": "ADD", "d": "D (мм)", "qty": "Кол-во"}
        cols = ("product", "sph", "cyl", "ax", "add", "d", "qty")
        max_px = {}
        for c in cols:
            max_px[c] = max(60, f.measure(headers[c]) + padding)
        for iid in self.basket.get_children(""):
            vals = self.basket.item(iid, "values") or ()
            for i, c in enumerate(cols):
                if i >= len(vals):
                    continue
                w = f.measure(str(vals[i])) + padding
                if w > max_px[c]:
                    max_px[c] = w
        try:
            avail = max(300, self.basket.winfo_width())
        except Exception:
            avail = sum(max_px.values())
        total = sum(max_px.values())
        if total > avail:
            ratio = avail / total
            for c in cols:
                max_px[c] = max(60, int(max_px[c] * ratio))
        for c in cols:
            self.basket.column(c, width=max_px[c], minwidth=60, stretch=True)

    def _done(self):
        items = list(self._basket)
        try:
            if callable(self.on_done):
                self.on_done(items)
        except Exception:
            pass
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._basket.clear()
        try:
            self._refresh_basket()
        except Exception:
            pass
        try:
            if callable(self.on_cancel):
                self.on_cancel()
        except Exception:
            pass

    def _cancel(self):
        if callable(self.on_cancel):
            self.on_cancel()


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
        # Use grid to avoid unexpected top empty space
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        self._card = card
        self._picker_panel = None
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)

        if not self.is_new:
            header = ttk.Frame(card, style="Card.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            ttk.Label(header, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Combobox(header, textvariable=self.status_var, values=self.STATUSES, height=4).grid(row=1, column=0, sticky="ew")
            header.columnconfigure(0, weight=1)

        ttk.Separator(card).grid(row=1, column=0, sticky="ew", pady=(12, 12))

        self._items_frame = ttk.Frame(card, style="Card.TFrame")
        self._items_frame.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(2, weight=1)

        cols = ("product", "sph", "cyl", "ax", "add", "d", "qty")
        self.items_tree = ttk.Treeview(self._items_frame, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "add": "ADD", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 240, "sph": 90, "cyl": 90, "ax": 90, "add": 90, "d": 90, "qty": 120}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(self._items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y_scroll.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        self._items_frame.columnconfigure(0, weight=1)
        self._items_frame.rowconfigure(0, weight=1)

        self._items_toolbar = ttk.Frame(card, style="Card.TFrame")
        self._items_toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(self._items_toolbar, text="Добавить позицию", style="Menu.TButton", command=self._add_item).pack(side="left")
        ttk.Button(self._items_toolbar, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left", padx=(8, 0))

        self._footer_btns = ttk.Frame(card, style="Card.TFrame")
        self._footer_btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(self._footer_btns, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(self._footer_btns, text="Отмена", style="Menu.TButton", command=self._go_back).pack(side="right", padx=(8, 0))

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
                try:
                    from app.utils import format_signed
                    sph = format_signed(it.get("sph",""))
                    cyl = format_signed(it.get("cyl",""))
                    add = format_signed(it.get("add",""))
                except Exception:
                    sph = it.get("sph",""); cyl = it.get("cyl",""); add = it.get("add","")
                values = (it.get("product", ""), sph, cyl, it.get("ax", ""), add, it.get("d", ""), it.get("qty", ""))
                self.items_tree.insert("", "end", iid=str(idx   pass

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
        return getattr(self, "db", None)

    def _add_item(self):
        if self.db:
            def _cancel():
                try:
                    if self._picker_panel is not None:
                        self._picker_panel.destroy()
                except Exception:
                    pass
                self._picker_panel = None
                try:
                    if hasattr(self, "_items_frame"):
                        self._items_frame.grid()
                    if hasattr(self, "_items_toolbar"):
                        self._items_toolbar.grid()
                    if hasattr(self, "_footer_btns"):
                        self._footer_btns.grid()
                    try:
                        self._card.rowconfigure(5, weight=0)
                        self._card.rowconfigure(2, weight=1)
                    except Exception:
                        pass
                except Exception:
                    pass
            def on_done(items):
                self.items.extend(items)
                self._refresh_items_view()
                _cancel()
            try:
                if self._picker_panel is not None:
                    self._picker_panel.destroy()
            except Exception:
                pass
            try:
                if hasattr(self, "_items_frame"):
                    self._items_frame.grid_remove()
                if hasattr(self, "_items_toolbar"):
                    self._items_toolbar.grid_remove()
                if hasattr(self, "_footer_btns"):
                    self._footer_btns.grid_remove()
                try:
                    self._card.rowconfigure(2, weight=0)
                    self._card.rowconfigure(5, weight=1)
                except Exception:
                    pass
            except Exception:
                pass
            self._picker_panel = MeridianProductPickerInline(self._card, self.db, on_done=on_done, on_cancel=_cancel)
            try:
                self._picker_panel.grid(row=5, column=0, sticky="nsew", pady=(0, 0))
            except Exception:
                self._picker_panel.pack(fill="both", expand=True, pady=(0, 0))
            return
        messagebox.showerror("База данных", "DB недоступна для добавления позиции.")

    def _edit_item(self):
        messagebox.showinfo("Редактирование", "Редактирование позиции отключено.")
        return

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
