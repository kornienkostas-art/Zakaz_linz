import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.db import AppDB  # type hint only


# Reusable spin control (duplicate small helper to keep file self-contained)
class SpinField(ttk.Frame):
    def __init__(self, master, var: tk.StringVar, step: float, lo: float, hi: float, round_to: float, decimals: int, show_plus: bool):
        super().__init__(master)
        self.var = var
        self.cfg = dict(step=step, lo=lo, hi=hi, round_to=round_to, decimals=decimals, show_plus=show_plus)
        self.entry = ttk.Entry(self, textvariable=self.var, width=10)
        self.entry.pack(side="left", fill="x", expand=True)
        btns = ttk.Frame(self)
        btns.pack(side="left", padx=(4, 0))
        ttk.Button(btns, text="−", width=1, command=lambda: self._apply(-self.cfg["step"])).pack(side="top", pady=(0, 2))
        ttk.Button(btns, text="+", width=1, command=lambda: self._apply(+self.cfg["step"])).pack(side="top")
        self.entry.bind("<MouseWheel>", self._on_wheel)
        self.entry.bind("<Button-4>", self._on_wheel)
        self.entry.bind("<Button-5>", self._on_wheel)
        self.entry.bind("<KeyPress>", self._on_key)
        self.entry.bind("<FocusOut>", lambda e: self._normalize())

    def _fmt(self, v: float) -> str:
        d = self.cfg["decimals"]
        s = f"{v:.{d}f}" if d > 0 else f"{int(round(v))}"
        if self.cfg["show_plus"]:
            if v >= 0 and not s.startswith("+"):
                s = "+" + s
        else:
            s = s.lstrip("+")
        return s

    def _parse(self, s: str) -> float:
        t = (s or "").replace(",", ".").strip()
        if not t:
            return 0.0
        try:
            return float(t)
        except Exception:
            return 0.0

    def _apply(self, delta: float):
        v = self._parse(self.var.get()) + delta
        lo, hi = self.cfg["lo"], self.cfg["hi"]
        v = max(lo, min(hi, v))
        rt = self.cfg["round_to"]
        if rt:
            v = round(v / rt) * rt
        self.var.set(self._fmt(v))

    def _normalize(self):
        self._apply(0.0)

    def _on_wheel(self, event):
        delta = 0
        if event.num == 4:
            delta = +1
        elif event.num == 5:
            delta = -1
        else:
            delta = +1 if event.delta > 0 else -1
        self._apply(delta * self.cfg["step"])
        return "break"

    def _on_key(self, event):
        if (event.state & 0x4) != 0:  # Ctrl
            if event.keysym in ("Up", "KP_Up"):
                self._apply(+self.cfg["step"])
                return "break"
            if event.keysym in ("Down", "KP_Down"):
                self._apply(-self.cfg["step"])
                return "break"
        return None


