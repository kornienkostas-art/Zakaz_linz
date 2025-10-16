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
    """Пересчёт астигматических линз (транспозиция цилиндра из минус в плюс).

    Улучшенный ввод Sph/Cyl/Ax:
    - Прокрутка колёсиком: Sph/Cyl по 0.25D, Axis по 1°.
    - Кнопки +/- рядом с полями.
    - Нормализация формата при потере фокуса.
    - Горячие клавиши Ctrl+↑/↓ (±шаг).
    - Кнопка «OD → OS».
    - Попытка «Вставить из буфера» (распознаёт простые форматы рецепта).
    """

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, padding=0)
        self.master = master
        self.on_back = on_back

        self.pack(fill="both", expand=True)
        self._build_ui()

    # ---- Helpers for stepping/normalization -------------------------------------------------

    def _step_value(self, val_str: str, step: float, lo: float, hi: float, round_to: float, signed: bool) -> str:
        v = _parse_num(val_str)
        if v is None:
            v = 0.0
        v = v + step
        v = max(lo, min(hi, v))
        if round_to:
            v = round(v / round_to) * round_to
        return _format_signed(v) if signed else f"{int(round(v))}"

    def _normalize_value(self, val_str: str, lo: float, hi: float, round_to: float, signed: bool) -> str:
        v = _parse_num(val_str)
        if v is None:
            v = 0.0
        v = max(lo, min(hi, v))
        if round_to:
            v = round(v / round_to) * round_to
        return _format_signed(v) if signed else f"{int(round(v))}"

    def _bind_spin(self, widget: ttk.Combobox, step: float, lo: float, hi: float, round_to: float, signed: bool):
        # Mouse wheel
        def on_wheel(event):
            delta = 0
            if event.num == 4:   # X11 up
                delta = +1
            elif event.num == 5: # X11 down
                delta = -1
            else:
                # Windows/Mac
                delta = +1 if event.delta > 0 else -1
            new = self._step_value(widget.get(), delta * step, lo, hi, round_to, signed)
            widget.set(new)
            return "break"

        widget.bind("<MouseWheel>", on_wheel)
        widget.bind("<Button-4>", on_wheel)
        widget.bind("<Button-5>", on_wheel)

        # Keyboard
        def on_key(event):
            if (event.state & 0x4) != 0:  # Ctrl pressed
                if event.keysym in ("Up", "KP_Up"):
                    widget.set(self._step_value(widget.get(), +step, lo, hi, round_to, signed))
                    return "break"
                if event.keysym in ("Down", "KP_Down"):
                    widget.set(self._step_value(widget.get(), -step, lo, hi, round_to, signed))
                    return "break"
            return None

        widget.bind("<KeyPress>", on_key)

        # Normalize on focus out
        def on_focus_out(_):
            widget.set(self._normalize_value(widget.get(), lo, hi, round_to, signed))

        widget.bind("<FocusOut>", on_focus_out)

    def _make_input_with_steppers(self, parent, values, default, step, lo, hi, round_to, signed, grid_opts):
        box = ttk.Frame(parent)
        box.grid(**grid_opts)
        cb = ttk.Combobox(box, values=values, width=10)
        cb.set(default)
        cb.pack(side="left", fill="x", expand=True)

        btns = ttk.Frame(box)
        btns.pack(side="left", padx=(4, 0))
        plus = ttk.Button(btns, text="+", width=2, command=lambda: cb.set(self._step_value(cb.get(), +step, lo, hi, round_to, signed)))
        minus = ttk.Button(btns, text="−", width=2, command=lambda: cb.set(self._step_value(cb.get(), -step, lo, hi, round_to, signed)))
        plus.pack(side="top", pady=(0, 2))
        minus.pack(side="top")

        self._bind_spin(cb, step, lo, hi, round_to, signed)
        return cb

    # -----------------------------------------------------------------------------------------

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

        self.od_sph = self._make_input_with_steppers(
            body, sph_vals, "+0.00", step=0.25, lo=-20.0, hi=20.0, round_to=0.25, signed=True,
            grid_opts=dict(row=1, column=1, sticky="ew", padx=(8, 0))
        )
        self.od_cyl = self._make_input_with_steppers(
            body, cyl_vals, "-0.25", step=0.25, lo=-10.0, hi=10.0, round_to=0.25, signed=True,
            grid_opts=dict(row=1, column=2, sticky="ew", padx=(8, 0))
        )
        self.od_ax = self._make_input_with_steppers(
            body, axis_vals, "90", step=1.0, lo=0.0, hi=180.0, round_to=1.0, signed=False,
            grid_opts=dict(row=1, column=3, sticky="ew", padx=(8, 0))
        )

        # OS
        ttk.Label(body, text="OS").grid(row=2, column=0, sticky="w", pady=(12, 4))
        ttk.Label(body, text="Sph").grid(row=2, column=1, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Cyl").grid(row=2, column=2, sticky="w", padx=(8, 0))
        ttk.Label(body, text="Ax").grid(row=2, column=3, sticky="w", padx=(8, 0))

        self.os_sph = self._make_input_with_steppers(
            body, sph_vals, "+0.00", step=0.25, lo=-20.0, hi=20.0, round_to=0.25, signed=True,
            grid_opts=dict(row=3, column=1, sticky="ew", padx=(8, 0))
        )
        self.os_cyl = self._make_input_with_steppers(
            body, cyl_vals, "-0.25", step=0.25, lo=-10.0, hi=10.0, round_to=0.25, signed=True,
            grid_opts=dict(row=3, column=2, sticky="ew", padx=(8, 0))
        )
        self.os_ax = self._make_input_with_steppers(
            body, axis_vals, "90", step=1.0, lo=0.0, hi=180.0, round_to=1.0, signed=False,
            grid_opts=dict(row=3, column=3, sticky="ew", padx=(8, 0))
        )

        # Actions
        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, columnspan=4, sticky="w", pady=(16, 8))
        ttk.Button(actions, text="OD → OS", command=self._copy_od_to_os).pack(side="left")
        ttk.Button(actions, text="Вставить из буфера", command=self._paste_from_clipboard).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Пересчитать", command=self._calc).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Копировать результат", command=self._copy).pack(side="left", padx=(8, 0))

        # Output
        self.result_text = tk.Text(body, height=6, wrap="word")
        self.result_text.grid(row=5, column=0, columnspan=4, sticky="nsew")
        body.rowconfigure(5, weight=1)

        self._render_initial_example()

    def _render_initial_example(self):
        example = (
            "Пример:\n"
            "Ваш рецепт:\n"
            "OD: Сфера(Sph) +3.00 Цилиндр(Cyl) -0.25 Ось(ax) 90°\n"
            "OS: Сфера(Sph) +2.50 Цилиндр(Cyl) -3.00 Ось(ax) 60°\n\n"
            "Результат:\n"
            "OD: Sph +2.75 Cyl +0.25 ax 180°\n"
            "OS: Sph -0.50 Cyl +3.00 ax 150°\n"
        )
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
        text.append("Ваш рецепт:")
        text.append(f"OD: Сфера(Sph) {self.od_sph.get()} Цилиндр(Cyl) {self.od_cyl.get()} Ось(ax) {self.od_ax.get()}°")
        text.append(f"OS: Сфера(Sph) {self.os_sph.get()} Цилиндр(Cyl) {self.os_cyl.get()} Ось(ax) {self.os_ax.get()}°")
        text.append("")
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

    # Convenience actions -------------------------------------------------------

    def _copy_od_to_os(self):
        try:
            self.os_sph.set(self._normalize_value(self.od_sph.get(), -20.0, 20.0, 0.25, True))
            self.os_cyl.set(self._normalize_value(self.od_cyl.get(), -10.0, 10.0, 0.25, True))
            self.os_ax.set(self._normalize_value(self.od_ax.get(), 0.0, 180.0, 1.0, False))
        except Exception:
            pass

    def _paste_from_clipboard(self):
        try:
            text = self.master.clipboard_get()
        except Exception:
            return
        if not text:
            return
        # Very simple parser for common formats:
        # "OD: Sph +3.00 Cyl -1.25 ax 90°"
        # "+3.00 -1.25 x 90", etc.
        import re

        def parse_side(s: str):
            # Extract three numbers: sph, cyl, axis
            s_norm = s.replace(",", ".")
            # Try explicit labels
            m = re.search(r"Sph\\s*([+\\-]?\\d+(?:\\.\\d+)?)", s_norm, re.I)
            sph = m.group(1) if m else None
            m = re.search(r"Cyl\\s*([+\\-]?\\d+(?:\\.\\d+)?)", s_norm, re.I)
            cyl = m.group(1) if m else None
            m = re.search(r"(?:Ax|Axis|x|×|x)\\s*([\\d]{1,3})", s_norm, re.I)
            axis = m.group(1) if m else None
            # Fallback: three numbers in order
            if not (sph and cyl and axis):
                nums = re.findall(r"[+\\-]?\\d+(?:\\.\\d+)?", s_norm)
                if len(nums) >= 3:
                    sph = sph or nums[0]
                    cyl = cyl or nums[1]
                    axis = axis or nums[2]
            return sph, cyl, axis

        # Split by lines; try to find lines starting with OD/OS
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        od_line = next((ln for ln in lines if ln.upper().startswith("OD")), None)
        os_line = next((ln for ln in lines if ln.upper().startswith("OS")), None)

        if od_line:
            sph, cyl, ax = parse_side(od_line)
            if sph: self.od_sph.set(self._normalize_value(sph, -20.0, 20.0, 0.25, True))
            if cyl: self.od_cyl.set(self._normalize_value(cyl, -10.0, 10.0, 0.25, True))
            if ax:  self.od_ax.set(self._normalize_value(ax, 0.0, 180.0, 1.0, False))
        if os_line:
            sph, cyl, ax = parse_side(os_line)
            if sph: self.os_sph.set(self._normalize_value(sph, -20.0, 20.0, 0.25, True))
            if cyl: self.os_cyl.set(self._normalize_value(cyl, -10.0, 10.0, 0.25, True))
            if ax:  self.os_ax.set(self._normalize_value(ax, 0.0, 180.0, 1.0, False))
        # If no labels, but got a single line with three numbers, apply to OD
        if not od_line and not os_line and len(lines) == 1:
            sph, cyl, ax = parse_side(lines[0])
            if sph and cyl and ax:
                self.od_sph.set(self._normalize_value(sph, -20.0, 20.0, 0.25, True))
                self.od_cyl.set(self._normalize_value(cyl, -10.0, 10.0, 0.25, True))
                self.od_ax.set(self._normalize_value(ax, 0.0, 180.0, 1.0, False))

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()