import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.utils import format_phone_mask
from app.db import AppDB  # type hint only


# --- Small spin control (wheel + +/- + Ctrl+arrows) -----------------------------------------
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

        # bindings
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


# --- New integrated MKL orders UI ------------------------------------------------------------
class MKLOrdersView(ttk.Frame):
    """Полностью переписанный экран заказов МКЛ: слева таблица, справа редактор."""

    STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame")
        self.master = master
        self.on_back = on_back
        self.db: AppDB | None = getattr(self.master, "db", None)

        # Root grid fill
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        self.orders: list[dict] = []
        self.clients = self.db.list_clients() if self.db else []
        self.products = self.db.list_products_mkl() if self.db else []

        self._build_header()
        self._build_left_table()
        self._build_right_editor()
        self._refresh_orders()

    def _build_header(self):
        bar = ttk.Frame(self, padding=(12, 10))
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(bar, text="← Главное меню", style="Back.TButton", command=self._go_back).pack(side="left")
        ttk.Button(bar, text="Клиенты", style="Menu.TButton", command=self._open_clients).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Товары", style="Menu.TButton", command=self._open_products).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt).pack(side="left", padx=(8, 0))

    def _build_left_table(self):
        left = ttk.Frame(self, padding=12)
        left.grid(row=1, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        cols = ("fio", "phone", "product", "sph", "cyl", "ax", "bc", "qty", "status", "date", "comment")
        headers = {"fio":"ФИО","phone":"Телефон","product":"Товар","sph":"Sph","cyl":"Cyl","ax":"Ax","bc":"BC","qty":"Кол-во","status":"Статус","date":"Дата","comment":"Комментарий"}
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="w")
            width = {"fio":200,"phone":140,"product":180,"sph":70,"cyl":70,"ax":60,"bc":60,"qty":70,"status":120,"date":140,"comment":160}[c]
            self.tree.column(c, width=width, anchor="w", stretch=True)
        y = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._load_selected())

        # actions under table
        actions = ttk.Frame(left)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(actions, text="Новый", style="Menu.TButton", command=self._clear_form).pack(side="left")
        ttk.Button(actions, text="Сохранить", style="Menu.TButton", command=self._save_current).pack(side="left", padx=(8,0))
        ttk.Button(actions, text="Удалить", style="Menu.TButton", command=self._delete_selected).pack(side="left", padx=(8,0))

    def _build_right_editor(self):
        right = ttk.Frame(self, padding=12)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)

        self.fio_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.sph_var = tk.StringVar(value="+0.00")
        self.cyl_var = tk.StringVar(value="-0.25")
        self.ax_var = tk.StringVar(value="90")
        self.bc_var = tk.StringVar(value="8.6")
        self.qty_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="Не заказан")
        self.comment_var = tk.StringVar()

        # Client
        ttk.Label(right, text="Клиент (ФИО)").grid(row=0, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.fio_var).grid(row=0, column=1, sticky="ew", padx=(8,0))
        ttk.Label(right, text="Телефон").grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Entry(right, textvariable=self.phone_var).grid(row=1, column=1, sticky="ew", padx=(8,0))

        # Product
        ttk.Label(right, text="Товар").grid(row=2, column=0, sticky="w", pady=(6,0))
        products = [p.get("name","") for p in self.products]
        self.product_combo = ttk.Combobox(right, textvariable=self.product_var, values=products, height=10)
        self.product_combo.grid(row=2, column=1, sticky="ew", padx=(8,0))

        # Optics
        ttk.Label(right, text="SPH").grid(row=3, column=0, sticky="w", pady=(10,0))
        SpinField(right, self.sph_var, step=0.25, lo=-30.0, hi=30.0, round_to=0.25, decimals=2, show_plus=True).grid(row=3, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="CYL").grid(row=4, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.cyl_var, step=0.25, lo=-10.0, hi=10.0, round_to=0.25, decimals=2, show_plus=True).grid(row=4, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="AX").grid(row=5, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.ax_var, step=1.0, lo=0.0, hi=180.0, round_to=1.0, decimals=0, show_plus=False).grid(row=5, column=1, sticky="w", padx=(8,0))
        ttk.Label(right, text="BC").grid(row=6, column=0, sticky="w", pady=(6,0))
        SpinField(right, self.bc_var, step=0.1, lo=8.0, hi=9.5, round_to=0.1, decimals=1, show_plus=False).grid(row=6, column=1, sticky="w", padx=(8,0))

        # Qty/Status
        ttk.Label(right, text="Количество").grid(row=7, column=0, sticky="w", pady=(10,0))
        qty_box = ttk.Frame(right); qty_box.grid(row=7, column=1, sticky="w", padx=(8,0))
        self.qty_spin = SpinField(qty_box, self.qty_var, step=1.0, lo=1.0, hi=20.0, round_to=1.0, decimals=0, show_plus=False)
        self.qty_spin.pack(side="left")

        ttk.Label(right, text="Статус").grid(row=8, column=0, sticky="w", pady=(6,0))
        ttk.Combobox(right, textvariable=self.status_var, values=self.STATUSES, height=8).grid(row=8, column=1, sticky="w", padx=(8,0))

        ttk.Label(right, text="Комментарий").grid(row=9, column=0, sticky="w", pady=(6,0))
        ttk.Entry(right, textvariable=self.comment_var).grid(row=9, column=1, sticky="ew", padx=(8,0))

        # Save buttons
        btns = ttk.Frame(right)
        btns.grid(row=10, column=0, columnspan=2, sticky="e", pady=(12,0))
        ttk.Button(btns, text="Очистить", style="Back.TButton", command=self._clear_form).pack(side="right", padx=(8,0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save_current).pack(side="right")

    # Navigation buttons to other screens
    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _open_clients(self):
        from app.views.clients import ClientsView
        from app.views.main import MainWindow
        def open_view():
            try: self.destroy()
            except Exception: pass
            ClientsView(self.master, self.db, on_back=lambda: MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
        open_view()

    def _open_products(self):
        from app.views.products_mkl import ProductsMKLView
        from app.views.main import MainWindow
        def open_view():
            try: self.destroy()
            except Exception: pass
            ProductsMKLView(self.master, self.db, on_back=lambda: MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
        open_view()

    # Data loading/rendering
    def _refresh_orders(self):
        self.orders = []
        if self.db:
            try:
                self.orders = self.db.list_mkl_orders()
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить заказы МКЛ:\n{e}")
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, o in enumerate(self.orders):
            values = (
                o.get("fio",""),
                format_phone_mask(o.get("phone","")),
                o.get("product",""),
                o.get("sph",""),
                o.get("cyl",""),
                o.get("ax",""),
                o.get("bc",""),
                o.get("qty",""),
                o.get("status",""),
                o.get("date",""),
                (o.get("comment","") or "").strip()
            )
            self.tree.insert("", "end", iid=str(idx), values=values)

        # select first
        try:
            first = self.tree.get_children()
            if first:
                self.tree.selection_set(first[0])
                self._load_selected()
        except Exception:
            pass

    def _load_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        o = self.orders[idx]
        self.fio_var.set(o.get("fio",""))
        self.phone_var.set(o.get("phone",""))
        self.product_var.set(o.get("product",""))
        self.sph_var.set(o.get("sph","+0.00"))
        self.cyl_var.set(o.get("cyl","-0.25"))
        self.ax_var.set(o.get("ax","90"))
        self.bc_var.set(o.get("bc","8.6"))
        self.qty_var.set(str(o.get("qty","1")))
        self.status_var.set(o.get("status","Не заказан"))
        self.comment_var.set(o.get("comment",""))

    def _collect_form(self) -> dict:
        return {
            "fio": (self.fio_var.get() or "").strip(),
            "phone": (self.phone_var.get() or "").strip(),
            "product": (self.product_var.get() or "").strip(),
            "sph": (self.sph_var.get() or "").strip(),
            "cyl": (self.cyl_var.get() or "").strip(),
            "ax": (self.ax_var.get() or "").strip(),
            "bc": (self.bc_var.get() or "").strip(),
            "qty": (self.qty_var.get() or "1").strip(),
            "status": (self.status_var.get() or "Не заказан").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": (self.comment_var.get() or "").strip(),
        }

    def _clear_form(self):
        self.tree.selection_remove(self.tree.selection())
        self.fio_var.set("")
        self.phone_var.set("")
        self.product_var.set("")
        self.sph_var.set("+0.00"); self.cyl_var.set("-0.25"); self.ax_var.set("90"); self.bc_var.set("8.6")
        self.qty_var.set("1"); self.status_var.set("Не заказан"); self.comment_var.set("")

    def _current_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            idx = int(sel[0])
            return self.orders[idx].get("id")
        except Exception:
            return None

    def _save_current(self):
        data = self._collect_form()
        # basic checks
        if not data["fio"]:
            messagebox.showinfo("Проверка", "Введите ФИО клиента.")
            return
        if not data["product"]:
            messagebox.showinfo("Проверка", "Выберите товар.")
            return
        rec_id = self._current_selected_id()
        try:
            if rec_id and self.db:
                self.db.update_mkl_order(rec_id, data)
            elif self.db:
                self.db.add_mkl_order(data)
        except Exception as e:
            messagebox.showerror("Сохранение", f"Не удалось сохранить заказ:\n{e}")
            return
        self._refresh_orders()

    def _delete_selected(self):
        rec_id = self._current_selected_id()
        if not rec_id:
            messagebox.showinfo("Удаление", "Не выбран заказ.")
            return
        if not messagebox.askyesno("Удалить", "Удалить выбранный заказ?"):
            return
        try:
            if self.db:
                self.db.delete_mkl_order(rec_id)
        except Exception as e:
            messagebox.showerror("Удаление", f"Не удалось удалить заказ:\n{e}")
            return
        self._refresh_orders()

    def _export_txt(self):
        # Группировка по товару, только статус 'Не заказан'
        if not self.orders:
            self._refresh_orders()
        groups: dict[str, list[dict]] = {}
        for o in self.orders:
            if (o.get("status","") or "").strip() != "Не заказан":
                continue
            key = (o.get("product","") or "").strip() or "(Без названия)"
            groups.setdefault(key, []).append(o)
        if not groups:
            messagebox.showinfo("Экспорт", "Нет заказов со статусом 'Не заказан'.")
            return
        lines = []
        for product, items in groups.items():
            lines.append(product)
            for o in items:
                parts=[]
                for k,lbl in (("sph","Sph"),("cyl","Cyl"),("ax","Ax"),("bc","BC")):
                    v=(o.get(k,"") or "").strip()
                    if v!="":
                        parts.append(f"{lbl}: {v}")
                q=(o.get("qty","") or "").strip()
                if q!="":
                    parts.append(f"Количество: {q}")
                if parts:
                    lines.append(" ".join(parts))
            lines.append("")
        content="\n".join(lines).strip()+"\n"
        date_str = datetime.now().strftime("%d.%m.%y")
        filename=f"MKL_{date_str}.txt"
        export_path = getattr(self.master, "app_settings", {}).get("export_path", None)
        if not export_path:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            export_path = desktop if os.path.isdir(desktop) else os.getcwd()
        path=os.path.join(export_path, filename)
        try:
            with open(path,"w",encoding="utf-8") as f: f.write(content)
            messagebox.showinfo("Экспорт", f"Экспорт выполнен:\n{path}")
        except Exception as e:
            messagebox.showerror("Экспорт", f"Ошибка записи файла:\n{e}")