class MeridianOrdersView(ttk.Frame):
    """Полностью переписанный экран заказов 'Меридиан': список + встроенный редактор с позициями."""
    STATUSES = ["Не заказан", "Заказан"]

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame")
        self.master = master
        self.on_back = on_back
        self.db: AppDB | None = getattr(self.master, "db", None)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(1, weight=1)

        self.orders: list[dict] = []
        self.items: list[dict] = []  # items of current order
        self.products = self.db.list_products_meridian() if self.db else []

        self._build_header()
        self._build_left_list()
        self._build_right_editor()
        self._refresh_orders()

    def _build_header(self):
        bar = ttk.Frame(self, padding=(12, 10))
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(bar, text="← Главное меню", style="Back.TButton", command=self._go_back).pack(side="left")
        ttk.Button(bar, text="Товары", style="Menu.TButton", command=self._open_products).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt).pack(side="left", padx=(8, 0))

    def _build_left_list(self):
        left = ttk.Frame(self, padding=12)
        left.grid(row=1, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        cols=("title","count","status","date")
        headers={"title":"Название заказа","count":"Позиций","status":"Статус","date":"Дата"}
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="w")
            width={"title":300,"count":90,"status":120,"date":140}[c]
            self.tree.column(c, width=width, anchor="w", stretch=True)
        y=ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._load_selected())

        actions = ttk.Frame(left)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8,0))
        ttk.Button(actions, text="Новый", style="Menu.TButton", command=self._new_order).pack(side="left")
        ttk.Button(actions, text="Сохранить", style="Menu.TButton", command=self._save_order).pack(side="left", padx=(8,0))
        ttk.Button(actions, text="Удалить", style="Menu.TButton", command=self._delete_order).pack(side="left", padx=(8,0))

    def _build_right_editor(self):
        right = ttk.Frame(self, padding=12)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)

        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Не заказан")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))

        ttk.Label(right, text="Название заказа").grid(row=0, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=(8,0))
        ttk.Label(right, text="Статус").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Combobox(right, textvariable=self.status_var, values=self.STATUSES, height=6).grid(row=1, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="Дата").grid(row=2, column=0, sticky="w", pady=(6,0))
        ttk.Entry(right, textvariable=self.date_var, state="readonly").grid(row=2, column=1, sticky="w", padx=(8,0))

        # Items table
        ttk.Separator(right).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10,8))
        ttk.Label(right, text="Позиции заказа").grid(row=4, column=0, columnspan=2, sticky="w")

        items_frame = ttk.Frame(right)
        items_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
        right.rowconfigure(5, weight=1)
        cols=("product","sph","cyl","ax","d","qty")
        headers={"product":"Товар","sph":"SPH","cyl":"CYL","ax":"AX","d":"D","qty":"Кол-во"}
        self.items_tree = ttk.Treeview(items_frame, columns=cols, show="headings")
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            width={"product":240,"sph":70,"cyl":70,"ax":60,"d":60,"qty":80}[c]
            self.items_tree.column(c, width=width, anchor="w", stretch=True)
        y2=ttk.Scrollbar(items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y2.set)
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y2.grid(row=0, column=1, sticky="ns")
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(0, weight=1)

        self.items_tree.bind("<<TreeviewSelect>>", lambda e: self._load_item_selected())

        # Inline item editor
        ttk.Separator(right).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8,8))
        self.it_product_var = tk.StringVar()
        self.it_sph_var = tk.StringVar(value="+0.00")
        self.it_cyl_var = tk.StringVar(value="-0.25")
        self.it_ax_var = tk.StringVar(value="90")
        self.it_d_var = tk.StringVar(value="45")
        self.it_qty_var = tk.StringVar(value="1")

        ttk.Label(right, text="Товар").grid(row=7, column=0, sticky="w")
        self.product_combo = ttk.Combobox(right, textvariable=self.it_product_var, values=[p.get("name","") for p in self.products], height=10)
        self.product_combo.grid(row=7, column=1, sticky="ew", padx=(8,0))

        ttk.Label(right, text="SPH").grid(row=8, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.it_sph_var, 0.25, -30.0, 30.0, 0.25, 2, True).grid(row=8, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="CYL").grid(row=9, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.it_cyl_var, 0.25, -10.0, 10.0, 0.25, 2, True).grid(row=9, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="AX").grid(row=10, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.it_ax_var, 1.0, 0.0, 180.0, 1.0, 0, False).grid(row=10, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="D (мм)").grid(row=11, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.it_d_var, 5.0, 40.0, 90.0, 5.0, 0, False).grid(row=11, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="Количество").grid(row=12, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.it_qty_var, 1.0, 1.0, 20.0, 1.0, 0, False).grid(row=12, column=1, sticky="w", padx=(8,0))

        it_btns = ttk.Frame(right)
        it_btns.grid(row=13, column=0, columnspan=2, sticky="e", pady=(8,0))
        ttk.Button(it_btns, text="Добавить/Обновить позицию", style="Menu.TButton", command=self._add_or_update_item).pack(side="right")
        ttk.Button(it_btns, text="Удалить позицию", style="Back.TButton", command=self._delete_item).pack(side="right", padx=(8,0))

    # Navigation
    def _go_back(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "on_back", None)
            if callable(cb):
                cb()

    def _open_products(self):
        from app.views.products_meridian import ProductsMeridianView
        from app.views.main import MainWindow
        try:
            self.destroy()
        except Exception:
            pass
        ProductsMeridianView(self.master, getattr(self.master, "db", None), on_back=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master)))

    # Data rendering
    def _refresh_orders(self):
        self.orders=[]
        if self.db:
            try:
                self.orders=self.db.list_meridian_orders()
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить заказы:\n{e}")
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx,o in enumerate(self.orders):
            count=0
            try:
                if self.db and o.get("id") is not None:
                    count=len(self.db.get_meridian_items(o["id"]))
            except Exception:
                count=0
            self.tree.insert("", "end", iid=str(idx), values=(o.get("title",""), count, o.get("status",""), o.get("date","")))
        # auto-select
        try:
            children=self.tree.get_children()
            if children:
                self.tree.selection_set(children[0]); self._load_selected()
        except Exception:
            pass

    def _load_selected(self):
        sel=self.tree.selection()
        if not sel:
            self.title_var.set(""); self.status_var.set("Не заказан"); self.date_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
            self.items=[]; self._render_items()
            return
        idx=int(sel[0]); o=self.orders[idx]
        self.title_var.set(o.get("title",""))
        self.status_var.set(o.get("status","Не заказан"))
        self.date_var.set(o.get("date",""))
        self.items=[]
        if self.db and o.get("id") is not None:
            try:
                self.items=self.db.get_meridian_items(o["id"])
            except Exception:
                self.items=[]
        self._render_items()

    def _render_items(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx,it in enumerate(self.items):
            self.items_tree.insert("", "end", iid=str(idx), values=(it.get("product",""), it.get("sph",""), it.get("cyl",""), it.get("ax",""), it.get("d",""), it.get("qty","")))

    def _load_item_selected(self):
        sel=self.items_tree.selection()
        if not sel: return
        idx=int(sel[0]); it=self.items[idx]
        self.it_product_var.set(it.get("product",""))
        self.it_sph_var.set(it.get("sph","+0.00"))
        self.it_cyl_var.set(it.get("cyl","-0.25"))
        self.it_ax_var.set(it.get("ax","90"))
        self.it_d_var.set(it.get("d","45"))
        self.it_qty_var.set(str(it.get("qty","1")))

    def _collect_order(self) -> dict:
        return {
            "title": (self.title_var.get() or "").strip(),
            "status": (self.status_var.get() or "Не заказан").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    def _new_order(self):
        # clear editor
        self.tree.selection_remove(self.tree.selection())
        self.title_var.set("")
        self.status_var.set("Не заказан")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.items=[]
        self._render_items()

    def _current_order_id(self):
        sel=self.tree.selection()
        if not sel: return None
        try:
            idx=int(sel[0]); return self.orders[idx].get("id")
        except Exception:
            return None

    def _save_order(self):
        data=self._collect_order()
        if not data["title"]:
            # автогенерация названия
            try:
                n=(len(self.orders)+1)
                data["title"]=f"Заказ Меридиан #{n}"
            except Exception:
                data["title"]="Заказ Меридиан"
        order_id=self._current_order_id()
        try:
            if order_id and self.db:
                self.db.update_meridian_order(order_id, data)
                self.db.replace_meridian_items(order_id, self.items)
            elif self.db:
                self.db.add_meridian_order(data, self.items)
        except Exception as e:
            messagebox.showerror("Сохранение", f"Не удалось сохранить заказ:\n{e}")
            return
        self._refresh_orders()

    def _delete_order(self):
        order_id=self._current_order_id()
        if not order_id:
            messagebox.showinfo("Удаление","Не выбран заказ."); return
        if not messagebox.askyesno("Удалить","Удалить выбранный заказ?"): return
        try:
            if self.db:
                self.db.delete_meridian_order(order_id)
        except Exception as e:
            messagebox.showerror("Удаление", f"Не удалось удалить заказ:\n{e}")
            return
        self._refresh_orders()

    # Items ops
    def _add_or_update_item(self):
        it={
            "product": (self.it_product_var.get() or "").strip(),
            "sph": (self.it_sph_var.get() or "").strip(),
            "cyl": (self.it_cyl_var.get() or "").strip(),
            "ax": (self.it_ax_var.get() or "").strip(),
            "d": (self.it_d_var.get() or "").strip(),
            "qty": (self.it_qty_var.get() or "1").strip(),
        }
        if not it["product"]:
            messagebox.showinfo("Позиция","Заполните поле 'Товар'."); return
        sel=self.items_tree.selection()
        if sel:
            idx=int(sel[0]); self.items[idx]=it
        else:
            self.items.append(it)
        self._render_items()

    def _delete_item(self):
        sel=self.items_tree.selection()
        if not sel: return
        idx=int(sel[0])
        del self.items[idx]
        self._render_items()

    def _export_txt(self):
        # Группировка по товару для заказов со статусом 'Не заказан'
        groups: dict[str,list[dict]]={}
        # Ensure we have latest orders
        if not self.orders:
            self._refresh_orders()
        for o in self.orders:
            if (o.get("status","") or "").strip()!="Не заказан":
                continue
            order_id=o.get("id")
            items=[]
            if self.db and order_id is not None:
                try:
                    items=self.db.get_meridian_items(order_id)
                except Exception:
                    items=[]
            for it in items:
                key=(it.get("product","") or "").strip() or "(Без названия)"
                groups.setdefault(key,[]).append(it)
        if not groups:
            messagebox.showinfo("Экспорт","Нет позиций со статусом 'Не заказан'."); return
        lines=[]
        for product, items in groups.items():
            lines.append(product)
            for it in items:
                parts=[]
                for k,lbl in (("sph","Sph"),("cyl","Cyl"),("ax","Ax")):
                    v=(it.get(k,"") or "").strip()
                    if v!="":
                        parts.append(f"{lbl}: {v}")
                d=(it.get("d","") or "").strip()
                if d!="":
                    parts.append(f"D:{d}мм")
                q=(it.get("qty","") or "").strip()
                if q!="":
                    parts.append(f"Количество: {q}")
                if parts:
                    lines.append(" ".join(parts))
            lines.append("")
        content="\n".join(lines).strip()+"\n"
        date_str = datetime.now().strftime("%d.%m.%y")
        filename=f"MERIDIAN_{date_str}.txt"
        export_path=getattr(self.master,"app_settings",{}).get("export_path",None)
        if not export_path:
            desktop=os.path.join(os.path.expanduser("~"),"Desktop")
            export_path=desktop if os.path.isdir(desktop) else os.getcwd()
        path=os.path.join(export_path, filename)
        try:
            with open(path,"w",encoding="utf-8") as f: f.write(content)
            messagebox.showinfo("Экспорт", f"Экспорт выполнен:\n{path}")
        except Exception as e:
            messagebox.showerror("Экспорт", f"Ошибка записи файла:\n{e}")