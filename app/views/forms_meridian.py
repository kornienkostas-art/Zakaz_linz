import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.utils import set_initial_geometry
from app.utils import create_tooltip


class MeridianProductPickerInline(ttk.Frame):
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
                # Показать в корзине текущую позицию для наглядности
                self._basket = [initial_item.copy()]
            except Exception:
                pass
        self._load_tree()
        # Обновим корзину, если заполнили начальное
        try:
            self._refresh_basket()
        except Exception:
            pass

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(3, weight=1)

        # Search + free product entry
        top = ttk.Frame(self, style="Card.TFrame")
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Поиск:", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ent_search = ttk.Entry(top, textvariable=self.search_var)
        ent_search.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        ent_search.bind("<KeyRelease>", lambda e: self._load_tree())

        ttk.Label(top, text="Свободный ввод товара:", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.free_name_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.free_name_var).grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(8, 0))

        # Tree
        self.tree = ttk.Treeview(self, show="tree", style="Data.Treeview")
