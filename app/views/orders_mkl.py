import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from datetime import datetime

from app.utils import fade_transition, format_phone_mask, center_on_screen
from app.db import AppDB  # type hint only


class MKLOrdersView(ttk.Frame):
    """Встроенное представление 'Заказ МКЛ' внутри главного окна (DB-backed)."""
    COLUMNS = ("fio", "phone", "product", "sph", "cyl", "ax", "add", "bc", "qty", "status", "date", "comment_flag")
    HEADERS = {
        "fio": "ФИО",
        "phone": "Телефон",
        "product": "Товар",
        "sph": "Sph",
        "cyl": "Cyl",
        "ax": "Ax",
        "add": "ADD",
        "bc": "BC",
        "qty": "Количество",
        "status": "Статус",
        "date": "Дата",
        "comment_flag": "Комментарий",
    }
    STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back
        self.db: AppDB | None = getattr(self.master, "db", None)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        # Явно размещаем представление в (row=0, column=0), чтобы избежать «пустой» верхней области
        self.grid(row=0, column=0, sticky="nsew")

        self.orders: list[dict] = []

        self._build_toolbar()
        # Ensure tree attribute always exists even if UI build fails
        self.tree = None
        try:
            self._build_table()
        except Exception as e:
            # Fallback minimal table to avoid blank screen
            try:
                container = ttk.Frame(self, style="Card.TFrame", padding=16)
                container.pack(fill="both", expand=True)
                ttk.Label(container, text="Ошибка построения таблицы заказов МКЛ", style="Subtitle.TLabel").pack(anchor="w")
                ttk.Label(container, text=str(e), foreground="#7f1d1d").pack(anchor="w", pady=(4, 8))
                table_frame = ttk.Frame(container, style="Card.TFrame")
                table_frame.pack(fill="both", expand=True)
                self.tree = ttk.Treeview(table_frame, columns=("fio", "phone"), show="headings")
                self.tree.heading("fio", text="ФИО", anchor="w")
                self.tree.heading("phone", text="Телефон", anchor="w")
                self.tree.grid(row=0, column=0, sticky="nsew")
                table_frame.columnconfigure(0, weight=1)
                table_frame.rowconfigure(0, weight=1)
            except Exception:
                pass
        self._refresh_orders_view()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="← Главное меню", style="Back.TButton", command=self._go_back).pack(side="left")
        ttk.Button(toolbar, text="Новый заказ", style="Menu.TButton", command=self._new_order).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Редактировать", style="Menu.TButton", command=self._edit_order).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Удалить", style="Menu.TButton", command=self._delete_order).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Сменить статус", style="Menu.TButton", command=self._change_status).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Клиенты", style="Menu.TButton", command=self._open_clients).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Товары", style="Menu.TButton", command=self._open_products).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt).pack(side="left", padx=(8, 0))

    def _go_back(self):
        try:
            self.destroy()
        finally:
            cb = getattr(self, "on_back", None)
            if callable(cb):
                cb()

    def _build_table(self):
        container = ttk.Frame(self, style="Card.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        header = ttk.Label(container, text="Заказ МКЛ • Таблица данных", style="Title.TLabel")
        sub = ttk.Label(container, text="Поля: ФИО, Телефон, Товар, Sph, Cyl, Ax, ADD, BC, Количество, Статус, Дата, Комментарий", style="Subtitle.TLabel")
        header.pack(anchor="w")
        sub.pack(anchor="w", pady=(4, 12))

        ttk.Separator(container).pack(fill="x", pady=(8, 12))

        table_frame = ttk.Frame(container, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        columns = self.COLUMNS
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Data.Treeview")
        for col in columns:
            self.tree.heading(col, text=self.HEADERS[col], anchor="w")
            width = {
                "fio": 200, "phone": 160, "product": 200, "sph": 80, "cyl": 80,
                "ax": 80, "add": 80, "bc": 80, "qty": 100, "status": 140, "date": 160, "comment_flag": 140,
            }[col]
            self.tree.column(col, width=width, anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree.tag_configure("status_Не заказан", background="#fee2e2", foreground="#7f1d1d")
        self.tree.tag_configure("status_Заказан", background="#fef3c7", foreground="#7c2d12")
        self.tree.tag_configure("status_Прозвонен", background="#dbeafe", foreground="#1e3a8a")
        self.tree.tag_configure("status_Вручен", background="#dcfce7", foreground="#065f46")

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Редактировать", command=self._edit_order)
        self.menu.add_command(label="Удалить", command=self._delete_order)
        self.menu.add_separator()
        status_menu = tk.Menu(self.menu, tearoff=0)
        for s in self.STATUSES:
            status_menu.add_command(label=s, command=lambda st=s: self._set_status(st))
        self.menu.add_cascade(label="Статус", menu=status_menu)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self._edit_order())

    def _show_context_menu(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.tree.selection_set(iid)
                self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _open_clients(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            from app.views.clients import ClientsView
            from app.views.main import MainWindow
            ClientsView(self.master, self.db, on_back=lambda: MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
        fade_transition(self.master, swap)

    def _open_products(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            from app.views.products_mkl import ProductsMKLView
            from app.views.main import MainWindow
            ProductsMKLView(self.master, self.db, on_back=lambda: MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
        fade_transition(self.master, swap)

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите заказ.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _new_order(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            try:
                from app.views.forms_mkl import NewMKLOrderView
                from app.views.main import MainWindow
                def on_submit(client_payload: dict):
                    # Сохранить новый заказ в базу и вернуться к списку
                    try:
                        if self.db:
                            self.db.add_mkl_order(client_payload)
                    except Exception as e:
                        try:
                            messagebox.showerror("База данных", f"Не удалось добавить заказ МКЛ:\\n{e}")
                        except Exception:
                            pass
                    MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master))
                NewMKLOrderView(
                    self.master,
                    db=self.db,
                    on_back=lambda: MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master)),
                    on_submit=on_submit
                )
            except Exception as e:
                # Покажем ошибку и восстановим список заказов
                try:
                    messagebox.showerror("Новый заказ", f"Ошибка открытия формы:\n{e}")
                except Exception:
                    pass
                from app.views.main import MainWindow
                MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master))
        try:
            from app.utils import fade_transition
            fade_transition(self.master, swap)
        except Exception:
            # Если плавный переход не удался, просто переключим
            swap()

    def _edit_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].copy()
        order_id = current.get("id")

        clients = self.db.list_clients() if self.db else []
        products = self.db.list_products_mkl() if self.db else []

        def on_save(updated: dict):
            new_status = updated.get("status", current.get("status", "Не заказан"))
            if new_status != current.get("status", "Не заказан"):
                updated["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if self.db and order_id:
                try:
                    self.db.update_mkl_order(order_id, updated)
                except Exception as e:
                    messagebox.showerror("База данных", f"Не удалось обновить заказ МКЛ:\n{e}")
            self._refresh_orders_view()

        from app.views.forms_mkl import OrderForm
        OrderForm(self, clients=clients, products=products, on_save=on_save, initial=current, statuses=self.STATUSES, db=self.db)

    def _delete_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        if not messagebox.askyesno("Удалить", "Удалить выбранный заказ?"):
            return
        order = self.orders[idx]
        order_id = order.get("id")
        if self.db and order_id:
            try:
                self.db.delete_mkl_order(order_id)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось удалить заказ МКЛ:\n{e}")
        self._refresh_orders_view()

    def _set_status(self, status: str):
        idx = self._selected_index()
        if idx is None:
            return
        order = self.orders[idx]
        order_id = order.get("id")
        old_status = order.get("status", "Не заказан")
        if status != old_status:
            if self.db and order_id:
                try:
                    self.db.update_mkl_order(order_id, {"status": status, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
                except Exception as e:
                    messagebox.showerror("База данных", f"Не удалось обновить статус заказа:\n{e}")
            self._refresh_orders_view()

    def _change_status(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].get("status", "Не заказан")

        dialog = tk.Toplevel(self)
        dialog.title("Сменить статус")
        dialog.configure(bg="#f8fafc")
        # Центрировать диалог относительно экрана
        try:
            center_on_screen(dialog)
        except Exception:
            pass
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Выберите статус", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        var = tk.StringVar(value=current)
        combo = ttk.Combobox(dialog, textvariable=var, values=self.STATUSES, height=6)
        combo.grid(row=1, column=0, sticky="ew", padx=12)
        ttk.Separator(dialog).grid(row=2, column=0, sticky="ew", padx=12, pady=(12, 12))

        btns = ttk.Frame(dialog, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="e", padx=12, pady=(0, 12))
        ttk.Button(btns, text="ОК", style="Menu.TButton", command=lambda: (self._set_status(var.get()), dialog.destroy())).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=dialog.destroy).pack(side="right", padx=(8, 0))

        dialog.columnconfigure(0, weight=1)

    def _export_txt(self):
        groups: dict[str, list[dict]] = {}
        for o in self.orders:
            if (o.get("status", "") or "").strip() == "Не заказан":
                key = (o.get("product", "") or "").strip() or "(Без названия)"
                groups.setdefault(key, []).append(o)

        if not groups:
            messagebox.showinfo("Экспорт", "Нет заказов со статусом 'Не заказан' для экспорта.")
            return

        lines: list[str] = []
        for product, items in groups.items():
            lines.append(product)
            for o in items:
                parts = []
                # Add parameters if present
                for key, label in (("sph", "Sph"), ("cyl", "Cyl"), ("ax", "Ax"), ("add", "ADD"), ("bc", "BC")):
                    val = (o.get(key, "") or "").strip()
                    if val != "":
                        parts.append(f"{label}: {val}")
                # Quantity if present
                qty = (o.get("qty", "") or "").strip()
                if qty != "":
                    parts.append(f"Количество: {qty}")
                # Comment should be to the right of quantity on the same line
                comment = (o.get("comment", "") or "").strip()
                if comment:
                    parts.append(f"Комментарий: {comment}")
                # Combine in one line if any
                if parts:
                    lines.append(" ".join(parts))
            lines.append("")

        content = "\n".join(lines).strip() + "\n"
        date_str = datetime.now().strftime("%d.%m.%y")
        filename = f"MKL_{date_str}.txt"
        export_path = getattr(self.master, "app_settings", {}).get("export_path", None)
        if not export_path:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            export_path = desktop if os.path.isdir(desktop) else os.getcwd()
        filepath = os.path.join(export_path, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Экспорт", f"Экспорт выполнен:\n{filepath}")
            try:
                import platform, subprocess
                if hasattr(os, "startfile"):
                    os.startfile(filepath)
                else:
                    sysname = platform.system()
                    if sysname == "Darwin":
                        subprocess.run(["open", filepath], check=False)
                    else:
                        subprocess.run(["xdg-open", filepath], check=False)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Экспорт", f"Ошибка записи файла:\n{e}")

    def _autosize_columns(self):
        """Resize columns to fit content and headers."""
        if not self.tree:
            return
        try:
            fnt = tkfont.nametofont("TkDefaultFont")
        except Exception:
            fnt = None
        pad = 24
        min_widths = {
            "fio": 120, "phone": 120, "product": 140, "sph": 60, "cyl": 60,
            "ax": 60, "add": 60, "bc": 60, "qty": 80, "status": 100, "date": 120, "comment_flag": 120
        }
        for col in self.COLUMNS:
            header = self.HEADERS[col]
            if fnt:
                maxw = fnt.measure(header)
            else:
                maxw = len(header) * 7
            for iid in self.tree.get_children(""):
                text = str(self.tree.set(iid, col))
                w = fnt.measure(text) if fnt else len(text) * 7
                if w > maxw:
                    maxw = w
            width = max(min_widths.get(col, 60), maxw + pad)
            self.tree.column(col, width=width)

    def _refresh_orders_view(self):
        """Reload orders from DB and render the table."""
        self.orders = []
        if self.db:
            try:
                self.orders = self.db.list_mkl_orders()
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить заказы МКЛ:\n{e}")
                self.orders = []
        # Clear and render
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self.orders):
            masked_phone = format_phone_mask(item.get("phone", ""))
            comment_flag = "ЕСТЬ" if (item.get("comment", "") or "").strip() else "НЕТ"
            values = (
                item.get("fio", ""),
                masked_phone,
                item.get("product", ""),
                item.get("sph", ""),
                item.get("cyl", ""),
                item.get("ax", ""),
                item.get("add", ""),
                item.get("bc", ""),
                item.get("qty", ""),
                item.get("status", ""),
                item.get("date", ""),
                comment_flag,
            )
            tag = f"status_{item.get('status','Не заказан')}"
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))
        # Auto-select the latest (first row since orders are DESC by id)
        try:
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[0])
                self.tree.focus(children[0])
                self.tree.see(children[0])
        except Exception:
            pass
        # Autosize columns after data is loaded
        try:
            self._autosize_columns()
        except Exception:
            pass