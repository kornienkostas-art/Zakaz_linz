import atexit
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from db import AppDB

SETTINGS_FILE = "settings.json"
DB_FILE = "data.db"


def ensure_settings(path: str):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 1}, f, ensure_ascii=False, indent=2)


def set_initial_geometry(win: tk.Tk | tk.Toplevel, min_w: int, min_h: int, center_to: tk.Tk | None = None):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    tw = max(min_w, int(sw * 0.7))
    th = max(min_h, int(sh * 0.7))
    tw = min(tw, int(sw * 0.9))
    th = min(th, int(sh * 0.9))
    win.geometry(f"{tw}x{th}")
    win.minsize(min_w, min_h)
    if center_to:
        x = center_to.winfo_rootx() + (center_to.winfo_width() // 2) - (tw // 2)
        y = center_to.winfo_rooty() + (center_to.winfo_height() // 2) - (th // 2)
    else:
        x = (sw // 2) - (tw // 2)
        y = (sh // 2) - (th // 2)
    win.geometry(f"+{x}+{y}")


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("УссурОЧки.рф — Заказ линз")
        set_initial_geometry(self.root, min_w=900, min_h=600)

        if not hasattr(self.root, "db") or not isinstance(self.root.db, AppDB):
            self.root.db = AppDB(DB_FILE)

        self._build_ui()
        self._refresh_stats()

    def _build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(side="top", fill="x", padx=12, pady=8)

        self.clients_count_var = tk.StringVar(value="Клиенты: 0")
        self.products_count_var = tk.StringVar(value="Товары: 0")
        self.mkl_count_var = tk.StringVar(value="MKL-заказы: 0")
        self.meridian_count_var = tk.StringVar(value="Meridian-заказы: 0")

        for var in (
            self.clients_count_var,
            self.products_count_var,
            self.mkl_count_var,
            self.meridian_count_var,
        ):
            ttk.Label(top, textvariable=var).pack(side="left", padx=8)

        ttk.Button(top, text="Обновить", command=self._refresh_stats).pack(side="right")

        tabs = ttk.Notebook(container)
        tabs.pack(fill="both", expand=True, padx=12, pady=8)

        tab_clients = ttk.Frame(tabs)
        tabs.add(tab_clients, text="Клиенты")

        form = ttk.Frame(tab_clients)
        form.pack(side="top", fill="x", padx=12, pady=12)

        ttk.Label(form, text="ФИО:").grid(row=0, column=0, sticky="w")
        self.fio_entry = ttk.Entry(form, width=40)
        self.fio_entry.grid(row=0, column=1, sticky="we", padx=8)

        ttk.Label(form, text="Телефон:").grid(row=1, column=0, sticky="w")
        self.phone_entry = ttk.Entry(form, width=20)
        self.phone_entry.grid(row=1, column=1, sticky="we", padx=8)

        ttk.Button(form, text="Добавить клиента", command=self._add_client).grid(
            row=0, column=2, rowspan=2, padx=8
        )

        form.columnconfigure(1, weight=1)

        list_frame = ttk.Frame(tab_clients)
        list_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.clients_list = tk.Listbox(list_frame)
        self.clients_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.clients_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.clients_list.configure(yscrollcommand=scrollbar.set)

        tab_products = ttk.Frame(tabs)
        tabs.add(tab_products, text="Товары")

        prod_top = ttk.Frame(tab_products)
        prod_top.pack(side="top", fill="x", padx=12, pady=12)
        ttk.Label(prod_top, text="Наименование:").pack(side="left")
        self.product_entry = ttk.Entry(prod_top, width=40)
        self.product_entry.pack(side="left", padx=8)
        ttk.Button(prod_top, text="Добавить товар", command=self._add_product).pack(side="left")

        self.products_list = tk.Listbox(tab_products)
        self.products_list.pack(fill="both", expand=True, padx=12, pady=8)

    def _refresh_stats(self):
        db = self.root.db
        clients = db.list_clients()
        products = db.list_products()
        mkl = db.list_mkl_orders()
        mer = db.list_meridian_orders()

        self.clients_count_var.set(f"Клиенты: {len(clients)}")
        self.products_count_var.set(f"Товары: {len(products)}")
        self.mkl_count_var.set(f"MKL-заказы: {len(mkl)}")
        self.meridian_count_var.set(f"Meridian-заказы: {len(mer)}")

        self.clients_list.delete(0, "end")
        for c in clients:
            self.clients_list.insert("end", f"{c['fio']} | {c['phone']}")

        self.products_list.delete(0, "end")
        for p in products:
            self.products_list.insert("end", p["name"])

    def _add_client(self):
        fio = self.fio_entry.get().strip()
        phone = self.phone_entry.get().strip()
        if not fio:
            messagebox.showwarning("Пустое ФИО", "Введите ФИО клиента")
            return
        self.root.db.add_client(fio, phone)
        self.fio_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self._refresh_stats()

    def _add_product(self):
        name = self.product_entry.get().strip()
        if not name:
            messagebox.showwarning("Пустое имя", "Введите наименование товара")
            return
        self.root.db.add_product(name)
        self.product_entry.delete(0, "end")
        self._refresh_stats()


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass

    try:
        root.state("zoomed")
    except tk.TclError:
        try:
            root.attributes("-zoomed", True)
        except tk.TclError:
            try:
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                root.geometry(f"{sw}x{sh}+0+0")
            except Exception:
                pass

    ensure_settings(SETTINGS_FILE)
    root.db = AppDB(DB_FILE)

    def _close_db():
        db = getattr(root, "db", None)
        if db:
            try:
                db.conn.close()
            except Exception:
                pass

    atexit.register(_close_db)

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()