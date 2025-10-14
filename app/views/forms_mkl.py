import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from app.db import AppDB
from app.utils import set_initial_geometry
from app.utils import format_phone_mask  # used for displaying client phones


class OrderForm(tk.Toplevel):
    """Форма создания/редактирования заказа МКЛ."""
    def __init__(
        self,
        master,
        clients: list[dict],
        products: list[dict],
        on_save=None,
        initial: dict | None = None,
        statuses: list[str] | None = None,
    ):
        super().__init__(master)
        self.title("Редактирование заказа" if initial else "Новый заказ")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=820, min_h=680, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.on_save = on_save
        self.clients = clients
        self.products = products
        self.statuses = statuses or ["Не заказан", "Заказан", "Прозвонен", "Вручен"]
        self.is_new = initial is None

        # Vars
        self.client_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.sph_var = tk.StringVar(value="")
        self.cyl_var = tk.StringVar(value="")
        self.ax_var = tk.StringVar(value="")
        self.bc_var = tk.StringVar(value="")
        self.qty_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))

        # Prefill from initial
        if initial:
            masked_phone = format_phone_mask(initial.get("phone", ""))
            self.client_var.set(f'{initial.get("fio","")} — {masked_phone}'.strip(" —"))
            self.product_var.set(initial.get("product", ""))
            self.sph_var.set(initial.get("sph", ""))
            self.cyl_var.set(initial.get("cyl", ""))
            self.ax_var.set(initial.get("ax", ""))
            self.bc_var.set(initial.get("bc", ""))
            try:
                self.qty_var.set(int(initial.get("qty", 1)))
            except Exception:
                self.qty_var.set(1)

        # Comment var
        self.comment_var = tk.StringVar(value=(initial or {}).get("comment", ""))

        # UI
        self._build_ui()

        # Hotkeys: Esc closes form
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        # Client selection with autocomplete
        ttk.Label(card, text="Клиент (ФИО или телефон)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.client_combo = ttk.Combobox(card, textvariable=self.client_var, values=self._client_values(), height=10)
        self.client_combo.grid(row=1, column=0, sticky="ew")
        self.client_combo.bind("<KeyRelease>", lambda e: self._filter_clients())

        # Product selection with autocomplete
        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        self.product_combo = ttk.Combobox(card, textvariable=self.product_var, values=self._product_values(), height=10)
        self.product_combo.grid(row=1, column=1, sticky="ew")
        self.product_combo.bind("<KeyRelease>", lambda e: self._filter_products())

        ttk.Separator(card).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 12))

        # Row 3: labels
        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=1, sticky="w", padx=(8, 0))
        # Row 4: entries
        self.sph_entry = ttk.Entry(card, textvariable=self.sph_var)
        self.sph_entry.grid(row=4, column=0, sticky="ew", padx=(0, 8))
        self.cyl_entry = ttk.Entry(card, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=4, column=1, sticky="ew", padx=(8, 0))
        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        # Row 5: labels
        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Label(card, text="BC (8.0…9.0, шаг 0.1)", style="Subtitle.TLabel").grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        # Row 6: entries
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=6, column=0, sticky="ew", padx=(0, 8))
        self.bc_entry = ttk.Entry(card, textvariable=self.bc_var)
        self.bc_entry.grid(row=6, column=1, sticky="ew", padx=(8, 0))
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))
        bc_vcmd = (self.register(lambda v: self._vc_decimal(v, 8.0, 9.0)), "%P")
        self.bc_entry.configure(validate="key", validatecommand=bc_vcmd)
        self.bc_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("bc"))

        for w in (self.client_combo, self.product_combo, self.sph_entry, self.cyl_entry, self.ax_entry, self.bc_entry):
            self._bind_clear_shortcuts(w)

        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=8, column=0, sticky="w")

        # Comment field
        ttk.Label(card, text="Комментарий", style="Subtitle.TLabel").grid(row=7, column=1, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(card, textvariable=self.comment_var)
        self.comment_entry.grid(row=8, column=1, sticky="ew")

        footer = ttk.Label(card, text="Дата устанавливается автоматически при создании/смене статуса", style="Subtitle.TLabel")
        footer.grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=10, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Back.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    # Helpers
    def _client_values(self):
        values = []
        for c in self.clients:
            fio = c.get("fio", "")
            phone = format_phone_mask(c.get("phone", ""))
            values.append(f"{fio} — {phone}".strip(" —"))
        return values

    def _product_values(self):
        return [p.get("name", "") for p in self.products]

    def _filter_clients(self):
        term = self.client_var.get().strip().lower()
        values = self._client_values()
        if term:
            values = [v for v in values if term in v.lower()]
        self.client_combo["values"] = values

    def _filter_products(self):
        term = self.product_var.get().strip().lower()
        values = self._product_values()
        if term:
            values = [v for v in values if term in v.lower()]
        self.product_combo["values"] = values

    def _bind_clear_shortcuts(self, widget):
        def clear():
            try:
                widget.delete(0, "end")
            except Exception:
                try:
                    widget.set("")
                except Exception:
                    pass
        widget.bind("<Delete>", lambda e: clear())

    # Validation
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

    def _apply_snap_for(self, field: str):
        if field == "sph":
            self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True))
        elif field == "cyl":
            self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True))
        elif field == "ax":
            self.ax_var.set(self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True))
        elif field == "bc":
            self.bc_var.set(self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True))

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = 0.0 if min_v <= 0.0 <= max_v else min_v
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

    def _parse_client(self, text: str) -> tuple[str, str]:
        t = (text or "").strip()
        if "—" in t:
            parts = t.split("—", 1)
            fio = parts[0].strip()
            phone_digits = re.sub(r"\D", "", parts[1])
            return fio, phone_digits
        term = t.lower()
        for c in self.clients:
            if term in c.get("fio", "").lower() or term in c.get("phone", "").lower():
                return c.get("fio", ""), c.get("phone", "")
        return t, re.sub(r"\D", "", t)

    def _parse_product(self, text: str) -> str:
        t = (text or "").strip()
        for p in self.products:
            if t.lower() == p.get("name", "").lower():
                return p.get("name", "")
        for p in self.products:
            if t.lower() in p.get("name", "").lower():
                return p.get("name", "")
        return t

    def _save(self):
        fio, phone = self._parse_client(self.client_var.get())
        product = self._parse_product(self.product_var.get())

        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=False)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        bc = self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True)
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)
        status = "Не заказан" if self.is_new else (self.status_var.get() or "Не заказан").strip()

        if not fio:
            messagebox.showinfo("Проверка", "Выберите или введите клиента.")
            return
        if not product:
            messagebox.showinfo("Проверка", "Выберите или введите товар.")
            return

        order = {
            "fio": fio,
            "phone": phone,
            "product": product,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "bc": bc,
            "qty": qty,
            "status": status,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        if callable(self.on_save):
            self.on_save(order)
        self.destroy()


class MKLOrderEditorView(ttk.Frame):
    """Встроенная форма создания/редактирования заказа МКЛ, как отдельный вид внутри главного окна."""
    def __init__(self, master: tk.Tk, db: Optional[AppDB], on_back, on_save, initial: dict | None = None):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back
        self.on_save = on_save
        self.is_new = initial is None

        # Fill window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # Load datasets
        self.clients = self.db.list_clients() if self.db else []
        self.products = self.db.list_products_mkl() if self.db else []

        # Vars
        self.client_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.sph_var = tk.StringVar(value="")
        self.cyl_var = tk.StringVar(value="")
        self.ax_var = tk.StringVar(value="")
        self.bc_var = tk.StringVar(value="")
        self.qty_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))

        # Prefill
        if initial:
            masked_phone = format_phone_mask(initial.get("phone", ""))
            self.client_var.set(f'{initial.get("fio","")} — {masked_phone}'.strip(" —"))
            self.product_var.set(initial.get("product", ""))
            self.sph_var.set(initial.get("sph", ""))
            self.cyl_var.set(initial.get("cyl", ""))
            self.ax_var.set(initial.get("ax", ""))
            self.bc_var.set(initial.get("bc", ""))
            try:
                self.qty_var.set(int(initial.get("qty", 1)))
            except Exception:
                self.qty_var.set(1)

        self._build_ui()

    def _build_ui(self):
        # Toolbar with back
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        # Client selection
        ttk.Label(card, text="Клиент (ФИО или телефон)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.client_combo = ttk.Combobox(card, textvariable=self.client_var, values=self._client_values(), height=10)
        self.client_combo.grid(row=1, column=0, sticky="ew")
        self.client_combo.bind("<KeyRelease>", lambda e: self._filter_clients())

        # Product selection
        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        self.product_combo = ttk.Combobox(card, textvariable=self.product_var, values=self._product_values(), height=10)
        self.product_combo.grid(row=1, column=1, sticky="ew")
        self.product_combo.bind("<KeyRelease>", lambda e: self._filter_products())

        ttk.Separator(card).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 12))

        # Row 3: labels
        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=1, sticky="w", padx=(8, 0))
        # Row 4: entries
        self.sph_entry = ttk.Entry(card, textvariable=self.sph_var)
        self.sph_entry.grid(row=4, column=0, sticky="ew", padx=(0, 8))
        self.cyl_entry = ttk.Entry(card, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=4, column=1, sticky="ew", padx=(8, 0))
        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        # Row 5: labels
        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Label(card, text="BC (8.0…9.0, шаг 0.1)", style="Subtitle.TLabel").grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        # Row 6: entries
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=6, column=0, sticky="ew", padx=(0, 8))
        self.bc_entry = ttk.Entry(card, textvariable=self.bc_var)
        self.bc_entry.grid(row=6, column=1, sticky="ew", padx=(8, 0))
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))
        bc_vcmd = (self.register(lambda v: self._vc_decimal(v, 8.0, 9.0)), "%P")
        self.bc_entry.configure(validate="key", validatecommand=bc_vcmd)
        self.bc_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("bc"))

        for w in (self.client_combo, self.product_combo, self.sph_entry, self.cyl_entry, self.ax_entry, self.bc_entry):
            self._bind_clear_shortcuts(w)

        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=8, column=0, sticky="w")

        footer = ttk.Label(card, text="Дата устанавливается автоматически при создании/смене статуса", style="Subtitle.TLabel")
        footer.grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=10, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self._go_back).pack(side="right", padx=(8, 0))

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    # Helpers: values for combo and filtering
    def _client_values(self):
        values = []
        for c in self.clients:
            fio = c.get("fio", "")
            phone = format_phone_mask(c.get("phone", ""))
            values.append(f"{fio} — {phone}".strip(" —"))
        return values

    def _product_values(self):
        return [p.get("name", "") for p in self.products]

    def _filter_clients(self):
        term = self.client_var.get().strip().lower()
        values = self._client_values()
        if term:
            values = [v for v in values if term in v.lower()]
        self.client_combo["values"] = values

    def _filter_products(self):
        term = self.product_var.get().strip().lower()
        values = self._product_values()
        if term:
            values = [v for v in values if term in v.lower()]
        self.product_combo["values"] = values

    def _bind_clear_shortcuts(self, widget):
        def clear():
            try:
                widget.delete(0, "end")
            except Exception:
                try:
                    widget.set("")
                except Exception:
                    pass
        widget.bind("<Delete>", lambda e: clear())

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

    def _apply_snap_for(self, field: str):
        if field == "sph":
            self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True))
        elif field == "cyl":
            self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True))
        elif field == "ax":
            self.ax_var.set(self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True))
        elif field == "bc":
            self.bc_var.set(self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True))

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = 0.0 if min_v <= 0.0 <= max_v else min_v
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

    def _parse_client(self, text: str) -> tuple[str, str]:
        t = (text or "").strip()
        if "—" in t:
            parts = t.split("—", 1)
            fio = parts[0].strip()
            phone_digits = re.sub(r"\\D", "", parts[1])
            return fio, phone_digits
        term = t.lower()
        for c in self.clients:
            if term in c.get("fio", "").lower() or term in c.get("phone", "").lower():
                return c.get("fio", ""), c.get("phone", "")
        return t, re.sub(r"\\D", "", t)

    def _parse_product(self, text: str) -> str:
        t = (text or "").strip()
        for p in self.products:
            if t.lower() == p.get("name", "").lower():
                return p.get("name", "")
        for p in self.products:
            if t.lower() in p.get("name", "").lower():
                return p.get("name", "")
        return t

    def _save(self):
        fio, phone = self._parse_client(self.client_var.get())
        product = self._parse_product(self.product_var.get())

        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=False)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        bc = self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True)
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)
        status = "Не заказан" if self.is_new else (self.status_var.get() or "Не заказан").strip()

        if not fio:
            messagebox.showinfo("Проверка", "Выберите или введите клиента.")
            return
        if not product:
            messagebox.showinfo("Проверка", "Выберите или введите товар.")
            return

        order = {
            "fio": fio,
            "phone": phone,
            "product": product,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "bc": bc,
            "qty": qty,
            "status": status,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": (self.comment_var.get() or "").strip(),
        }
        cb = getattr(self, "on_save", None)
        if callable(cb):
            cb(order)
        self._go_back()


