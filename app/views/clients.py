import re
import tkinter as tk
from tkinter import ttk, messagebox

from app.utils import format_phone_mask
from app.db import AppDB  # type hint only


class ClientsView(ttk.Frame):
    """Список клиентов как встроенный вид (CRUD с SQLite) с кнопкой 'Назад'."""
    def __init__(self, master: tk.Tk, db: AppDB | None, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.db = db
        self.on_back = on_back

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self._dataset: list[dict] = []
        self._filtered: list[dict] = []

        self._build_ui()
        self._reload()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        search_card = ttk.Frame(self, style="Card.TFrame", padding=16)
        search_card.pack(fill="x")

        ttk.Label(search_card, text="Поиск по ФИО или телефону", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_card, textvariable=self.search_var, width=40)
        entry.grid(row=1, column=0, sticky="w")
        entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        btns = ttk.Frame(search_card, style="Card.TFrame")
        btns.grid(row=1, column=1, sticky="w", padx=(12, 0))
        ttk.Button(btns, text="Добавить", style="Menu.TButton", command=self._add).pack(side="left")
        ttk.Button(btns, text="Редактировать", style="Menu.TButton", command=self._edit).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Удалить", style="Menu.TButton", command=self._delete).pack(side="left", padx=(8, 0))

        table_card = ttk.Frame(self, style="Card.TFrame", padding=16)
        table_card.pack(fill="both", expand=True)

        columns = ("fio", "phone")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", style="Data.Treeview")
        self.tree.heading("fio", text="ФИО", anchor="w")
        self.tree.heading("phone", text="Телефон", anchor="w")
        self.tree.column("fio", width=380, anchor="w")
        self.tree.column("phone", width=220, anchor="w")

        y_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        self._refresh_view()

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()

    def _reload(self):
        try:
            self._dataset = self.db.list_clients() if self.db else []
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось загрузить клиентов:\n{e}")
            self._dataset = []
        self._apply_filter()

    def _apply_filter(self):
        term = self.search_var.get().strip().lower()
        if not term:
            self._filtered = list(self._dataset)
        else:
            self._filtered = [c for c in self._dataset if term in c.get("fio", "").lower() or term in c.get("phone", "").lower()]
        self._refresh_view()

    def _refresh_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self._filtered):
            masked_phone = format_phone_mask(item.get("phone", ""))
            self.tree.insert("", "end", iid=str(idx), values=(item.get("fio", ""), masked_phone))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите запись.")
            return None
        return int(sel[0])

    def _add(self):
        ClientForm(self, on_save=self._on_add_save)

    def _on_add_save(self, data: dict):
        try:
            if self.db:
                self.db.add_client(data.get("fio", ""), data.get("phone", ""))
            else:
                self._dataset.append({"id": None, **data})
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось добавить клиента:\n{e}")
        self._reload()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        ClientForm(self, initial=item.copy(), on_save=lambda d: self._on_edit_save(item, d))

    def _on_edit_save(self, original_item: dict, data: dict):
        try:
            if self.db and original_item.get("id") is not None:
                self.db.update_client(original_item["id"], data.get("fio", ""), data.get("phone", ""))
            else:
                original_item.update(data)
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось обновить клиента:\n{e}")
        self._reload()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранного клиента?"):
            try:
                if self.db and item.get("id") is not None:
                    self.db.delete_client(item["id"])
                else:
                    self._dataset.remove(item)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось удалить клиента:\n{e}")
            self._reload()


class ClientForm(tk.Toplevel):
    def __init__(self, master, initial: dict | None = None, on_save=None):
        super().__init__(master)
        self.title("Карточка клиента")
        self.configure(bg="#f8fafc")
        from app.utils import set_initial_geometry  # local import to avoid cycles
        set_initial_geometry(self, min_w=480, min_h=280, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        self.vars = {
            "fio": tk.StringVar(value=(initial or {}).get("fio", "")),
            "phone": tk.StringVar(value=(initial or {}).get("phone", "")),
        }

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="ФИО", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        fio_entry = ttk.Entry(card, textvariable=self.vars["fio"])
        fio_entry.grid(row=1, column=0, sticky="ew")
        # Автофокус на первое поле ввода
        try:
            self.after(50, lambda: fio_entry.focus_set())
        except Exception:
            pass

        ttk.Label(card, text="Телефон", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(card, textvariable=self.vars["phone"]).grid(row=3, column=0, sticky="ew")

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        card.columnconfigure(0, weight=1)

    def _save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["fio"]:
            messagebox.showinfo("Проверка", "Введите ФИО.")
            return
        if not data["phone"]:
            messagebox.showinfo("Проверка", "Введите телефон.")
            return
        data["phone"] = re.sub(r"\D", "", data["phone"])
        if self.on_save:
            self.on_save(data)
        self.destroy()