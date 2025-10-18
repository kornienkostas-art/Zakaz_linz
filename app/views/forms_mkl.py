import tkinter as tk
from tkinter import ttk
from datetime import datetime

from app.utils import set_initial_geometry, format_phone_mask


class OrderForm(tk.Toplevel):
    """Простая форма создания/редактирования заказа МКЛ (редактор существующего заказа)."""
    def __init__(self, master, clients: list[dict], products: list[dict], on_save=None, initial: dict | None = None, statuses: list[str] | None = None):
        super().__init__(master)
        self.title("Редактирование заказа" if initial else "Новый заказ")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=800, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.on_save = on_save
        self.clients = clients or []
        self.products = products or []
        self.statuses = statuses or ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

        self.fio_var = tk.StringVar(value=(initial or {}).get("fio", ""))
        phone_init = format_phone_mask((initial or {}).get("phone", ""))
        self.phone_var = tk.StringVar(value=phone_init)
        self.product_var = tk.StringVar(value=(initial or {}).get("product", ""))
        self.sph_var = tk.StringVar(value=(initial or {}).get("sph", ""))
        self.cyl_var = tk.StringVar(value=(initial or {}).get("cyl", ""))
        self.ax_var = tk.StringVar(value=(initial or {}).get("ax", ""))
        self.bc_var = tk.StringVar(value=(initial or {}).get("bc", ""))
        self.qty_var = tk.IntVar(value=int((initial or {}).get("qty", 1) or 1))
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.comment_var = tk.StringVar(value=(initial or {}).get("comment", ""))

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        for i in range(2):
            card.columnconfigure(i, weight=1)

        ttk.Label(card, text="ФИО", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.fio_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(card, text="Телефон", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Entry(card, textvariable=self.phone_var).grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.product_var).grid(row=3, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(card, text="SPH", style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.sph_var).grid(row=5, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(card, text="CYL", style="Subtitle.TLabel").grid(row=4, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.cyl_var).grid(row=5, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(card, text="AX", style="Subtitle.TLabel").grid(row=6, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.ax_var).grid(row=7, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(card, text="BC", style="Subtitle.TLabel").grid(row=6, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.bc_var).grid(row=7, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(card, text="Количество", style="Subtitle.TLabel").grid(row=8, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var).grid(row=9, column=0, sticky="w")

        ttk.Label(card, text="Комментарий", style="Subtitle.TLabel").grid(row=8, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(card, textvariable=self.comment_var).grid(row=9, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(card, text="Статус", style="Subtitle.TLabel").grid(row=10, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(card, textvariable=self.status_var, values=self.statuses, height=6).grid(row=11, column=0, sticky="w")

        ttk.Separator(card).grid(row=12, column=0, columnspan=2, sticky="ew", pady=(12, 12))
        actions = ttk.Frame(card, style="Card.TFrame")
        actions.grid(row=13, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(actions, text="Отмена", style="Back.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    def _save(self):
        order = {
            "fio": (self.fio_var.get() or "").strip(),
            "phone": (self.phone_var.get() or "").strip(),
            "product": (self.product_var.get() or "").strip(),
            "sph": (self.sph_var.get() or "").strip(),
            "cyl": (self.cyl_var.get() or "").strip(),
            "ax": (self.ax_var.get() or "").strip(),
            "bc": (self.bc_var.get() or "").strip(),
            "qty": str(self.qty_var.get()),
            "status": (self.status_var.get() or "Не заказан").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": (self.comment_var.get() or "").strip(),
        }
        cb = getattr(self, "on_save", None)
        if callable(cb):
            cb(order)
        self.destroy()


