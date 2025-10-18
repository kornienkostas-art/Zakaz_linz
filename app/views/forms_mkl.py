import tkinter as tk
from tkinter import ttk
from datetime import datetime

from app.utils import set_initial_geometry
from app.utils import create_tooltip


class OrderForm(tk.Toplevel):
    """Форма создания/редактирования заказа МКЛ без клиента и товара."""
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
        set_initial_geometry(self, min_w=720, min_h=560, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.on_save = on_save
        self.is_new = initial is None

        # Vars
        self.sph_var = tk.StringVar(value=(initial or {}).get("sph", ""))
        self.cyl_var = tk.StringVar(value=(initial or {}).get("cyl", ""))
        self.ax_var = tk.StringVar(value=(initial or {}).get("ax", ""))
        self.bc_var = tk.StringVar(value=(initial or {}).get("bc", ""))
        try:
            init_qty = int((initial or {}).get("qty", 1))
        except Exception:
            init_qty = 1
        self.qty_var = tk.IntVar(value=init_qty)
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.comment_var = tk.StringVar(value=(initial or {}).get("comment", ""))

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Separator(card).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w", padx=(8, 0))

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

        sph_row = ttk.Frame(card, style="Card.TFrame")
        sph_row.grid(row=2, column=0, sticky="ew", padx=(0, 8))
        sph_row.columnconfigure(1, weight=1)
        btn_sph_dec = ttk.Button(sph_row, text="−", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, -1))
        btn_sph_dec.grid(row=0, column=0, sticky="w")
        self.sph_entry = ttk.Entry(sph_row, textvariable=self.sph_var)
        self.sph_entry.grid(row=0, column=1, sticky="ew", padx=4)
        btn_sph_inc = ttk.Button(sph_row, text="+", width=3, command=lambda: _nudge(self.sph_var, -30.0, 30.0, 0.25, +1))
        btn_sph_inc.grid(row=0, column=2, sticky="e")
        try:
            create_tooltip(btn_sph_dec, "SPH: уменьшить на 0.25. Диапазон: −30.00…+30.00")
            create_tooltip(btn_sph_inc, "SPH: увеличить на 0.25. Диапазон: −30.00…+30.00")
        except Exception:
            pass

        cyl_row = ttk.Frame(card, style="Card.TFrame")
        cyl_row.grid(row=2, column=1, sticky="ew", padx=(8, 0))
        cyl_row.columnconfigure(1, weight=1)
        btn_cyl_dec = ttk.Button(cyl_row, text="−", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, -1))
        btn_cyl_dec.grid(row=0, column=0, sticky="w")
        self.cyl_entry = ttk.Entry(cyl_row, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=0, column=1, sticky="ew", padx=4)
        btn_cyl_inc = ttk.Button(cyl_row, text="+", width=3, command=lambda: _nudge(self.cyl_var, -10.0, 10.0, 0.25, +1))
        btn_cyl_inc.grid(row=0, column=2, sticky="e")
        try:
            create_tooltip(btn_cyl_dec, "CYL: уменьшить на 0.25. Диапазон: −10.00…+10.00")
            create_tooltip(btn_cyl_inc, "CYL: увеличить на 0.25. Диапазон: −10.00…+10.00")
        except Exception:
            pass

        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Label(card, text="BC (8.0…9.0, шаг 0.1)", style="Subtitle.TLabel").grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=4, column=0, sticky="ew", padx=(0, 8))
        self.bc_entry = ttk.Entry(card, textvariable=self.bc_var)
        self.bc_entry.grid(row=4, column=1, sticky="ew", padx=(8, 0))
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))
        bc_vcmd = (self.register(lambda v: self._vc_decimal(v, 8.0, 9.0)), "%P")
        self.bc_entry.configure(validate="key", validatecommand=bc_vcmd)
        self.bc_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("bc"))

        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=6, column=0, sticky="w")

        ttk.Label(card, text="Комментарий", style="Subtitle.TLabel").grid(row=5, column=1, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(card, textvariable=self.comment_var)
        self.comment_entry.grid(row=6, column=1, sticky="ew")

        footer = ttk.Label(card, text="Дата устанавливается автоматически при создании/смене статуса", style="Subtitle.TLabel")
        footer.grid(row=7, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Back.TButton", command=self._go_back).pack(side="right", padx=(8, 0))

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

    def _go_back(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "on_back", None)
            if callable(cb):
                cb()

    def _save(self):
        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=False)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        bc = self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True)
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)

        order = {
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "bc": bc,
            "qty": qty,
            "status": (self.status_var.get() or "Не заказан").strip(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": (self.comment_var.get() or "").strip(),
        }
        cb = getattr(self, "on_save", None)
        if callable(cb):
            cb(order)
        self._go_back()


