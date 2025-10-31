import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from datetime import datetime

from app.utils import set_initial_geometry
from app.utils import create_tooltip


from tkinter import font as tkfont



class MeridianProductPickerInline(ttk.Label(right, text="Количество (1…20)").grid(row=2, column=4, sticky="w", padx=(12, 0), pady=(6, 0))
        ttk.Spinbox(right, from_=1, to=20, textvariable=self.qty_var, width=7).grid(row=2, column=5, sticky="w", pady=(6, 0))Frame):
    """Встроенная панель выбора товара с группами + свободный ввод имени и корзиной позиций."""
    def __init__(self, master, db, on_done, on_cancel=None, initial_item: dict | None = None):
        super().__init__(master, style="Card.TFrame", padding=12)
        self.db = db
        self.on_done = on_done
        self.on_cancel = on_cancel
        self._basket: list[dict] = []
        self._build_ui()
        # Гарантируем начальное наполнение (если таблицы пустые)
        try:
            self._ensure_seed()
        except Exception:
            pass
        # Если пришла исходная позиция (режим редактирования) — заполним поля и корзину
        if initial_item:
            try:
                name = (initial_item.get("product", "") or "").strip()
                self.free_name_var.set(name)
                self.sel_product_var.set(name)
                self.sel_label.configure(text=name)
                self.sph_var.set(initial_item.get("sph", ""))
                self.cyl_var.set(initial_item.get("cyl", ""))
                self.ax_var.set(initial_item.get("ax", ""))
                self.d_var.set(initial_item.get("d", ""))
                try:
                    self.qty_var.set(int(initial_item.get("qty", 1)))
                except Exception:
                    self.qty_var.set(1)
                # Панель сама закроется после добавления в заказ (через on_cancel внутри _done)
        panel = MeridianProductPickerInline(
            self._card,
            db,
            on_done=lambda items: (self.items.extend(items), self._refresh_items_view()),
            on_cancel=self._close_picker,
            initial_item=initial_item,
        )
        # Размещаем панель на всю доступную область
        try:
            panel.grid(row=5, column=0, sticky="nsew", pady=(0, 0))
        except Exception:
            panel.pack(fill="both", expand=True, pady=(0, 0))
        self._picker_panel = panelоказать в корзине текущую позицию для наглядности
                self._basket = [initial_item.copy()]
            except Exception:
                pass
        self._load_tree()
        # Обновим корзину, если заполнили начальное
        try:
            self._refresh_basket()
        except Exception:
            pass
        # Initial autosize
        try:
            self._autosize_tree_column()
        except Exception:
            pass
        try:
            self._autosize_basket_columns()
        except Exception:
            pass

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
