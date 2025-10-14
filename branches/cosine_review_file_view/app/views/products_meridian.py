import tkinter as tk
from tkinter import ttk, messagebox

from app.db import AppDB  # type hint only

class ProductsMeridianView(ttk.Frame):
    """Справочник товаров для Меридиан (таблица products_meridian)."""
    def __init__(self, master: tk.Tk, db: AppDB | None, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self._dataset: list[dict] = []
        self._build_ui()
        self._reload()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        table_card = ttk.Frame(self, style="Card.TFrame", padding=16)
        table_card.pack(fill="both", expand=True)

        header = ttk.Label(table_card, text="Товары (Меридиан)", style="Title.TLabel")
        header.grid(row=0, column=0, sticky="w", columnspan=2)
        ttk.Separator(table_card).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 12))

        bar = ttk.Frame(table_card, style="Card.TFrame")
        bar.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Button(bar, text="Добавить", style="Menu.TButton", command=self._add).pack(side="left")
        ttk.Button(bar, text="Редактировать", style="Menu.TButton", command=self._edit).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить", style="Menu.TButton", command=self._delete).pack(side="left", padx=(8, 0))

        columns = ("name",)
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", style="Data.Treeview")
        self.tree.heading("name", text="Название товара", anchor="w")
        self.tree.column("name", width=600, anchor="w")

        y_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)

        self.tree.grid(row=3, column=0, sticky="nsew")
        y_scroll.grid(row=3, column=1, sticky="ns")
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(3, weight=1)

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _reload(self):
        try:
            self._dataset = self.db.list_products_meridian() if self.db else []
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось загрузить товары:\n{e}")
            self._dataset = []
        self._refresh_view()

    def _refresh_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self._dataset):
            self.tree.insert("", "end", iid=str(idx), values=(item.get("name", ""),))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите товар.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _add(self):
        ProductForm(self, on_save=self._on_add_save)

    def _on_add_save(self, data: dict):
        try:
            if self.db:
                self.db.add_product_meridian(data.get("name", ""))
            else:
                self._dataset.append({"id": None, **data})
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось добавить товар:\n{e}")
        self._reload()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._dataset[idx]
        ProductForm(self, initial=item.copy(), on_save=lambda d: self._on_edit_save(item, d))

    def _on_edit_save(self, original_item: dict, data: dict):
        try:
            if self.db and original_item.get("id") is not None:
                self.db.update_product_meridian(original_item["id"], data.get("name", ""))
            else:
                original_item.update(data)
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось обновить товар:\n{e}")
        self._reload()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._dataset[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранный товар?"):
            try:
                if self.db and item.get("id") is not None:
                    self.db.delete_product_meridian(item["id"])
                else:
                    self._dataset.remove(item)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось удалить товар:\n{e}")
            self._reload()

class ProductForm(tk.Toplevel):
    def __init__(self, master, initial: dict | None = None, on_save=None):
        super().__init__(master)
        self.title("Карточка товара (Меридиан)")
        self.configure(bg="#f8fafc")
        set_initial_geometry = __import__("app.utils", fromlist=["set_initial_geometry"]).set_initial_geometry
        set_initial_geometry(self, min_w=600, min_h=260, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.on_save = on_save
        self.vars = {
            "name": tk.StringVar(value=(initial or {}).get("name", "")),
        }

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Название товара", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.vars["name"]).grid(row=1, column=0, sticky="ew")

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=2, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        card.columnconfigure(0, weight=1)

    def _save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["name"]:
            messagebox.showinfo("Проверка", "Введите название товара.")
            return
        if self.on_save:
            self.on_save(data)
        self.destroy()