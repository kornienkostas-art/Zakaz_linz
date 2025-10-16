import tkinter as tk
from tkinter import ttk, messagebox

from app.utils import set_initial_geometry


def _frange(start: float, stop: float, step: float):
    vals = []
    x = start
    # protect against float drift
    while (step > 0 and x <= stop + 1e-9) or (step < 0 and x >= stop - 1e-9):
        vals.append(round(x, 2))
        x = round(x + step, 5)
    return vals


def _format_signed(val: float) -> str:
    # Always show sign and 2 decimals
    return f"{val:+.2f}"


def _parse_num(s: str) -> float | None:
    try:
        s = (s or "").strip().replace(",", ".")
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _transpose_minus_to_plus(sph: float, cyl: float, axis: int) -> tuple[float, float, int]:
    # S' = S + C; C' = -C; Axis' = Axis ± 90 (normalized to 0..180)
    s2 = sph + cyl
    c2 = -cyl
    a2 = (axis + 90) % 180
    # Conventionally represent 0 as 180 for readability (as in example they use 180°)
    if a2 == 0:
        a2 = 180
    return s2, c2, a2


class AstigCalcView(ttk.Frame):
    """Пересчёт астигматических линз (транспозиция цилиндра из минус в плюс)."""

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, padding=0)
        self.master = master
        self.on_back = on_back

        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self, padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Back.TButton", command=self._go_back).pack(side="left")

        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(3, weight=1)

        # Values for comboboxes
        sph_vals = [_format_signed(v) for v in _frange(-20.0, 20.0, 0.25)]
        cyl_vals = [_format_signed(v) for v in _frange(-10.0, 10.0, 0.25)]
        axis_vals = [str(i) for i in range(0, 181, 1)]

        # OD
        ttk.Label(body, text="OD").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(body, text="Sph").grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Cyl").grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Ax").grid(row=0, column=3, sticky="w", padx=(8, 0))

        self.od_sph = ttk.Combobox(body, values=sph_vals)
        self.od_cyl = ttk.Combobox(body, values=cyl_vals)
        self.od_ax = ttk.Combobox(body, values=axis_vals)
        self.od_sph.set("+0.00")
        self.od_cyl.set("-0.25")
        self.od_ax.set("90")
        self.od_sph.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self.od_cyl.grid(row=1, column=2, sticky="ew", padx=(8, 0))
        self.od_ax.grid(row=1, column=3, sticky="ew", padx=(8, 0))

        # OS
        ttk.Label(body, text="OS").grid(row=2, column=0, sticky="w", pady=(12, 4))
        ttk.Label(body, text="Sph").grid(row=2, column=1, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Cyl").grid(row=2, column=2, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Ax").grid(row=2, column=3, sticky="w", padx=(8, 0))

        self.os_sph = ttk.Combobox(body, values=sph_vals)
        self.os_cyl = ttk.Combobox(body, values=cyl_vals)
        self.os_ax = ttk.Combobox(body, values=axis_vals)
        self.os_sph.set("+0.00")
        self.os_cyl.set("-0.25")
        self.os_ax.set("90")
        self.os_sph.grid(row=3, column=1, sticky="ew", padx=(8, 0))
        self.os_cyl.grid(row=3, column=2, sticky="ew", padx=(8, 0))
        self.os_ax.grid(row=3, column=3, sticky="ew", padx=(8, 0))

        # Actions
        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, columnspan=4, sticky="w", pady=(16, 8))
        ttk.Button(actions, text="Пересчитать", command=self._calc).pack(side="left")
        ttk.Button(actions, text="Копировать результат", command=self._copy).pack(side="left", padx=(8, 0))

        # Output
        self.result_text = tk.Text(body, height=6, wrap="word")
        self.result_text.grid(row=5, column=0, columnspan=4, sticky="nsew")
        body.rowconfigure(5, weight=1)

        self._render_initial_example()

    def _render_initial_example(self):
        example = "Результат:"
        try:
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", example)
        except Exception:
            pass

    def _calc_one(self, sph_s: str, cyl_s: str, ax_s: str) -> tuple[float, float, int] | None:
        s = _parse_num(sph_s)
        c = _parse_num(cyl_s)
        try:
            a = int((ax_s or "").strip())
        except Exception:
            a = None
        if s is None or c is None or a is None:
            return None
        a = max(0, min(180, a))
        s2, c2, a2 = _transpose_minus_to_plus(s, c, a)
        # Round to steps of 0.25 for Sph/Cyl
        s2 = round(s2 * 4) / 4
        c2 = round(c2 * 4) / 4
        return s2, c2, a2

    def _calc(self):
        od = self._calc_one(self.od_sph.get(), self.od_cyl.get(), self.od_ax.get())
        os = self._calc_one(self.os_sph.get(), self.os_cyl.get(), self.os_ax.get())
        if od is None or os is None:
            messagebox.showerror("Пересчёт", "Проверьте корректность введённых значений (Sph/Cyl/Axis).")
            return
        od_s, od_c, od_a = od
        os_s, os_c, os_a = os

        text = []
        text.append("Результат:")
        text.append(f"OD: Sph {_format_signed(od_s)} Cyl {_format_signed(od_c)} ax {od_a}°")
        text.append(f"OS: Sph {_format_signed(os_s)} Cyl {_format_signed(os_c)} ax {os_a}°")

        try:
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", "\n".join(text))
        except Exception:
            pass

    def _copy(self):
        try:
            text = self.result_text.get("1.0", "end").strip()
            if not text:
                return
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
        except Exception:
            pass

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()