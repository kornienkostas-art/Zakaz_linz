import tkinter as tk
from tkinter import ttk, messagebox


class AppState:
    """Простое хранилище данных до подключения БД."""
    def __init__(self):
        self.clients = []  # [{'fio': str, 'phone': str}]
        self.products = []  # [{'name': str}]


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=24)
        self.master = master
        self.state = AppState()
        self._configure_root()
        self._setup_style()
        self._build_layout()

    # Window and grid configuration
    def _configure_root(self):
        self.master.title("УссурОЧки.рф")
        # Center window on screen
        width, height = 600, 380
        self.master.geometry(f"{width}x{height}")
        self.master.minsize(540, 340)
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f"+{x}+{y}")
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
        MKLOrdersWindow(self.master, self.state)

    def _on_order_meridian(self):
        messagebox.showinfo("Заказ Меридиан", "Раздел 'Заказ Меридиан' будет реализован позже.")

    def _on_settings(self):
        messagebox.showinfo("Настройки", "Раздел 'Настройки' будет реализован позже.")


class MKLOrdersWindow(tk.Toplevel):
    """Окно 'Заказ МКЛ' с таблицей данных и доступом к клиентам/товарам."""
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

    def __init__(self, master: tk.Tk, state: AppState):
        super().__init__(master)
        self.state = state
        self.title("Заказ МКЛ")
        self.configure(bg="#0f172a")
        self.geometry("1000x560")
        self.minsize(820, 460)
        # Center relative to parent
        self.update_idletasks()
        x = master.winfo_rootx() + 40
        y = master.winfo_rooty() + 40
        self.geometry(f"+{x}+{y}")

        # Close behavior
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Build UI
        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=12)
        toolbar.pack(fill="x")

        ttk.Label(toolbar, text="Заказ МКЛ", style="Title.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Управление клиентами и товарами", style="Subtitle.TLabel").pack(side="left", padx=(12, 0))

        # Buttons
        btn_clients = ttk.Button(toolbar, text="Клиенты", style="Menu.TButton", command=self._open_clients)
        btn_products = ttk.Button(toolbar, text="Товары", style="Menu.TButton", command=self._open_products)
        btn_add_record = ttk.Button(toolbar, text="Добавить запись", style="Menu.TButton", command=self._add_record_placeholder)

        btn_clients.pack(side="right", padx=(8, 0))
        btn_products.pack(side="right", padx=(8, 0))
        btn_add_record.pack(side="right", padx=(8, 0))

    def _build_table(self):
        container = ttk.Frame(self, style="Card.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        sub = ttk.Label(
            container,
            text="Поля: ФИО, Телефон, Товар, Sph, Cyl, Ax, Bc, Количество, Статус, Дата",
            style="Subtitle.TLabel",
        )
        sub.pack(anchor="w", pady=(0, 12))

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
                "phone": 120,
                "product": 160,
                "sph": 70,
                "cyl": 70,
                "ax": 70,
                "bc": 70,
                "qty": 100,
                "status": 120,
                "date": 120,
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
        ClientsWindow(self, self.state)

    def _open_products(self):
        ProductsWindow(self, self.state)

    def _add_record_placeholder(self):
        messagebox.showinfo("Добавить запись", "Форма добавления записи будет реализована на следующем шаге.")


