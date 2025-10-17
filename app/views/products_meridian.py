import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from app.db import AppDB  # type hint only


def _clean_spaces(name: str) -> str:
    return " ".join((name or "").split())


MERIDIAN_SEED = [
    ("ПОЛИМЕРНЫЕ ЛИНЗЫ", [
        "1.81 ASPHERIC HMC KOREA",
        "1.76 SUPER+ASPHERIC, BLUE KOREA",
        "1.74 ASPHERIC HMC KOREA",
        "1.67 ASPHERIC HMC/EMI KOREA",
        "1.67 ASPHERIC KOREA",
        "1.67 AS BLUE BLOCKER KOREA",
        "1.67 DOUBLE ASPHERIC, BLUE BLOCKER KOREA",
        "1.61 ASPHERIC HMC/EMI",
        "1.61 BLUE LIGHT BLOCKER",
        "1.61 SPH HMC MR-8",
        "1.61 BLUE LIGHT LOCKER HARD CLEAN COATED",
        "1.61 BLUE LIGHT BLOCKER MR-8",
        "1.61 AS MR-8",
        "1.61 PERIFOCAL KOREA",
        "1.61 ANTI-FOG AR UV420",
        "1.61 Defocus BLUE LIGHT BLOCKER UV420",
        "1.61 STELLEST LENSES",
        "1.56 BLUE LIGHT BLOCKER",
        "1.56 AS COMPUTRON",
        "1.56 HI-MAX HMC",
        "1.56 KINDER HMC",
        "1.56 GOLD HMC/EMI",
        "1.56 ASPHERIC NEW MIRACLE HMC/EMI",
        "1.56 ANTI-FOG BLUE LIGHT BLOCKER",
        "1.56 SPH под ПОКРАСКУ",
        "1.49 CR-39 глаукомные",
        "1.49 SPH",
    ]),
    ("ПОЛИМЕРНЫЕ ПОЛЯРИЗАЦИОННЫЕ ЛИНЗЫ", [
        "1.61 POLARIZED GREY HC",
        "1.61 POLARIZED Brown HC",
        "1.56 POLARIZED GREY",
        "1.56 POLARIZED Brown",
        "1.56 POLARIZED HMC GREY",
        "1.56 POLARIZED HMC Brown",
        "1.56 MIRROR POLARIZED",
    ]),
    ("ПОЛИМЕРНЫЕ ТОНИРОВАННЫЕ ЛИНЗЫ", [
        "1.61 AS HI-MAX НМС 80% GREY",
        "1.61 AS HI-MAX НМС 80% Brown",
        "1.56 HI-MAX 20% GREY",
        "1.56 HI-MAX 20% Brown",
        "1.56 HI-MAX 50% GREY",
        "1.56 HI-MAX 50% Brown",
        "1.56 GRADIENT GREY",
        "1.56 GRADIENT Brown",
    ]),
    ("ПОЛИМЕРНЫЕ ФОТОХРОМНЫЕ ЛИНЗЫ", [
        "1.74 PHOTOCHROMIC HMC GREY",
        "1.74 PHOTOCHROMIC HMC Brown",
        "1.67 PHOTOCHROMIC BLUE BLOCKER GREY",
        "1.67 PHOTOCHROMIC BLUE BLOCKER Brown",
        "1.61 MR-8 PHOTOCHROMIC BLUE BLOCKER KOREA GREY",
        "1.61 MR-8 PHOTOCHROMIC BLUE BLOCKER KOREA Brown",
        "1.61 PHOTOCHROMIC HMC GREY",
        "1.61 PHOTOCHROMIC HMC Brown",
        "1.61 TRANSITIONS BLUE BLOCKER PHOTO GREY",
        "1.56 PHOTOCHROMIC GREY",
        "1.56 PHOTOCHROMIC Brown",
        "1.56 PHOTOCHROMIC TRANSITIONS GREY",
        "1.56 PHOTOCHROMIC TRANSITIONS Brown",
        "1.56 TRANSITIONS BLUE LIGHT BLOCKER PHOTO GREY",
        "1.56 PHOTOCHROMIC HMC GREY",
        "1.56 PHOTOCHROMIC HMC Brown",
        "1.56 POLARIZED PHOTOCHROMIC GREY HMC",
    ]),
    ("ПОЛИМЕРНЫЕ БИФОКАЛЬНЫЕ, ПРОГРЕССИВНЫЕ ЛИНЗЫ", [
        "1.56 PROGRESSIVE",
        "1.56 PROGRESSIVE HMC",
        "1.59 POLYCARBONATE PROGRESSIVE HMC",
        "1.56 OFFICE BLUE LIGHT BLOCKER",
        "1.56 OFFICE HMC",
        "1.56 BIFOCAL F TOP HMC",
        "1.49 BIFOCAL F TOP",
        "1.56 PHOTOCHROMIC PROGRESSIVE GREY",
        "1.56 PHOTOCHROMIC PROGRESSIVE Brown",
        "1.56 PHOTOCHROMIC BIFOCAL GREY",
        "1.56 PHOTOCHROMIC BIFOCAL Brown",
    ]),
    ("ПОЛИМЕРНЫЕ ЛИНЗЫ ДЛЯ ВОЖДЕНИЯ", [
        "1.61 AS DRIVING LENS BLUE LOCKER (AR/blue) KOREA",
        "1.56 YELLOW FARA EMI (AR/blue)",
        "1.56 YELLOW-FARA POLARIZED (AR/blue)",
        "1.56 YELLOW-FARA PHOTOCHROMIC GREY (AR/green)",
    ]),
    ("ПОЛИКАРБОНАТНЫЕ ЛИНЗЫ", [
        "1.59 POLYCARBONAT HMC",
        "1.59 POLYCARBONAT",
        "1.59 POLYCARBONAT BLUE LIGHT BLOCKER",
        "1.59 POLYCARBONAT PHOTOCHROMIC GREY",
    ]),
    ("МИНЕРАЛЬНЫЕ ЛИНЗЫ", [
        "1.71 GLASS COMPUTRON GREEN",
        "1.71 GLASS COMPUTRON BLUE",
        "1.71 WHITE GLASS HI-INDEX",
        "1.523 WHITE GLASS",
        "1.523 GLASS PHOTOCHROMIC GREY",
        "1.523 GLASS PHOTOCHROMIC BROWN",
        "1.523 GLASS GREY",
        "1.523 GLASS BROWN",
        "1.523 GLASS GREEN",
        "1.523 GLASS YELLOW FARA",
        "1.523 GLASS BIFOCAL F-TOP",
    ]),
]


