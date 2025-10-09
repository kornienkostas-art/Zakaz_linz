import tkinter as tk
from tkinter import ttk, messagebox


def set_initial_geometry(win: tk.Tk | tk.Toplevel, min_w: int, min_h: int, center_to: tk.Tk | None = None):
    """Adaptive window sizing: ensure minimum size and center on screen or relative to parent."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()

    # Target size: 70% of screen, but not less than min and not more than 90% of screen
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


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=24)
        self.master = master
        self._configure_root()
        self._setup_style()
        self._build_layout()

    # Window and grid configuration
    def _configure_root(self):
        self.master.title("УссурОЧки.рф")
        # Adaptive size so всё сразу видно без разворачивания
        set_initial_geometry(self.master, min_w=800, min_h=520)
        self.master.configure(bg="#f8fafc")  # light background

        # Make the frame fill the window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)

    # Modern, readable style
    def _setup_style(self):
        self.style = ttk.Style(self.master)

        # Use "clam" theme for better visuals cross-platform
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # Base colors (light theme)
        bg = "#f8fafc"            # light gray-50
        card_bg = "#ffffff"       # white card
        accent = "#3b82f6"        # blue accent
        text_primary = "#111827"  # near-black
        text_muted = "#6b7280"    # gray-500
        button_bg = "#e5e7eb"     # gray-200
        button_hover = "#d1d5db"  # gray-300
        border = "#e5e7eb"        # gray-200

        # Global settings
        self.style.configure(".", background=bg)
        self.style.configure("Card.TFrame", background=card_bg, borderwidth=1, relief="solid")
        self.style.map(
            "Card.TFrame",
            background=[("active", card_bg)]
        )

        # Title style
        self.style.configure(
            "Title.TLabel",
            background=card_bg,
            foreground=text_primary,
            font=("Segoe UI", 20, "bold")
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=card_bg,
            foreground=text_muted,
            font=("Segoe UI", 11)
        )

        # Button style
        self.style.configure(
            "Menu.TButton",
            background=button_bg,
            foreground=text_primary,
            font=("Segoe UI", 12, "bold"),
            padding=(16, 12),
            borderwidth=1
        )
        self.style.map(
            "Menu.TButton",
            background=[("active", button_hover)],
            relief=[("pressed", "sunken"), ("!pressed", "flat")],
            foreground=[("disabled", text_muted), ("!disabled", text_primary)]
        )

        # Separator
        self.style.configure("TSeparator", background=border)

        # Table (Treeview) style
        self.style.configure(
            "Data.Treeview",
            background=card_bg,
            fieldbackground=card_bg,
            foreground=text_primary,
            rowheight=28,
            bordercolor=border,
            borderwidth=1,
        )
        self.style.configure(
            "Data.Treeview.Heading",
            background="#f3f4f6",  # gray-100
            foreground=text_primary,
            font=("Segoe UI", 11, "bold"),
            bordercolor=border,
            borderwidth=1,
        )

        # Save some colors for drawing
        self._colors = {
            "bg": bg,
            "card_bg": card_bg,
            "accent": accent,
            "text_primary": text_primary,
            "text_muted": text_muted,
            "border": border,
        }

    def _build_layout(self):
        # Outer container (card)
        card = ttk.Frame(self, style="Card.TFrame", padding=24)
        card.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)

        # Header
        title = ttk.Label(card, text="УссурОЧки.рф", style="Title.TLabel")
        subtitle = ttk.Label(
            card,
            text="Главное меню • Выберите раздел",
            style="Subtitle.TLabel",
        )
        title.grid(row=0, column=0, sticky="w")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 12))

        ttk.Separator(card).grid(row=2, column=0, sticky="ew", pady=(8, 16))

        # Buttons container
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=3, column=0, sticky="nsew")
        buttons.columnconfigure(0, weight=1)

        # Buttons
        btn_mkl = ttk.Button(
            buttons, text="Заказ МКЛ", style="Menu.TButton", command=self._on_order_mkl
        )
        btn_meridian = ttk.Button(
            buttons, text="Заказ Меридиан", style="Menu.TButton", command=self._on_order_meridian
        )
        btn_settings = ttk.Button(
            buttons, text="Настройки", style="Menu.TButton", command=self._on_settings
        )

        # Layout buttons with spacing
        btn_mkl.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        btn_meridian.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        btn_settings.grid(row=2, column=0, sticky="ew")

        # Footer hint
        footer = ttk.Label(
            card,
            text="Локальная база данных будет добавлена позже. Начинаем с меню.",
            style="Subtitle.TLabel",
        )
        footer.grid(row=4, column=0, sticky="w", pady=(20, 0))

    # Actions
    def _on_order_mkl(self):
        # Переключаемся на представление заказов внутри главного окна
        self.destroy()
        MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master))

    def _on_order_meridian(self):
        messagebox.showinfo("Заказ Меридиан", "Раздел 'Заказ Меридиан' будет реализован позже.")

    def _on_settings(self):
        messagebox.showinfo("Настройки", "Раздел 'Настройки' будет реализован позже.")


class MKLOrdersView(ttk.Frame):
    """Встроенное представление 'Заказ МКЛ' внутри главного окна."""
    COLUMNS = (
        "fio", "phone", "product", "sph", "cyl", "ax", "bc", "qty", "status", "date"
    )
    HEADERS = {
        "fio": "ФИО клиента",
        "phone": "Телефон",
        "product": "Товар",
        "sph": "Sph",
        "cyl": "Cyl",
        "ax": "Ax",
        "bc": "Bc",
        "qty": "Количество",
        "status": "Статус",
        "date": "Дата",
    }
    STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back

        # Make the frame fill the window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # In-memory datasets (to be replaced with SQLite later)
        self.orders = []       # list of dicts
        self.clients = []      # list of dicts: {"fio":..., "phone":...}
        self.products = []     # list of dicts: {"name":...}

        # Build UI
        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")

        # Back to main menu
        btn_back = ttk.Button(toolbar, text="← Главное меню", style="Menu.TButton", command=self._go_back)

        # Order: Новый заказ, Редактировать, Удалить, Клиент, Добавить Товар
        btn_new_order = ttk.Button(toolbar, text="Новый заказ", style="Menu.TButton", command=self._new_order)
        btn_edit_order = ttk.Button(toolbar, text="Редактировать", style="Menu.TButton", command=self._edit_order)
        btn_delete_order = ttk.Button(toolbar, text="Удалить", style="Menu.TButton", command=self._delete_order)
        btn_clients = ttk.Button(toolbar, text="Клиент", style="Menu.TButton", command=self._open_clients)
        btn_products = ttk.Button(toolbar, text="Добавить Товар", style="Menu.TButton", command=self._open_products)

        btn_back.pack(side="left")
        btn_new_order.pack(side="left", padx=(8, 0))
        btn_edit_order.pack(side="left", padx=(8, 0))
        btn_delete_order.pack(side="left", padx=(8, 0))
        btn_clients.pack(side="left", padx=(8, 0))
        btn_products.pack(side="left", padx=(8, 0))

    def _build_table(self):
        container = ttk.Frame(self, style="Card.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        header = ttk.Label(container, text="Заказ МКЛ • Таблица данных", style="Title.TLabel")
        sub = ttk.Label(
            container,
            text="Поля: ФИО, Телефон, Товар, Sph, Cyl, Ax, Bc, Количество, Статус, Дата",
            style="Subtitle.TLabel",
        )
        header.pack(anchor="w")
        sub.pack(anchor="w", pady=(4, 12))

        ttk.Separator(container).pack(fill="x", pady=(8, 12))

        # Treeview with scrollbars
        table_frame = ttk.Frame(container, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        columns = self.COLUMNS
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Data.Treeview",
        )

        # Define headings and columns widths
        for col in columns:
            text = self.HEADERS[col]
            self.tree.heading(col, text=text, anchor="w")
            width = {
                "fio": 180,
                "phone": 140,
                "product": 180,
                "sph": 90,
                "cyl": 90,
                "ax": 90,
                "bc": 90,
                "qty": 120,
                "status": 140,
                "date": 140,
            }[col]
            self.tree.column(col, width=width, anchor="w", stretch=True)

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Tag styles for statuses (row highlighting)
        self._configure_status_tags()

        # Hint footer
        hint = ttk.Label(
            container,
            text="Создавайте новые заказы через кнопку 'Новый заказ'. БД подключим позже.",
            style="Subtitle.TLabel",
        )
        hint.pack(anchor="w", pady=(12, 0))

        # Context menu for status/edit/delete
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Редактировать", command=self._edit_order)
        self.menu.add_command(label="Удалить", command=self._delete_order)
        self.menu.add_separator()
        status_menu = tk.Menu(self.menu, tearoff=0)
        for s in self.STATUSES:
            status_menu.add_command(label=s, command=lambda st=s: self._set_status(st))
        self.menu.add_cascade(label="Статус", menu=status_menu)

        self.tree.bind("<Button-3>", self._show_context_menu)  # Right-click

    def _configure_status_tags(self):
        # Row highlighting by status (light theme)
        self.tree.tag_configure("status_Не заказан", background="#fee2e2", foreground="#7f1d1d")   # red-100 bg, red-900 text
        self.tree.tag_configure("status_Заказан", background="#fef3c7", foreground="#7c2d12")       # amber-100 bg, amber-900 text
        self.tree.tag_configure("status_Прозвонен", background="#dbeafe", foreground="#1e3a8a")     # blue-100 bg, blue-900 text
        self.tree.tag_configure("status_Вручен", background="#dcfce7", foreground="#065f46")        # green-100 bg, green-900 text

    def _show_context_menu(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.tree.selection_set(iid)
                self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _open_clients(self):
        ClientsWindow(self, self.clients)

    def _open_products(self):
        ProductsWindow(self, self.products)

    def _new_order(self):
        OrderForm(self, clients=self.clients, products=self.products, on_save=self._save_order)

    def _save_order(self, order: dict):
        # Добавляем заказ и обновляем таблицу
        self.orders.append(order)
        self._refresh_orders_view()

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите заказ.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _edit_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].copy()
        old_status = current.get("status", "Не заказан")

        def on_save(updated: dict):
            # Если статус изменился — обновить дату
            new_status = updated.get("status", old_status)
            if new_status != old_status:
                from datetime import datetime
                updated["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.orders[idx] = updated
            self._refresh_orders_view()

        OrderForm(self, clients=self.clients, products=self.products, on_save=on_save, initial=current, statuses=self.STATUSES)

    def _delete_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        if messagebox.askyesno("Удалить", "Удалить выбранный заказ?"):
            self.orders.pop(idx)
            self._refresh_orders_view()

    def _set_status(self, status: str):
        idx = self._selected_index()
        if idx is None:
            return
        old_status = self.orders[idx].get("status", "Не заказан")
        if status != old_status:
            from datetime import datetime
            self.orders[idx]["status"] = status
            self.orders[idx]["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._refresh_orders_view()

    def _refresh_orders_view(self):
        # Очистить и отрисовать из self.orders
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self.orders):
            values = (
                item.get("fio", ""),
                item.get("phone", ""),
                item.get("product", ""),
                item.get("sph", ""),
                item.get("cyl", ""),
                item.get("ax", ""),
                item.get("bc", ""),
                item.get("qty", ""),
                item.get("status", ""),
                item.get("date", ""),
            )
            tag = f"status_{item.get('status','Не заказан')}"
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))


class ClientsWindow(tk.Toplevel):
    """Список клиентов с поиском и CRUD."""
    def __init__(self, master: tk.Toplevel, clients: list[dict]):
        super().__init__(master)
        self.title("Клиенты")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Esc closes window
        self.bind("<Escape>", lambda e: self.destroy())
        self._dataset = clients  # reference to parent list
        self._filtered = list(self._dataset)  # working copy

        self._build_ui()

    def _build_ui(self):
        # Search bar
        search_card = ttk.Frame(self, style="Card.TFrame", padding=16)
        search_card.pack(fill="x")

        ttk.Label(search_card, text="Поиск по ФИО или телефону", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_card, textvariable=self.search_var, width=40)
        entry.grid(row=1, column=0, sticky="w")
        entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        # Buttons
        btns = ttk.Frame(search_card, style="Card.TFrame")
        btns.grid(row=1, column=1, sticky="w", padx=(12, 0))
        ttk.Button(btns, text="Добавить", style="Menu.TButton", command=self._add).pack(side="left")
        ttk.Button(btns, text="Редактировать", style="Menu.TButton", command=self._edit).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text="Удалить", style="Menu.TButton", command=self._delete).pack(side="left", padx=(8, 0))

        # Table
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

    def _apply_filter(self):
        term = self.search_var.get().strip().lower()
        if not term:
            self._filtered = list(self._dataset)
        else:
            self._filtered = [
                c for c in self._dataset
                if term in c.get("fio", "").lower() or term in c.get("phone", "").lower()
            ]
        self._refresh_view()

    def _refresh_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self._filtered):
            self.tree.insert("", "end", iid=str(idx), values=(item.get("fio", ""), item.get("phone", "")))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите запись.")
            return None
        return int(sel[0])

    def _add(self):
        ClientForm(self, on_save=self._on_add_save)

    def _on_add_save(self, data: dict):
        self._dataset.append(data)
        self._apply_filter()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        ClientForm(self, initial=item.copy(), on_save=lambda d: self._on_edit_save(idx, d))

    def _on_edit_save(self, filtered_idx: int, data: dict):
        # Map filtered index back to original dataset
        original_item = self._filtered[filtered_idx]
        orig_idx = self._dataset.index(original_item)
        self._dataset[orig_idx] = data
        self._apply_filter()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранного клиента?"):
            self._dataset.remove(item)
            self._apply_filter()


class ClientForm(tk.Toplevel):
    def __init__(self, master, initial: dict | None = None, on_save=None):
        super().__init__(master)
        self.title("Карточка клиента")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=480, min_h=280, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Esc closes form
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        self.vars = {
            "fio": tk.StringVar(value=(initial or {}).get("fio", "")),
            "phone": tk.StringVar(value=(initial or {}).get("phone", "")),
        }

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="ФИО", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.vars["fio"]).grid(row=1, column=0, sticky="ew")

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
        if self.on_save:
            self.on_save(data)
        self.destroy()


class ProductsWindow(tk.Toplevel):
    """Список товаров с CRUD."""
    def __init__(self, master: tk.Toplevel, products: list[dict]):
        super().__init__(master)
        self.title("Товары")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Esc closes window
        self.bind("<Escape>", lambda e: self.destroy())
        self._dataset = products
        self._filtered = list(self._dataset)

        self._build_ui()

    def _build_ui(self):
        # Toolbar
        bar = ttk.Frame(self, style="Card.TFrame", padding=16)
        bar.pack(fill="x")
        ttk.Button(bar, text="Добавить", style="Menu.TButton", command=self._add).pack(side="left")
        ttk.Button(bar, text="Редактировать", style="Menu.TButton", command=self._edit).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Удалить", style="Menu.TButton", command=self._delete).pack(side="left", padx=(8, 0))

        # Table
        table_card = ttk.Frame(self, style="Card.TFrame", padding=16)
        table_card.pack(fill="both", expand=True)

        columns = ("name",)
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", style="Data.Treeview")
        self.tree.heading("name", text="Название товара", anchor="w")
        self.tree.column("name", width=600, anchor="w")

        y_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        self._refresh_view()

    def _refresh_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self._filtered):
            self.tree.insert("", "end", iid=str(idx), values=(item.get("name", ""),))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите товар.")
            return None
        return int(sel[0])

    def _add(self):
        ProductForm(self, on_save=self._on_add_save)

    def _on_add_save(self, data: dict):
        self._dataset.append(data)
        self._filtered = list(self._dataset)
        self._refresh_view()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        ProductForm(self, initial=item.copy(), on_save=lambda d: self._on_edit_save(idx, d))

    def _on_edit_save(self, filtered_idx: int, data: dict):
        original_item = self._filtered[filtered_idx]
        orig_idx = self._dataset.index(original_item)
        self._dataset[orig_idx] = data
        self._filtered = list(self._dataset)
        self._refresh_view()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранный товар?"):
            self._dataset.remove(item)
            self._filtered = list(self._dataset)
            self._refresh_view()


class ProductForm(tk.Toplevel):
    def __init__(self, master, initial: dict | None = None, on_save=None):
        super().__init__(master)
        self.title("Карточка товара")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=480, min_h=240, center_to=master)
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


class OrderForm(tk.Toplevel):
    """Форма создания/редактирования заказа."""
    def __init__(
        self,
        master,
        clients: list[dict],
        products: list[dict],
        on_save=None,
        initial: dict | None = None,
        statuses: list[str] | None = None,
    ):
        super().__init__(master)
        self.title("Редактирование заказа" if initial else "Новый заказ")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=820, min_h=680, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.on_save = on_save
        self.clients = clients
        self.products = products
        self.statuses = statuses or ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

        # Vars
        self.client_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.sph_var = tk.StringVar(value="0")
        self.cyl_var = tk.StringVar(value="")
        self.ax_var = tk.StringVar(value="")
        self.bc_var = tk.StringVar(value="")
        self.qty_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))

        # Prefill from initial
        if initial:
            self.client_var.set(f'{initial.get("fio","")} — {initial.get("phone","")}'.strip(" —"))
            self.product_var.set(initial.get("product", ""))
            self.sph_var.set(initial.get("sph", "0"))
            self.cyl_var.set(initial.get("cyl", ""))
            self.ax_var.set(initial.get("ax", ""))
            self.bc_var.set(initial.get("bc", ""))
            try:
                self.qty_var.set(int(initial.get("qty", 1)))
            except Exception:
                self.qty_var.set(1)

        # UI
        self._build_ui()

        # Hotkeys: Esc closes form
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        # Client selection with autocomplete
        ttk.Label(card, text="Клиент (ФИО или телефон)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        self.client_combo = ttk.Combobox(card, textvariable=self.client_var, values=self._client_values(), height=10)
        self.client_combo.grid(row=1, column=0, sticky="ew")
        # Только фильтрация списка, без принудительного открытия
        self.client_combo.bind("<KeyRelease>", lambda e: self._filter_clients())

        # Product selection with autocomplete
        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w")
        self.product_combo = ttk.Combobox(card, textvariable=self.product_var, values=self._product_values(), height=10)
        self.product_combo.grid(row=1, column=1, sticky="ew")
        self.product_combo.bind("<KeyRelease>", lambda e: self._filter_products())

        ttk.Separator(card).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 12))

        # Characteristics
        # SPH
        sph_frame = ttk.Frame(card, style="Card.TFrame")
        sph_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(sph_frame, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").pack(anchor="w")
        self.sph_entry = ttk.Entry(sph_frame, textvariable=self.sph_var)
        self.sph_entry.pack(fill="x")

        # CYL
        cyl_frame = ttk.Frame(card, style="Card.TFrame")
        cyl_frame.grid(row=3, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(cyl_frame, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").pack(anchor="w")
        self.cyl_entry = ttk.Entry(cyl_frame, textvariable=self.cyl_var)
        self.cyl_entry.pack(fill="x")

        # AX
        ax_frame = ttk.Frame(card, style="Card.TFrame")
        ax_frame.grid(row=4, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        ttk.Label(ax_frame, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").pack(anchor="w")
        self.ax_entry = ttk.Entry(ax_frame, textvariable=self.ax_var)
        self.ax_entry.pack(fill="x")

        # BC
        bc_frame = ttk.Frame(card, style="Card.TFrame")
        bc_frame.grid(row=4, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        ttk.Label(bc_frame, text="BC (8.0…9.0, шаг 0.1)", style="Subtitle.TLabel").pack(anchor="w")
        self.bc_entry = ttk.Entry(bc_frame, textvariable=self.bc_var)
        self.bc_entry.pack(fill="x")

        # Bind clear shortcuts (Delete) for inputs
        for w in (self.client_combo, self.product_combo, self.sph_entry, self.cyl_entry, self.ax_entry, self.bc_entry):
            self._bind_clear_shortcuts(w)

        # QTY
        qty_frame = ttk.Frame(card, style="Card.TFrame")
        qty_frame.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
        ttk.Label(qty_frame, text="Количество (1…20)", style="Subtitle.TLabel").pack(anchor="w")
        self.qty_spin = ttk.Spinbox(qty_frame, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.pack(anchor="w")

        # Status
        status_frame = ttk.Frame(card, style="Card.TFrame")
        status_frame.grid(row=5, column=1, sticky="nsew", pady=(8, 0))
        ttk.Label(status_frame, text="Статус", style="Subtitle.TLabel").pack(anchor="w")
        self.status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, values=self.statuses, height=6)
        self.status_combo.pack(fill="x")

        # Footer and save
        footer = ttk.Label(card, text="Дата устанавливается автоматически при создании/смене статуса", style="Subtitle.TLabel")
        footer.grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=7, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    # Helpers: values for combo and filtering
    def _client_values(self):
        return [f'{c.get("fio","")} — {c.get("phone","")}' for c in self.clients]

    def _product_values(self):
        return [p.get("name", "") for p in self.products]

    def _filter_clients(self):
        term = self.client_var.get().strip().lower()
        values = self._client_values()
        if term:
            values = [v for v in values if term in v.lower()]
        # Update list without forcing dropdown open (avoids caret/Backspace issues)
        self.client_combo["values"] = values

    def _filter_products(self):
        term = self.product_var.get().strip().lower()
        values = self._product_values()
        if term:
            values = [v for v in values if term in v.lower()]
        # Update list without forcing dropdown open
        self.product_combo["values"] = values

    def _open_combo(self, combo: ttk.Combobox):
        # Open dropdown programmatically when focusing/clicking the field
        try:
            combo.event_generate("<Down>")
        except Exception:
            pass

    def _bind_clear_shortcuts(self, widget):
        # Delete clears the whole field
        def clear():
            try:
                widget.delete(0, "end")
            except Exception:
                try:
                    widget.set("")
                except Exception:
                    pass
        widget.bind("<Delete>", lambda e: clear())

    # Normalization and snapping (без подсказок)
    @staticmethod
    def _normalize_decimal(text: str) -> str:
        return (text or "").replace(",", ".").strip()

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        """Convert string to stepped value within range. Return '' if empty and allowed."""
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = 0.0 if min_v <= 0.0 <= max_v else min_v
        # Clamp
        v = max(min_v, min(max_v, v))
        # Snap to nearest step
        steps = round((v - min_v) / step)
        snapped = min_v + steps * step
        # Final clamp for floating rounding
        snapped = max(min_v, min(max_v, snapped))
        return f"{snapped:.2f}"

    @staticmethod
    def _snap_int(value_str: str, min_v: int, max_v: int, allow_empty: bool = False) -> str:
        text = (value_str or "").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = int(float(text.replace(",", ".")))
        except ValueError:
            v = min_v
        v = max(min_v, min(max_v, v))
        return str(v)

    def _parse_client(self, text: str) -> tuple[str, str]:
        """Return (fio, phone) from 'FIO — phone' or direct input."""
        t = (text or "").strip()
        if "—" in t:
            parts = t.split("—", 1)
            return parts[0].strip(), parts[1].strip()
        # Try find match from dataset
        term = t.lower()
        for c in self.clients:
            if term in c.get("fio", "").lower() or term in c.get("phone", "").lower():
                return c.get("fio", ""), c.get("phone", "")
        return t, ""

    def _parse_product(self, text: str) -> str:
        t = (text or "").strip()
        # Try exact match
        for p in self.products:
            if t.lower() == p.get("name", "").lower():
                return p.get("name", "")
        # Or first contains
        for p in self.products:
            if t.lower() in p.get("name", "").lower():
                return p.get("name", "")
        return t

    def _save(self):
        # Compose order dict with validation/snap
        fio, phone = self._parse_client(self.client_var.get())
        product = self._parse_product(self.product_var.get())

        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=False)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        bc = self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True)
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)
        status = (self.status_var.get() or "Не заказан").strip()

        if not fio:
            messagebox.showinfo("Проверка", "Выберите или введите клиента.")
            return
        if not product:
            messagebox.showinfo("Проверка", "Выберите или введите товар.")
            return

        from datetime import datetime
        order = {
            "fio": fio,
            "phone": phone,
            "product": product,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "bc": bc,
            "qty": qty,
            "status": status,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        if self.on_save:
            self.on_save(order)
        self.destroy()


def main():
    # High-DPI scaling for readability
    try:
        # On Windows, enable automatic scaling
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Tk scaling improves text/UI size on HiDPI
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()