class ClientsWindow(tk.Toplevel):
    """Список клиентов: поиск по ФИО/Телефону, добавить/редактировать/удалить."""
    COLUMNS = ("fio", "phone")
    HEADERS = {"fio": "ФИО", "phone": "Телефон"}

    def __init__(self, master: tk.Toplevel, state: AppState):
        super().__init__(master)
        self.state = state
        self.title("Клиенты")
        self.configure(bg="#0f172a")
        self.geometry("640x460")
        self.minsize(560, 400)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Position near parent
        self.update_idletasks()
        x = master.winfo_rootx() + 60
        y = master.winfo_rooty() + 60
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        # Search bar
        top = ttk.Frame(self, style="Card.TFrame", padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Поиск:", style="Subtitle.TLabel").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var)
        search_entry.pack(side="left", padx=(8, 8))
        self.search_var.trace_add("write", lambda *_: self._refresh_table())

        self.search_by = tk.StringVar(value="fio")
        by_cb = ttk.Combobox(top, textvariable=self.search_by, values=["fio", "phone"], width=10, state="readonly")
        by_cb.pack(side="left")
        by_cb.bind("<<ComboboxSelected>>", lambda *_: self._refresh_table())

        # Buttons
        btn_add = ttk.Button(top, text="Добавить", style="Menu.TButton", command=self._add_client)
        btn_edit = ttk.Button(top, text="Редактировать", style="Menu.TButton", command=self._edit_client)
        btn_delete = ttk.Button(top, text="Удалить", style="Menu.TButton", command=self._delete_client)
        btn_add.pack(side="right", padx=(8, 0))
        btn_edit.pack(side="right", padx=(8, 0))
        btn_delete.pack(side="right", padx=(8, 0))

        # Table
        table_frame = ttk.Frame(self, style="Card.TFrame", padding=12)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", style="Data.Treeview")
        for col in self.COLUMNS:
            self.tree.heading(col, text=self.HEADERS[col], anchor="w")
            self.tree.column(col, width=260 if col == "fio" else 140, anchor="w", stretch=True)
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

    def _refresh_table(self):
        query = (self.search_var.get() or "").strip().lower()
        by = self.search_by.get()
        # Clear
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Fill
        for idx, client in enumerate(self.state.clients):
            val = client.get(by, "")
            if query and query not in (val or "").lower():
                continue
            self.tree.insert("", "end", iid=str(idx), values=(client.get("fio", ""), client.get("phone", "")))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _add_client(self):
        ClientForm(self, self.state, on_save=lambda: self._refresh_table())

    def _edit_client(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning("Выбор", "Выберите клиента для редактирования.")
            return
        ClientForm(self, self.state, index=idx, on_save=lambda: self._refresh_table())

    def _delete_client(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning("Выбор", "Выберите клиента для удаления.")
            return
        client = self.state.clients[idx]
        if messagebox.askyesno("Удалить клиента", f"Удалить клиента: {client.get('fio', '')}?"):
            del self.state.clients[idx]
            self._refresh_table()


class ClientForm(tk.Toplevel):
    """Форма клиента: ФИО, Телефон."""
    def __init__(self, master: tk.Toplevel, state: AppState, index: int | None = None, on_save=None):
        super().__init__(master)
        self.state = state
        self.index = index
        self.on_save = on_save
        self.title("Клиент")
        self.configure(bg="#0f172a")
        self.geometry("420x220")
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        x = master.winfo_rootx() + 80
        y = master.winfo_rooty() + 80
        self.geometry(f"+{x}+{y}")

        container = ttk.Frame(self, style="Card.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="ФИО", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(container, text="Телефон", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.fio_var = tk.StringVar(value=(self.state.clients[index]["fio"] if index is not None else ""))
        self.phone_var = tk.StringVar(value=(self.state.clients[index]["phone"] if index is not None else ""))

        fio_entry = ttk.Entry(container, textvariable=self.fio_var)
        phone_entry = ttk.Entry(container, textvariable=self.phone_var)
        fio_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        phone_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        container.columnconfigure(1, weight=1)

        btns = ttk.Frame(container, style="Card.TFrame")
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right", padx=(8, 0))

    def _save(self):
        fio = self.fio_var.get().strip()
        phone = self.phone_var.get().strip()
        if not fio:
            messagebox.showwarning("Проверка", "Введите ФИО.")
            return
        data = {"fio": fio, "phone": phone}
        if self.index is None:
            self.state.clients.append(data)
        else:
            self.state.clients[self.index] = data
        if self.on_save:
            self.on_save()
        self.destroy()


class ProductsWindow(tk.Toplevel):
    """Список товаров: добавить/редактировать/удалить."""
    COLUMNS = ("name",)
    HEADERS = {"name": "Наименование"}

    def __init__(self, master: tk.Toplevel, state: AppState):
        super().__init__(master)
        self.state = state
        self.title("Товары")
        self.configure(bg="#0f172a")
        self.geometry("520x420")
        self.minsize(460, 360)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        x = master.winfo_rootx() + 60
        y = master.winfo_rooty() + 60
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        top = ttk.Frame(self, style="Card.TFrame", padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Список товаров", style="Subtitle.TLabel").pack(side="left")

        btn_add = ttk.Button(top, text="Добавить", style="Menu.TButton", command=self._add_product)
        btn_edit = ttk.Button(top, text="Редактировать", style="Menu.TButton", command=self._edit_product)
        btn_delete = ttk.Button(top, text="Удалить", style="Menu.TButton", command=self._delete_product)
        btn_add.pack(side="right", padx=(8, 0))
        btn_edit.pack(side="right", padx=(8, 0))
        btn_delete.pack(side="right", padx=(8, 0))

        table_frame = ttk.Frame(self, style="Card.TFrame", padding=12)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", style="Data.Treeview")
        for col in self.COLUMNS:
            self.tree.heading(col, text=self.HEADERS[col], anchor="w")
            self.tree.column(col, width=360, anchor="w", stretch=True)
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, product in enumerate(self.state.products):
            self.tree.insert("", "end", iid=str(idx), values=(product.get("name", ""),))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _add_product(self):
        ProductForm(self, self.state, on_save=self._refresh_table)

    def _edit_product(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning("Выбор", "Выберите товар для редактирования.")
            return
        ProductForm(self, self.state, index=idx, on_save=self._refresh_table)

    def _delete_product(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning("Выбор", "Выберите товар для удаления.")
            return
        product = self.state.products[idx]
        if messagebox.askyesno("Удалить товар", f"Удалить товар: {product.get('name', '')}?"):
            del self.state.products[idx]
            self._refresh_table()


class ProductForm(tk.Toplevel):
    """Форма товара: Наименование."""
    def __init__(self, master: tk.Toplevel, state: AppState, index: int | None = None, on_save=None):
        super().__init__(master)
        self.state = state
        self.index = index
        self.on_save = on_save
        self.title("Товар")
        self.configure(bg="#0f172a")
        self.geometry("420x180")
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        x = master.winfo_rootx() + 80
        y = master.winfo_rooty() + 80
        self.geometry(f"+{x}+{y}")

        container = ttk.Frame(self, style="Card.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Наименование", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")

        self.name_var = tk.StringVar(value=(self.state.products[index]["name"] if index is not None else ""))

        name_entry = ttk.Entry(container, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        container.columnconfigure(1, weight=1)

        btns = ttk.Frame(container, style="Card.TFrame")
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right", padx=(8, 0))

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Проверка", "Введите наименование товара.")
            return
        data = {"name": name}
        if self.index is None:
            self.state.products.append(data)
        else:
            self.state.products[self.index] = data
        if self.on_save:
            self.on_save()
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
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass

    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()