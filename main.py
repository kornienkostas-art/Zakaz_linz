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
        self.master.configure(bg="#0f172a")  # slate-900

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

        # Base colors
        bg = "#0f172a"        # deep slate
        card_bg = "#111827"   # slightly lighter slate
        accent = "#22c55e"    # emerald
        text_primary = "#e5e7eb"  # light gray
        text_muted = "#9ca3af"    # muted gray
        button_bg = "#1f2937"     # dark gray
        button_hover = "#374151"  # hover
        border = "#334155"

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
            background=button_bg,
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
        MKLOrdersWindow(self.master)

    def _on_order_meridian(self):
        messagebox.showinfo("Заказ Меридиан", "Раздел 'Заказ Меридиан' будет реализован позже.")

    def _on_settings(self):
        messagebox.showinfo("Настройки", "Раздел 'Настройки' будет реализован позже.")


class MKLOrdersWindow(tk.Toplevel):
    """Окно 'Заказ МКЛ' с таблицей данных."""
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

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title("Заказ МКЛ")
        self.configure(bg="#0f172a")
        set_initial_geometry(self, min_w=1000, min_h=640, center_to=master)

        # Close behavior
        self.transient(master)
        self.grab_set()  # modal-like
        self.protocol("WM_DELETE_WINDOW", self.destroy)

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

        btn_clients = ttk.Button(toolbar, text="Клиент", style="Menu.TButton", command=self._open_clients)
        btn_products = ttk.Button(toolbar, text="Добавить Товар", style="Menu.TButton", command=self._open_products)

        btn_clients.pack(side="left")
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

        # Hint footer
        hint = ttk.Label(
            container,
            text="Данные пока пустые. Добавление/редактирование и локальная БД (SQLite) подключим на следующих шагах.",
            style="Subtitle.TLabel",
        )
        hint.pack(anchor="w", pady=(12, 0))

    def _open_clients(self):
        ClientsWindow(self, self.clients)

    def _open_products(self):
        ProductsWindow(self, self.products)


class ClientsWindow(tk.Toplevel):
    """Список клиентов с поиском и CRUD."""
    def __init__(self, master: tk.Toplevel, clients: list[dict]):
        super().__init__(master)
        self.title("Клиенты")
        self.configure(bg="#0f172a")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
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
        self.configure(bg="#0f172a")
        set_initial_geometry(self, min_w=480, min_h=280, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

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
        self.configure(bg="#0f172a")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
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
        self.configure(bg="#0f172a")
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
    main():
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
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()