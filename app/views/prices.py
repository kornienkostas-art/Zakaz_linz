import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from app.utils import set_initial_geometry, fade_transition
from app.db import AppDB


class PricesView(ttk.Frame):
    """Список прайсов: добавить, редактировать, открыть."""

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, padding=0)
        self.master = master
        self.on_back = on_back
        self.db: AppDB = getattr(self.master, "db", None)

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._reload()

    def _build_ui(self):
        toolbar = ttk.Frame(self, padding=(16, 12))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="← Назад", style="Back.TButton", command=self._go_back).pack(side="left")

        ttk.Button(toolbar, text="Добавить", command=self._add).pack(side="right")
        ttk.Button(toolbar, text="Редактировать", command=self._edit).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Удалить", command=self._delete).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Открыть", command=self._open_selected).pack(side="right", padx=(8, 0))

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("name", "path")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Название")
        self.tree.heading("path", text="Путь к файлу")
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("path", width=600, anchor="w")
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Double click opens
        self.tree.bind("<Double-1>", lambda e: self._open_selected())

    def _reload(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            items = self.db.list_prices() if self.db else []
        except Exception:
            items = []
        for it in items:
            self.tree.insert("", "end", iid=str(it["id"]), values=(it["name"], it["path"]))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def _add(self):
        self._open_form()

    def _edit(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("Прайсы", "Выберите запись для редактирования.")
            return
        # get data
        try:
            all_items = self.db.list_prices()
            item = next((x for x in all_items if x["id"] == pid), None)
        except Exception:
            item = None
        self._open_form(item)

    def _delete(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("Прайсы", "Выберите запись для удаления.")
            return
        try:
            all_items = self.db.list_prices()
            item = next((x for x in all_items if x["id"] == pid), None)
        except Exception:
            item = None
        if not item:
            return
        name = item.get("name") or ""
        if not messagebox.askyesno("Удалить прайс", f"Удалить '{name}'?"):
            return
        try:
            self.db.delete_price(pid)
            self._reload()
        except Exception as e:
            messagebox.showerror("Прайсы", f"Не удалось удалить:\n{e}")

    def _open_form(self, item=None):
        top = tk.Toplevel(self.master)
        top.title("Добавить прайс" if not item else "Редактировать прайс")
        # Make dialog behave modally and stay above the main window
        try:
            top.transient(self.master)
            top.grab_set()
            top.focus_set()
        except Exception:
            pass
        set_initial_geometry(top, 520, 180, center_to=self.master)
        frm = ttk.Frame(top, padding=16)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Название").grid(row=0, column=0, sticky="w")
        name_var = tk.StringVar(value=(item["name"] if item else ""))
        ttk.Entry(frm, textvariable=name_var).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(frm, text="Файл").grid(row=1, column=0, sticky="w", pady=(10, 0))
        path_var = tk.StringVar(value=(item["path"] if item else ""))
        row = ttk.Frame(frm)
        row.grid(row=1, column=1, sticky="ew", pady=(10, 0))
        row.columnconfigure(0, weight=1)
        ttk.Entry(row, textvariable=path_var).grid(row=0, column=0, sticky="ew")
        def _browse():
            p = filedialog.askopenfilename(
                parent=top,
                title="Выберите файл прайса",
                filetypes=[
                    ("Все файлы", "*.*"),
                    ("Excel", "*.xlsx;*.xls"),
                    ("Текст", "*.txt;*.csv"),
                    ("PDF", "*.pdf"),
                ]
            )
            # Bring the dialog back to front and focus it
            try:
                top.lift()
                top.focus_force()
            except Exception:
                pass
            if p:
                path_var.set(p)
        ttk.Button(row, text="Обзор…", command=_browse).grid(row=0, column=1, padx=(8, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(16, 0))
        def _ok():
            name = (name_var.get() or "").strip()
            path = (path_var.get() or "").strip()
            if not name or not path:
                messagebox.showerror("Прайсы", "Укажите название и файл.", parent=top)
                return
            try:
                if item:
                    self.db.update_price(item["id"], name, path)
                else:
                    self.db.add_price(name, path)
                try:
                    top.grab_release()
                except Exception:
                    pass
                top.destroy()
                self._reload()
            except Exception as e:
                messagebox.showerror("Прайсы", f"Не удалось сохранить:\n{e}", parent=top)
        ttk.Button(btns, text="Сохранить", command=_ok).pack(side="right")
        ttk.Button(btns, text="Отмена", command=lambda: (top.grab_release() if True else None) or top.destroy()).pack(side="right", padx=(8, 0))

    def _open_selected(self):
        pid = self._selected_id()
        if not pid:
            return
        try:
            all_items = self.db.list_prices()
            item = next((x for x in all_items if x["id"] == pid), None)
        except Exception:
            item = None
        if not item:
            return
        path = item.get("path") or ""
        if not path:
            return
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Прайсы", f"Не удалось открыть файл:\n{e}")

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()