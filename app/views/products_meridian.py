import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from app.db import AppDB  # type hint only


def _clean_spaces(name: str) -> str:
    return " ".join((name or "").split())


class NameDialog(tk.Toplevel):
    def __init__(self, master, title: str, prompt: str, initial: str = ""):
        super().__init__(master)
        self.title(title)
        self.configure(bg="#f8fafc")
        # Небольшое, но широкое окно без раздувания на 70% экрана
        try:
            self.minsize(700, 120)
        except Exception:
            pass
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.result = None
        frm = ttk.Frame(self, padding=16, style="Card.TFrame")
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=prompt, style="Subtitle.TLabel").pack(anchor="w")
        self.entry = ttk.Entry(frm)
        self.entry.pack(fill="x", expand=True, pady=(8, 8))
        self.entry.insert(0, initial or "")
        try:
            self.entry.icursor("end")
            self.entry.select_range(0, "end")
        except Exception:
            pass

        btns = ttk.Frame(frm, style="Card.TFrame")
        btns.pack(fill="x", anchor="e")
        ttk.Button(btns, text="OK", style="Menu.TButton", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self._cancel).pack(side="right", padx=(8, 0))

        # Центрируем аккуратно без масштабирования
        try:
            from app.utils import center_on_screen
            self.update_idletasks()
            center_on_screen(self)
        except Exception:
            pass

        self.entry.focus_set()

    def _ok(self):
        self.result = (self.entry.get() or "").strip()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


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

        # Actions (single row + universal move arrows)
        bar = ttk.Frame(card, style="Card.TFrame")
        bar.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Button(bar, text="Добавить группу", style="Menu.TButton", command=self._add_group).pack(side="left")
        ttk.Button(bar, text="Добавить подгруппу", style="Menu.TButton", command=self._add_subgroup).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Переименовать группу", style="Menu.TButton", command=self._rename_group).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить группу", style="Menu.TButton", command=self._delete_group).pack(side="left", padx=(8, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(bar, text="Добавить товар", style="Menu.TButton", command=self._add_product).pack(side="left")
        ttk.Button(bar, text="Редактировать товар", style="Menu.TButton", command=self._edit_product).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить товар", style="Menu.TButton", command=self._delete_product).pack(side="left", padx=(8, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(bar, text="▲", width=4, style="Menu.TButton", command=lambda: self._move_selected(-1)).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="▼", width=4, style="Menu.TButton", command=lambda: self._move_selected(+1)).pack(side="left", padx=(4, 0))

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

        # Double-click expand/collapse only on groups (по всей строке)
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

    def _capture_state(self):
        open_gids = set()
        try:
            for top in self.tree.get_children(""):
                tags = set(self.tree.item(top, "tags") or [])
                if "group" in tags:
                    gid = None
                    for t in tags:
                        if t.startswith("gid:"):
                            v = t.split(":", 1)[1]
                            gid = None if v == "None" else int(v)
                    if gid is not None and self.tree.item(top, "open"):
                        open_gids.add(gid)
        except Exception:
            pass
        kind, info = self._selection()
        sel = None
        if kind and info:
            sel = {"kind": kind, "gid": info.get("gid"), "pid": info.get("pid")}
        return open_gids, sel

    def _reload(self, initial_seed: bool = False, preserve_state: bool = False, open_gids: set | None = None, select_pref: dict | None = None):
        if initial_seed and self.db:
            self._seed_if_empty()
        if preserve_state and (open_gids is None or select_pref is None):
            # auto-capture if not provided
            og, sel = self._capture_state()
            if open_gids is None:
                open_gids = og
            if select_pref is None:
                select_pref = sel
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
        self._refresh_view(open_gids=open_gids, select_pref=select_pref)

    def _find_node_by_tag(self, tag: str):
        try:
            def walk(parent=""):
                for child in self.tree.get_children(parent):
                    tags = self.tree.item(child, "tags") or []
                    if tag in tags:
                        return child
                    found = walk(child)
                    if found:
                        return found
                return None
            return walk("")
        except Exception:
            return None

    def _refresh_view(self, open_gids: set | None = None, select_pref: dict | None = None):
        self.tree.delete(*self.tree.get_children())
        # Ungrouped section if exists
        ungrouped_root = None
        if self._ungrouped:
            ungrouped_root = self.tree.insert("", "end", text="Без группы", open=True, tags=("group", "ungrouped", "gid:None"))
            for p in self._ungrouped:
                self.tree.insert(ungrouped_root, "end", text=p["name"], tags=("product", f"pid:{p['id']}", "gid:None"))

        # Build hierarchy: parent_id -> list of groups
        children_map = {}
        for g in self._groups:
            pid = g.get("parent_id")
            children_map.setdefault(pid, []).append(g)

        gid_to_node = {}

        def add_group_node(parent_tree_item, gdict):
            gid = gdict["id"]
            is_open = bool(open_gids and gid in open_gids)
            node = self.tree.insert(parent_tree_item, "end", text=gdict["name"], open=is_open, tags=("group", f"gid:{gid}"))
            gid_to_node[gid] = node
            # child groups first
            for child in children_map.get(gid, []):
                add_group_node(node, child)
            # then products under this group
            for p in self._group_products.get(gid, []):
                self.tree.insert(node, "end", text=p["name"], tags=("product", f"pid:{p['id']}", f"gid:{gid}"))

        # Top-level groups
        for g in children_map.get(None, []):
            add_group_node("", g)

        # Restore selection
        try:
            if select_pref:
                target_item = None
                if select_pref.get("kind") == "product" and select_pref.get("pid") is not None:
                    target_item = self._find_node_by_tag(f"pid:{select_pref['pid']}")
                if not target_item:
                    gid = select_pref.get("gid")
                    if gid is None and ungrouped_root:
                        target_item = ungrouped_root
                    elif gid in gid_to_node:
                        target_item = gid_to_node[gid]
                if target_item:
                    self.tree.selection_set(target_item)
                    self.tree.see(target_item)
        except Exception:
            pass

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

    def _on_double_click(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return
            tags = set(self.tree.item(item, "tags") or [])
            if "group" in tags:
                is_open = self.tree.item(item, "open")
                self.tree.item(item, open=not is_open)
                return
            if "product" in tags:
                self._edit_product()
        except Exception:
            pass

    # Group actions
    def _add_group(self):
        dlg = NameDialog(self, "Новая группа", "Введите название группы:")
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return
        name = _clean_spaces(name)
        try:
            og, sel = self._capture_state()
            self.db.add_product_group_meridian(name, None)
            self._reload(preserve_state=True, open_gids=og, select_pref=sel)
        except Exception as e:
            messagebox.showerror("Группа", f"Не удалось добавить группу:\n{e}")

    def _add_subgroup(self):
        kind, info = self._selection()
        parent_id = None
        if kind == "group":
            parent_id = info["gid"]
            if parent_id is None:
                messagebox.showinfo("Подгруппа", "Выберите группу (не 'Без группы').")
                return
        elif kind == "product":
            parent_id = info["gid"]
            if parent_id is None:
                messagebox.showinfo("Подгруппа", "Выберите товар в нужной группе, либо выделите группу.")
                return
        else:
            messagebox.showinfo("Подгруппа", "Сначала выберите группу или товар внутри группы.")
            return

        dlg = NameDialog(self, "Новая подгруппа", "Введите название подгруппы:")
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return
        name = _clean_spaces(name)
        try:
            og, sel = self._capture_state()
            gid_new = self.db.add_product_group_meridian(name, parent_id)
            if og is None:
                og = set()
            og.add(parent_id)
            self._reload(preserve_state=True, open_gids=og, select_pref={"kind": "group", "gid": gid_new, "pid": None})
        except Exception as e:
            messagebox.showerror("Подгруппа", f"Не удалось добавить подгруппу:\n{e}")

    def _rename_group(self):
        kind, info = self._selection()
        if kind != "group":
            messagebox.showinfo("Группа", "Выберите группу.")
            return
        if info["gid"] is None:
            messagebox.showinfo("Группа", "Нельзя переименовать 'Без группы'.")
            return
        dlg = NameDialog(self, "Переименовать группу", "Новое название:", initial=info["text"])
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return
        name = _clean_spaces(name)
        try:
            # Keep same parent, change only name
            parent_id = None
            for g in self._groups:
                if g["id"] == info["gid"]:
                    parent_id = g.get("parent_id")
                    break
            og, sel = self._capture_state()
            self.db.update_product_group_meridian(info["gid"], name, parent_id)
            self._reload(preserve_state=True, open_gids=og, select_pref=sel)
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
        if not messagebox.askyesno("Удалить группу", f"Удалить группу '{info['text']}' и все её подгруппы?\nТовары останутся в 'Без группы'."):
            return
        try:
            og, sel = self._capture_state()
            self.db.delete_product_group_meridian(gid)
            # после удаления группы выберем "Без группы" или ближайшую группу
            self._reload(preserve_state=True, open_gids=og, select_pref={"kind": "group", "gid": None, "pid": None})
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
            og, sel = self._capture_state()
            self.db.move_group_meridian(gid, direction)
            self._reload(preserve_state=True, open_gids=og, select_pref=sel)
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
        dlg = NameDialog(self, "Новый товар", "Название товара:")
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return
        name = _clean_spaces(name)
        try:
            og, sel = self._capture_state()
            self.db.add_product_meridian(name, gid)
            # Попробуем выбрать только что добавленный товар: заново загрузим и выберем группу gid
            self._reload(preserve_state=True, open_gids=og, select_pref={"kind": "group", "gid": gid, "pid": None})
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
        dlg = NameDialog(self, "Переименовать товар", "Новое название:", initial=current)
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return
        name = _clean_spaces(name)
        try:
            og, sel = self._capture_state()
            self.db.update_product_meridian(pid, name, gid)
            self._reload(preserve_state=True, open_gids=og, select_pref=sel)
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
            og, _sel = self._capture_state()
            gid = info["gid"]
            self.db.delete_product_meridian(info["pid"])
            # После удаления выберем группу, чтобы дерево не схлопывалось
            self._reload(preserve_state=True, open_gids=og, select_pref={"kind": "group", "gid": gid, "pid": None})
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось удалить товар:\n{e}")

    def _move_product(self, direction: int):
        kind, info = self._selection()
        if kind != "product":
            messagebox.showinfo("Товар", "Выберите товар.")
            return
        try:
            og, sel = self._capture_state()
            self.db.move_product_meridian(info["pid"], direction)
            self._reload(preserve_state=True, open_gids=og, select_pref=sel)
        except Exception as e:
            messagebox.showerror("Товар", f"Не удалось переместить товар:\n{e}")

    def _move_selected(self, direction: int):
        """Move selected entity (group or product) up/down within its level."""
        kind, info = self._selection()
        if not kind:
            messagebox.showinfo("Перемещение", "Выберите группу или товар.")
            return
        if kind == "group":
            gid = info["gid"]
            if gid is None:
                messagebox.showinfo("Группа", "Нельзя перемещать 'Без группы'.")
                return
            try:
                og, sel = self._capture_state()
                self.db.move_group_meridian(gid, direction)
                self._reload(preserve_state=True, open_gids=og, select_pref=sel)
            except Exception as e:
                messagebox.showerror("Группа", f"Не удалось переместить группу:\n{e}")
        elif kind == "product":
            try:
                og, sel = self._capture_state()
                self.db.move_product_meridian(info["pid"], direction)
                self._reload(preserve_state=True, open_gids=og, select_pref=sel)
            except Exception as e:
                messagebox.showerror("Товар", f"Не удалось переместить товар:\n{e}")