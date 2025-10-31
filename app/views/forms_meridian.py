import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Минимальная рабочая форма редактора заказа Меридиан.
# Включает ввод позиции и список позиций. Не зависит от других классов,
# чтобы исключить проблемы при импорте.


class MeridianOrderEditorView(ttk.Frame):
    """Редактор заказа 'Меридиан' внутри главного окна (минимально необходимая реализация)."""

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

        # Данные
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.items: list[dict] = []
        for it in (initial or {}).get("items", []):
            self.items.append(it.copy())

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")
        ttk.Button(toolbar, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        # Статус
        ttk.Label(card, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(card, textvariable=self.status_var, values=self.STATUSES, height=4).grid(row=1, column=0, sticky="w")

        ttk.Separator(card).grid(row=2, column=0, sticky="ew", pady=(12, 12))

        # Ввод позиции
        form = ttk.Frame(card, style="Card.TFrame")
        form.grid(row=3, column=0, sticky="ew")
        for i in range(14):
            form.columnconfigure(i, weight=0)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(5, weight=1)
        form.columnconfigure(9, weight=1)
        form.columnconfigure(13, weight=0)

        ttk.Label(form, text="Товар").grid(row=0, column=0, sticky="w")
        self.product_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.product_var, width=40).grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="SPH").grid(row=0, column=2, sticky="w")
        self.sph_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sph_var, width=8).grid(row=0, column=3, sticky="w", padx=(4, 12))

        ttk.Label(form, text="CYL").grid(row=0, column=4, sticky="w")
        self.cyl_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cyl_var, width=8).grid(row=0, column=5, sticky="w", padx=(4, 12))

        ttk.Label(form, text="AX").grid(row=0, column=6, sticky="w")
        self.ax_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ax_var, width=6).grid(row=0, column=7, sticky="w", padx=(4, 12))

        ttk.Label(form, text="ADD").grid(row=0, column=8, sticky="w")
        self.add_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.add_var, width=8).grid(row=0, column=9, sticky="w", padx=(4, 12))

        ttk.Label(form, text="D (мм)").grid(row=0, column=10, sticky="w")
        self.d_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.d_var, width=6).grid(row=0, column=11, sticky="w", padx=(4, 12))

        ttk.Label(form, text="Кол-во").grid(row=0, column=12, sticky="w")
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=20, textvariable=self.qty_var, width=6).grid(row=0, column=13, sticky="w", padx=(4, 0))

        ttk.Button(card, text="Добавить позицию", style="Menu.TButton", command=self._add_item).grid(row=4, column=0, sticky="w", pady=(8, 8))

        # Таблица позиций
        cols = ("product", "sph", "cyl", "ax", "add", "d", "qty")
        self.items_tree = ttk.Treeview(card, columns=cols, show="headings", style="Data.Treeview")
        headers = {"product": "Товар", "sph": "SPH", "cyl": "CYL", "ax": "AX", "add": "ADD", "d": "D (мм)", "qty": "Количество"}
        widths = {"product": 360, "sph": 70, "cyl": 70, "ax": 60, "add": 70, "d": 70, "qty": 90}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)
        y_scroll = ttk.Scrollbar(card, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y_scroll.set)
        self.items_tree.grid(row=5, column=0, sticky="nsew")
        y_scroll.grid(row=5, column=1, sticky="ns")
        card.rowconfigure(5, weight=1)

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=6, column=0, sticky="w", pady=(8, 0))
        ttk.Button(btns, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left")

        self._refresh_items_view()

    def _add_item(self):
        product = (self.product_var.get() or "").strip()
        if not product:
            messagebox.showinfo("Позиция", "Введите название товара.")
            return
        sph = (self.sph_var.get() or "").strip()
        cyl = (self.cyl_var.get() or "").strip()
        ax = (self.ax_var.get() or "").strip()
        add = (self.add_var.get() or "").strip()
        d = (self.d_var.get() or "").strip()
        try:
            qty = max(1, int(self.qty_var.get()))
        except Exception:
            qty = 1

        item = {"product": product, "sph": sph, "cyl": cyl, "ax": ax, "add": add, "d": d, "qty": str(qty)}
        self.items.append(item)
        self._refresh_items_view()

        # Очистить поля (кроме product)
        self.sph_var.set("")
        self.cyl_var.set("")
        self.ax_var.set("")
        self.add_var.set("")
        self.d_var.set("")
        self.qty_var.set(1)

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
            values = (it.get("product", ""), it.get("sph", ""), it.get("cyl", ""), it.get("ax", ""), it.get("add", ""), it.get("d", ""), it.get("qty", ""))
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
