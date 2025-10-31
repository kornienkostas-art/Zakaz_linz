import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.utils import fade_transition, center_on_screen
from app.db import AppDB  # type hint only


class MeridianOrdersView(ttk.Frame):
    """Встроенное представление 'Заказ Меридиан' внутри главного окна."""
    COLUMNS = ("title", "items_count", "status", "date")
    HEADERS = {
        "title": "Название заказа",
        "items_count": "Позиций",
        "status": "Статус",
        "date": "Дата",
    }
    STATUSES = ["Не заказан", "Заказан"]

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self.orders: list[dict] = []

        # Build UI with safe fallback to avoid blank screen
        failed = False
        last_error = None
        last_trace = ""
        try:
            self._build_toolbar()
            self._build_table()
        except Exception as e:
            failed = True
            last_error = e
            # Collect traceback and try to persist to a writable temp dir
            try:
                import traceback, tempfile, os
                last_trace = traceback.format_exc()
                log_path = os.path.join(tempfile.gettempdir(), "orders_meridian_error.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("Ошибка построения экрана 'Заказы Меридиан'\n")
                    f.write(str(e) + "\n\n")
                    f.write(last_trace)
            except Exception:
                log_path = "(не удалось записать лог в temp)"
            # Minimal fallback UI with inline error details (ttk)
            try:
                container = ttk.Frame(self, style="Card.TFrame", padding=16)
                container.pack(fill="both", expand=True)
                ttk.Button(container, text="← Назад", style="Accent.TButton", command=self._go_back).pack(anchor="w")
                try:
                    ttk.Separator(container).pack(fill="x", pady=(8, 12))
                except Exception:
                    pass
                ttk.Label(
                    container,
                    text="Не удалось отобразить список заказов. Ниже — подробности ошибки.",
                    style="Subtitle.TLabel",
                    justify="left"
                ).pack(anchor="w", pady=(4, 8))
                # Show traceback inline for quick copy
                try:
                    txt = tk.Text(container, height=10, wrap="none")
                    txt.pack(fill="both", expand=True)
                    txt.insert("1.0", f"{e}\n\n{last_trace}\nЛог: {log_path}")
                    txt.configure(state="disabled")
                except Exception:
                    ttk.Label(container, text=f"Ошибка: {e}\nЛог: {log_path}", justify="left").pack(anchor="w")
                try:
                    ttk.Separator(container).pack(fill="x", pady=(8, 12))
                except Exception:
                    pass
                ttk.Button(container, text="Новый заказ", style="Menu.TButton", command=self._new_order).pack(anchor="w")
            except Exception:
                pass

        # Absolute last resort: if nothing was packed (styles could be broken), render plain Tk fallback
        try:
            if failed and not self.winfo_children():
                self._render_plain_fallback(last_error, last_trace)
        except Exception:
            pass

    def _render_plain_fallback(self, error, trace_txt: str = ""):
        # Plain Tk widgets without ttk/styles to guarantee visibility
        f = tk.Frame(self, bg="#f8fafc")
        f.pack(fill="both", expand=True)
        tk.Button(f, text="← Назад", command=self._go_back).pack(anchor="w", padx=12, pady=8)
        tk.Label(f, text="Не удалось отобразить список заказов (plain fallback).", bg="#f8fafc").pack(anchor="w", padx=12)
        if error:
            try:
                t = tk.Text(f, height=12)
                t.pack(fill="both", expand=True, padx=12, pady=8)
                t.insert("1.0", f"{error}\n\n{trace_txt}")
                t.configure(state="disabled")
            except Exception:
                tk.Label(f, text=str(error), bg="#f8fafc").pack(anchor="w", padx=12, pady=8)
        tk.Button(f, text="Новый заказ", command=self._new_order).pack(anchor="w", padx=12, pady=(8, 12))

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")

        btn_back = ttk.Button(toolbar, text="← Главное меню", style="Accent.TButton", command=self._go_back)

        btn_new_order = ttk.Button(toolbar, text="Новый заказ", style="Menu.TButton", command=self._new_order)
        btn_edit_order = ttk.Button(toolbar, text="Редактировать", style="Menu.TButton", command=self._edit_order)
        btn_delete_order = ttk.Button(toolbar, text="Удалить", style="Menu.TButton", command=self._delete_order)
        btn_change_status = ttk.Button(toolbar, text="Сменить статус", style="Menu.TButton", command=self._change_status)
        btn_products = ttk.Button(toolbar, text="Товары", style="Menu.TButton", command=self._open_products)
        btn_export = ttk.Button(toolbar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt)

        btn_back.pack(side="left")
        btn_new_order.pack(side="left", padx=(8, 0))
        btn_edit_order.pack(side="left", padx=(8, 0))
        btn_delete_order.pack(side="left", padx=(8, 0))
        btn_change_status.pack(side="left", padx=(8, 0))
        btn_products.pack(side="left", padx=(8, 0))
        btn_export.pack(side="left", padx=(8, 0))

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

        header = ttk.Label(container, text="Заказ Меридиан • Список заказов", style="Title.TLabel")
        sub = ttk.Label(container, text="Каждый заказ может содержать несколько позиций товара", style="Subtitle.TLabel")
        header.pack(anchor="w")
        sub.pack(anchor="w", pady=(4, 12))
        ttk.Separator(container).pack(fill="x", pady=(8, 12))

        table_frame = ttk.Frame(container, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        columns = self.COLUMNS
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Data.Treeview")
        for col in columns:
            self.tree.heading(col, text=self.HEADERS[col], anchor="w")
            width = {"title": 360, "items_count": 100, "status": 140, "date": 160}[col]
            self.tree.column(col, width=width, anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree.tag_configure("status_Не заказан", background="#fee2e2", foreground="#7f1d1d")
        self.tree.tag_configure("status_Заказан", background="#fef3c7", foreground="#7c2d12")

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

        self._refresh_orders_view()

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
            ClientsView(self.master, getattr(self.master, "db", None), on_back=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
        fade_transition(self.master, swap)

    def _open_products(self):
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            from app.views.products_meridian import ProductsMeridianView
            from app.views.main import MainWindow
            ProductsMeridianView(self.master, getattr(self.master, "db", None), on_back=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master)))
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

    def _delete_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        order = self.orders[idx]
        order_id = order.get("id")
        if not order_id:
            messagebox.showinfo("Удалить", "Не удалось определить идентификатор заказа.")
            return
        if not messagebox.askyesno("Удалить", "Удалить выбранный заказ?"):
            return
        db = getattr(self.master, "db", None)
        if db:
            try:
                db.delete_meridian_order(order_id)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось удалить заказ:\n{e}")
                return
        self._refresh_orders_view()

    def _set_status(self, status: str):
        idx = self._selected_index()
        if idx is None:
            return
        order = self.orders[idx]
        order_id = order.get("id")
        old_status = order.get("status", "Не заказан")
        if status == old_status:
            return
        db = getattr(self.master, "db", None)
        if db and order_id:
            try:
                db.update_meridian_order(order_id, {"status": status, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось обновить статус заказа:\n{e}")
                return
        self._refresh_orders_view()

    

    def _new_order(self):
        def swap():
            from app.views.forms_meridian import MeridianOrderEditorView
            from app.views.main import MainWindow

            def on_save(order: dict):
                # Save to DB only; view will be recreated by on_back of editor
                db = getattr(self.master, "db", None)
                title = (order.get("title", "") or "").strip()
                if not title:
                    try:
                        existing = db.list_meridian_orders() if db else []
                        title = f"Заказ Меридиан #{len(existing) + 1}"
                    except Exception:
                        title = "Заказ Меридиан"
                    order["title"] = title
                if db:
                    try:
                        # Доверяем AppDB: позиции будут сохранены внутри add_meridian_order
                        db.add_meridian_order(order, order.get("items", []))
                    except Exception as e:
                        messagebox.showerror("База данных", f"Не удалось сохранить заказ Меридиан:\\n{e}")rder: dict):
                # Save to DB only; view will be recreated by on_back of editor
                db = getattr(self.master, "db", None)
                title = (order.get("title", "") or "").strip()
                if not title:
                    try:
                        existing = db.list_meridian_orders() if db else []
                        title = f"Заказ Меридиан #{len(existing) + 1}"
                    except Exception:
                        title = "Заказ Меридиан"
                    order["title"] = title
                if db:
                    try:
                        new_id = db.add_meridian_order(order, order.get("items", []))
                        # Перезапишем позиции, чтобы сохранить ADD
                        try:
                            db.conn.execute("DELETE FROM meridian_items WHERE order_id=?;", (new_id,))
                            for it in order.get("items", []):
                                db.conn.execute(
                                    'INSERT INTO meridian_items (order_id, product, sph, cyl, ax, "add", d, qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
                                    (
                                        new_id,
                                        it.get("product", ""),
                                        it.get("sph", ""),
                                        it.get("cyl", ""),
                                        it.get("ax", ""),
                                        it.get("add", ""),
                                        it.get("d", ""),
                                        it.get("qty", ""),
                                    ),
                                )
                            db.conn.commit()
                        except Exception:
                            # Если что-то пойдет не так — останутся позиции без ADD из стандартной вставки
                            pass
                    except Exception as e:
                        messagebox.showerror("База данных", f"Не удалось сохранить заказ Меридиан:\n{e}")

            # Чистим корень и создаём редактор заново, чтобы не оставалось пустых областей
            try:
                for w in list(self.master.winfo_children()):
                    try:
                        w.destroy()
                    except Exception:
                        pass
                # Гарантируем растяжение корня
                try:
                    self.master.columnconfigure(0, weight=1)
                    self.master.rowconfigure(0, weight=1)
                except Exception:
                    pass
                MeridianOrderEditorView(
                    self.master,
                    db=getattr(self.master, "db", None),
                    on_back=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master)),
                    on_save=on_save,
                    initial=None,
                )
            except Exception as e:
                # Показать минимальный экран вместо пустого, если редактор не построился
                try:
                    container = ttk.Frame(self.master, padding=16, style="Card.TFrame")
                    container.grid(row=0, column=0, sticky="nsew")
                    ttk.Button(container, text="← Назад", style="Accent.TButton",
                               command=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))).pack(anchor="w")
                    ttk.Separator(container).pack(fill="x", pady=(8, 12))
                    ttk.Label(container, text=f"Не удалось открыть редактор заказа:\n{e}",
                              style="Subtitle.TLabel", justify="left").pack(anchor="w", pady=(4, 12))
                except Exception:
                    pass
        fade_transition(self.master, swap)

    def _edit_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].copy()
        order_id = current.get("id")

        items = []
        if self.master.db and order_id:
            try:
                items = self.master.db.get_meridian_items(order_id)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить позиции заказа:\\n{e}")f self.master.db and order_id:
            try:
                # Локальная выборка, чтобы гарантировать чтение ADD
                rows = self.master.db.conn.execute(
                    'SELECT id, order_id, product, sph, cyl, ax, COALESCE("add","") AS add_value, d, qty FROM meridian_items WHERE order_id=? ORDER BY id ASC;',
                    (order_id,),
                ).fetchall()
                items = [
                    {
                        "id": r["id"],
                        "order_id": r["order_id"],
                        "product": r["product"],
                        "sph": r["sph"] or "",
                        "cyl": r["cyl"] or "",
                        "ax": r["ax"] or "",
                        "add": r["add_value"] or "",
                        "d": r["d"] or "",
                        "qty": r["qty"] or "",
                    }
                    for r in rows
                ]
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить позиции заказа:\n{e}")

        initial = {"status": current.get("status", "Не заказан"), "date": current.get("date", ""), "items": items}

        def swap():
            from app.views.forms_meridian import MeridianOrderEditorView
            from app.views.main import MainWindow

            def on_save(updated: dict):
                if self.master.db and order_id:
                    try:
                        self.master.db.update_meridian_order(order_id, {
                            "status": updated.get("status", current.get("status", "Не заказан")),
                            "date": updated.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
                        })
                        # Доверяем AppDB атомарно заменить позиции
                        self.master.db.replace_meridian_items(order_id, updated.get("items", []))
                    except Exception as e:
                        messagebox.showerror("База данных", f"Не удалось обновить заказ:\n{e}")

            # Полная очистка корня и создание редактора, чтобы не оставалось пустых областей
            try:
                for w in list(self.master.winfo_children()):
                    try:
                        w.destroy()
                    except Exception:
                        pass
                try:
                    self.master.columnconfigure(0, weight=1)
                    self.master.rowconfigure(0, weight=1)
                except Exception:
                    pass
                MeridianOrderEditorView(
                    self.master,
                    db=getattr(self.master, "db", None),
                    on_back=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master)),
                    on_save=on_save,
                    initial=initial,
                )
            except Exception as e:
                # Показать минимальный экран вместо пустого
                try:
                    container = ttk.Frame(self.master, padding=16, style="Card.TFrame")
                    container.grid(row=0, column=0, sticky="nsew")
                    ttk.Button(container, text="← Назад", style="Accent.TButton",
                               command=lambda: MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))).pack(anchor="w")
                    ttk.Separator(container).pack(fill="x", pady=(8, 12))
                    ttk.Label(container, text=f"Не удалось открыть редактор заказа:\n{e}",
                              style="Subtitle.TLabel", justify="left").pack(anchor="w", pady=(4, 12))
                except Exception:
                    pass

        fade_transition(self.master, swap)

    def _change_status(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].get("status", "Не заказан")

        dialog = tk.Toplevel(self)
        dialog.title("Сменить статус")
        dialog.configure(bg="#f8fafc")
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

        # Center the dialog on screen
        try:
            from app.utils import center_on_screen
            center_on_screen(dialog)
        except Exception:
            pass

    def _refresh_orders_view(self):
        db = getattr(self.master, "db", None)
        if db:
            try:
                self.orders = db.list_meridian_orders()
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить заказы Меридиан:\n{e}")
                self.orders = []
        else:
            self.orders = getattr(self, "orders", [])
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, o in enumerate(self.orders):
            items_count = 0
            if db and o.get("id") is not None:
                try:
                    cnt_rows = db.conn.execute("SELECT COUNT(1) AS c FROM meridian_items WHERE order_id=?;", (o["id"],)).fetchone()
                    items_count = int(cnt_rows["c"] or 0)
                except Exception:
                    items_count = 0
            values = (o.get("title", ""), items_count, o.get("status", ""), o.get("date", ""))
            tag = f"status_{o.get('status','Не заказан')}"
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))
        # Auto-select the latest order (first row; list is DESC by id)
        try:
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[0])
                self.tree.focus(children[0])
                self.tree.see(children[0])
        except Exception:
            pass

    def _export_txt(self):
        """Экспорт позиций из заказов 'Не заказан' с загрузкой items из БД, сгруппировано по товару."""
        db = getattr(self.master, "db", None)
        groups: dict[str, list[dict]] = {}
        for order in self.orders:
            if (order.get("status", "") or "").strip() != "Не заказан":
                continue
            order_id = order.get("id")
            items = []
            if db and order_id is not None:
                try:
                    items = db.get_meridian_items(order_id)
                except Exception:
                    items = []
            for it in items:
                key = (it.get("product", "") or "").strip() or "(Без названия)"
                groups.setdefault(key, []).append(it)

        if not groups:
            messagebox.showinfo("Экспорт", "Нет позиций со статусом 'Не заказан' для экспорта.")
            return

        lines: list[str] = []
        for product, items in groups.items():
            lines.append(product)
            for it in items:
                parts = []
                for key, label in (("sph", "Sph"), ("cyl", "Cyl"), ("ax", "Ax"), ("add", "ADD")):
                    val = (it.get(key, "") or "").strip()
                    if val != "":
                        parts.append(f"{label}: {val}")
                dval = (it.get("d", "") or "").strip()
                if dval != "":
                    parts.append(f"D:{dval}мм")
                qty = (it.get("qty", "") or "").strip()
                if qty != "":
                    parts.append(f"Количество: {qty}")
                if parts:
                    lines.append(" ".join(parts))
            lines.append("")

        content = "\n".join(lines).strip() + "\n"
        date_str = datetime.now().strftime("%d.%m.%y")
        filename = f"MERIDIAN_{date_str}.txt"
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