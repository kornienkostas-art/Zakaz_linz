import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class MeridianOrderEditorView(ttk.Frame):
    """Простой редактор заказа 'Меридиан' (откат к базовому функционалу без каталога и ADD)."""

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

        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.items: list[dict] = [it.copy() for it in (initial or {}).get("items", [])]

        self._build_ui()
        self._refresh_items_view()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")
        ttk.Button(toolbar, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")

        body = ttk.Frame(self, style="Card.TFrame", padding=12)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        # Статус
        ttk.Label(body, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(body, textvariable=self.status_var, values=self.STATUSES, height=4, width=18).grid(row=1, column=0, sticky="w")

        ttk.Separator(body).grid(row=2, column=0, sticky="ew", pady=(12, 12))

        # Форма ввода (без каталога и ADD)
        form = ttk.Frame(body, style="Card.TFrame")
        form.grid(row=3, column=0, sticky="ew")
        for i in range(10):
            form.columnconfigure(i, weight=0)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Товар").grid(row=0, column=0, sticky="w")
        self.product_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.product_var).grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="SPH").grid(row=0, column=2, sticky="w")
        self.sph_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sph_var, width=10).grid(row=0, column=3, sticky="w", padx=(4, 12))

        ttk.Label(form, text="CYL").grid(row=0, column=4, sticky="w")
        self.cyl_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cyl_var, width=10).grid(row=0, column=5, sticky="w", padx=(4, 12))

        ttk.Label(form, text="AX").grid(row=0, column=6, sticky="w")
        self.ax_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ax_var, width=6).grid(row=0, column=7, sticky="w", padx=(4, 12))

        ttk.Label(form, text="D (мм)").grid(row=0, column=8, sticky="w")
        self.d_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.d_var, width=8).grid(row=0, column=9, sticky="w", padx=(4, 12))

        ttk.Label(form, text="Кол-во").grid(row=0, column=10, sticky="w")
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=99, textvariable=self.qty_var, width=6).grid(row=0, column=11, sticky="w", padx=(4, 0))

        ttk.Button(body, text="Добавить позицию", style="Menu.TButton", command=self._add_item).grid(row=4, column=0, sticky="w", pady=(8, 8))

        # Таблица позиций (без ADD)
        cols = ("product", "sph", "cyl", "ax", "d", "qty")
        self.items_tree = ttk.Treeview(body, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 360, "sph": 90, "cyl": 90, "ax": 80, "d": 90, "qty": 110}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)
        self.items_tree.grid(row=5, column=0, sticky="nsew")
        body.rowconfigure(5, weight=1)

        ttk.Button(body, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).grid(row=6, column=0, sticky="w", pady=(8, 0))

    def _add_item(self):
        name = (self.product_var.get() or "").strip()
        if not name:
            messagebox.showinfo("Позиция", "Введите название товара.")
            return
        def norm(v): return (v or "").strip()
        item = {
            "product": name,
            "sph": norm(self.sph_var.get()),
            "cyl": norm(self.cyl_var.get()),
            "ax": norm(self.ax_var.get()),
            "d": norm(self.d_var.get()),
            "qty": str(max(1, int(self.qty_var.get() or 1))),
        }
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

    def _refresh_items_view(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, it in enumerate(self.items):
            values = (it.get("product", ""), it.get("sph", ""), it.get("cyl", ""), it.get("ax", ""), it.get("d", ""), it.get("qty", ""))
            self.items_tree.insert("", "end", iid=str(idx), values=values)

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