class ProductsMeridianView(ttk.Frame):
    """Справочник товаров для Меридиан (с группами и порядком)."""
    def __init__(self, master: tk.Tk, db: AppDB | None, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self._build_ui()
        self._reload(initial_seed=True)

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)

        header = ttk.Label(card, text="Товары (Меридиан): группы и позиции", style="Title.TLabel")
        header.grid(row=0, column=0, sticky="w", columnspan=3)
        ttk.Separator(card).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 12))

        # Actions
        bar = ttk.Frame(card, style="Card.TFrame")
        bar.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Button(bar, text="Добавить группу", style="Menu.TButton", command=self._add_group).pack(side="left")
        ttk.Button(bar, text="Переименовать группу", style="Menu.TButton", command=self._rename_group).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить группу", style="Menu.TButton", command=self._delete_group).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Группа ↑", style="Menu.TButton", command=lambda: self._move_group(-1)).pack(side="left", padx=(16, 0))
        ttk.Button(bar, text="Группа ↓", style="Menu.TButton", command=lambda: self._move_group(+1)).pack(side="left", padx=(8, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(bar, text="Добавить товар", style="Menu.TButton", command=self._add_product).pack(side="left")
        ttk.Button(bar, text="Редактировать товар", style="Menu.TButton", command=self._edit_product).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить товар", style="Menu.TButton", command=self._delete_product).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Товар ↑", style="Menu.TButton", command=lambda: self._move_product(-1)).pack(side="left", padx=(16, 0))
        ttk.Button(bar, text="Товар ↓", style="Menu.TButton", command=lambda: self._move_product(+1)).pack(side="left", padx=(8, 0))

        # Tree
        self.tree = ttk.Treeview(card, columns=("name",), show="tree", style="Data.Treeview")
        self.tree.heading("#0", text="Группы / Товары", anchor="w")
        self.tree.column("#0", width=720, anchor="w")

        y_scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)

        self.tree.grid(row=3, column=0, sticky="nsew")
        y_scroll.grid(row=3, column=1, sticky="ns")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(3, weight=1)

        # Double-click expand/collapse
        self.tree.bind("<Double-1>", self._on_double_click)

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _seed_if_empty(self):
        try:
            groups = self.db.list_product_groups_meridian()
            prods = self.db.list_products_meridian()
        except Exception:
            return
        if groups or prods:
            return
        # Seed with provided data, cleaning spaces and fixing typos
        for gname, items in MERIDIAN_SEED:
            gname = _clean_spaces(gname)
            gid = self.db.add_product_group_meridian(gname)
            for nm in items:
                self.db.add_product_meridian(_clean_spaces(nm), gid)

    def _reload(self, initial_seed: bool = False):
        if initial_seed and self.db:
            self._seed_if_empty()
        # Load groups and products
        try:
            self._groups = self.db.list_product_groups_meridian()
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось загрузить группы:\n{e}")
            self._groups = []
        try:
            # Build mapping group_id -> products
            self._group_products = {}
            for g in self._groups:
                self._group_products[g["id"]] = self.db.list_products_meridian_by_group(g["id"])
            self._ungrouped = self.db.list_products_meridian_by_group(None)
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось загрузить товары:\n{e}")
            self._group_products = {}
            self._ungrouped = []
        self._refresh_view()

    def _refresh_view(self):
        self.tree.delete(*self.tree.get_children())
        # Ungrouped section if exists
        if self._ungrouped:
            uroot = self.tree.insert("", "end", text="Без группы", open=True, tags=("group", "ungrouped", "gid:None"))
            for p in self._ungrouped:
                self.tree.insert(uroot, "end", text=p["name"], tags=("product", f"pid:{p['id']}", "gid:None"))
        # Groups
        for g in self._groups:
            gid = g["id"]
            node = self.tree.insert("", "end", text=g["name"], open=False, tags=("group", f"gid:{gid}"))
            for p in self._group_products.get(gid, []):
                self.tree.insert(node, "end", text=p["name"], tags=("product", f"pid:{p['id']}", f"gid:{gid}"))

    def _selection(self):
        sel = self.tree.selection()
        if not sel:
            return None, None
        item = sel[0]
        tags = set(self.tree.item(item, "tags") or [])
        text = self.tree.item(item, "text")
        gid = None
        pid = None
        for t in tags:
            if t.startswith("gid:"):
                v = t.split(":", 1)[1]
                gid = None if v == "None" else int(v)
            if t.startswith("pid:"):
                pid = int(t.split(":", 1)[1])
        kind = "group" if "group" in tags and "product" not in tags else ("product" if "product" in tags else None)
        return kind, {"item": item, "text": text, "gid": gid, "pid": pid}

    def _on_double_click(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        try:
            is_open = self.tree.item(item, "open")
            self.tree.item(item, open=not is_open)
        except Exception:
            pass

    # Group actions
    def _add_group(self):
        name = simpledialog.askstring("Новая группа", "Введите название группы:", parent=self)
        if not name:
            return
        name = _clean_spaces(name)
        try:
            self.db.add_product_group_meridian(name)
            self._reload()
        except Exception as e:
            messagebox.showerror("Группа", f"Не удалось добавить группу:\n{e}")

    def _rename_group(self):
        kind, info = self._selection()
        if kind != "group":
            messagebox.showinfo("Группа", "Выберите группу.")
            return
        current = info["text"]
        name = simpledialog.askstring("Переименовать группу", "Новое название:", initialvalue=current, parent=self)
        if not name:
            return
        name = _clean_spaces(name)
        try:
            # find gid from tag
            gid = info["gid"]
            if gid is None:
                messagebox.showinfo("Группа", "Нельзя переименовать 'Без группы'.")
                return
            self.db.update_product_group_meridian(gid, name)
            self._reload()
        except Exception as e:
            messagebox.showerror("Группа", f"Не удалось переименовать группу:\n{e}")

    def _delete_group(self):
        kind, info = self._selection()
        if kind != "group":
            messagebox.showinfo("Группа", "Выберите группу.")
            return
        gid = info["gid"]
        if gid is None:
            messagebox.showinfo("Группа", "Нельзя удалить 'Без группы'.")
            return
        if not messagebox.askyesno("Удалить группу", f"Удалить группу '{info['text']}'?\nТовары останутся в 'Без группы'."):
            return
        try:
            self.db.delete_product_group_meridian(gid)
            self._reload()
        except Exception as e:
            messagebox.showerror("Группа", f"Не удалось удалить группу:\n{e}")

    def _move_group(self, direction: int):
        kind, info = self._selection()
        if kind != "group":
            messagebox.showinfo("Группа", "Выберите группу.")
            return
        gid = info["gid"]
        if gid is None:
            messagebox.showinfo("Группа", "Нельзя перемещать 'Без группы'.")
            return
        try:
            self.db.move_group_meridian(gid, direction)
            self._reload()
        except Exception as e:
            messagebox.showerror("Группа", f"Не удалось переместить группу:\n{e}")

    # Product actions
    def _add_product(self):
        kind, info = self._selection()
        gid = None
        if kind == "group":
            gid = info["gid"]
        elif kind == "product":
            gid = info["gid"]
        name = simpledialog.askstring("Новый товар", "Название товара:", parent=self)
        if not name:
            return
        name = _clean_spaces(name)
        try:
            self.db.add_product_meridian(name, gid)
            self._reload()
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось добавить товар:\n{e}")

    def _edit_product(self):
        kind, info = self._selection()
        if kind != "product":
            messagebox.showinfo("Товар", "Выберите товар.")
            return
        current = info["text"]
        pid = info["pid"]
        gid = info["gid"]
        name = simpledialog.askstring("Переименовать товар", "Новое название:", initialvalue=current, parent=self)
        if not name:
            return
        name = _clean_spaces(name)
        try:
            self.db.update_product_meridian(pid, name, gid)
            self._reload()
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось переименовать товар:\n{e}")

    def _delete_product(self):
        kind, info = self._selection()
        if kind != "product":
            messagebox.showinfo("Товар", "Выберите товар.")
            return
        if not messagebox.askyesno("Удалить товар", f"Удалить '{info['text']}'?"):
            return
        try:
            self.db.delete_product_meridian(info["pid"])
            self._reload()
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось удалить товар:\n{e}")

    def _move_product(self, direction: int):
        kind, info = self._selection()
        if kind != "product":
            messagebox.showinfo("Товар", "Выберите товар.")
            return
        try:
            self.db.move_product_meridian(info["pid"], direction)
            self._reload()
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось переместить товар:\n{e}")