import tkinter as tk
from tkinter import ttk, messagebox

# --- SQLite persistence layer (simple repositories) ---
import sqlite3
import os
from datetime import datetime
import re


class AppDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable foreign keys
        try:
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        # Clients
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                phone TEXT NOT NULL
            );
            """
        )
        # Products
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # MKL orders (flat structure for now)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mkl_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                phone TEXT NOT NULL,
                product TEXT NOT NULL,
                sph TEXT,
                cyl TEXT,
                ax TEXT,
                bc TEXT,
                qty TEXT,
                status TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        # Meridian orders (header) + items
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meridian_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meridian_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                sph TEXT,
                cyl TEXT,
                ax TEXT,
                d TEXT,
                qty TEXT,
                FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    # --- Clients ---
    def list_clients(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, fio, phone FROM clients ORDER BY fio COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "fio": r["fio"], "phone": r["phone"]} for r in rows]

    def add_client(self, fio: str, phone: str) -> int:
        cur = self.conn.execute("INSERT INTO clients (fio, phone) VALUES (?, ?);", (fio, phone))
        self.conn.commit()
        return cur.lastrowid

    def update_client(self, client_id: int, fio: str, phone: str):
        self.conn.execute("UPDATE clients SET fio=?, phone=? WHERE id=?;", (fio, phone, client_id))
        self.conn.commit()

    def delete_client(self, client_id: int):
        self.conn.execute("DELETE FROM clients WHERE id=?;", (client_id,))
        self.conn.commit()

    # --- Products ---
    def list_products(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name FROM products ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def add_product(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO products (name) VALUES (?);", (name,))
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id: int, name: str):
        self.conn.execute("UPDATE products SET name=? WHERE id=?;", (name, product_id))
        self.conn.commit()

    def delete_product(self, product_id: int):
        self.conn.execute("DELETE FROM products WHERE id=?;", (product_id,))
        self.conn.commit()

    # --- MKL Orders ---
    def list_mkl_orders(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, fio, phone, product, sph, cyl, ax, bc, qty, status, date FROM mkl_orders ORDER BY id DESC;"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "fio": r["fio"],
                "phone": r["phone"],
                "product": r["product"],
                "sph": r["sph"] or "",
                "cyl": r["cyl"] or "",
                "ax": r["ax"] or "",
                "bc": r["bc"] or "",
                "qty": r["qty"] or "",
                "status": r["status"],
                "date": r["date"],
            }
            for r in rows
        ]

    def add_mkl_order(self, order: dict) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO mkl_orders (fio, phone, product, sph, cyl, ax, bc, qty, status, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                order.get("fio", ""),
                order.get("phone", ""),
                order.get("product", ""),
                order.get("sph", ""),
                order.get("cyl", ""),
                order.get("ax", ""),
                order.get("bc", ""),
                order.get("qty", ""),
                order.get("status", "Не заказан"),
                order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_mkl_order(self, order_id: int, fields: dict):
        # Only update provided fields
        cols = []
        vals = []
        for k in ("fio", "phone", "product", "sph", "cyl", "ax", "bc", "qty", "status", "date"):
            if k in fields:
                cols.append(f"{k}=?")
                vals.append(fields[k])
        if cols:
            vals.append(order_id)
            self.conn.execute(f"UPDATE mkl_orders SET {', '.join(cols)} WHERE id=?;", tuple(vals))
            self.conn.commit()

    def delete_mkl_order(self, order_id: int):
        self.conn.execute("DELETE FROM mkl_orders WHERE id=?;", (order_id,))
        self.conn.commit()

    # --- Meridian Orders + Items ---
    def list_meridian_orders(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, status, date FROM meridian_orders ORDER BY id DESC;"
        ).fetchall()
        return [{"id": r["id"], "title": r["title"], "status": r["status"], "date": r["date"]} for r in rows]

    def get_meridian_items(self, order_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, order_id, product, sph, cyl, ax, d, qty FROM meridian_items WHERE order_id=? ORDER BY id ASC;",
            (order_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "order_id": r["order_id"],
                "product": r["product"],
                "sph": r["sph"] or "",
                "cyl": r["cyl"] or "",
                "ax": r["ax"] or "",
                "d": r["d"] or "",
                "qty": r["qty"] or "",
            }
            for r in rows
        ]

    def add_meridian_order(self, order: dict, items: list[dict]) -> int:
        cur = self.conn.execute(
            "INSERT INTO meridian_orders (title, status, date) VALUES (?, ?, ?);",
            (order.get("title", ""), order.get("status", "Не заказан"), order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))),
        )
        order_id = cur.lastrowid
        for it in items:
            self.conn.execute(
                """
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("d", ""),
                    it.get("qty", ""),
                ),
            )
        self.conn.commit()
        return order_id

    def update_meridian_order(self, order_id: int, fields: dict):
        cols = []
        vals = []
        for k in ("title", "status", "date"):
            if k in fields:
                cols.append(f"{k}=?")
                vals.append(fields[k])
        if cols:
            vals.append(order_id)
            self.conn.execute(f"UPDATE meridian_orders SET {', '.join(cols)} WHERE id=?;", tuple(vals))
            self.conn.commit()

    def replace_meridian_items(self, order_id: int, items: list[dict]):
        # Replace items for order
        self.conn.execute("DELETE FROM meridian_items WHERE order_id=?;", (order_id,))
        for it in items:
            self.conn.execute(
                """
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("d", ""),
                    it.get("qty", ""),
                ),
            )
        self.conn.commit()

    def delete_meridian_order(self, order_id: int):
        # Items will be cascaded
        self.conn.execute("DELETE FROM meridian_orders WHERE id=?;", (order_id,))
        self.conn.commit()


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


def fade_transition(root: tk.Tk, swap_callback, duration_ms: int = 120, steps: int = 8):
    """Simple fade-out, swap view, fade-in on the root window."""
    try:
        # Fade out
        for i in range(steps):
            alpha = 1.0 - (i + 1) / steps
            root.attributes("-alpha", max(0.0, alpha))
            root.update_idletasks()
            root.after(int(duration_ms / steps))
        # Swap content
        swap_callback()
        root.update_idletasks()
        # Fade in
        for i in range(steps):
            alpha = (i + 1) / steps
            root.attributes("-alpha", min(1.0, alpha))
            root.update_idletasks()
            root.after(int(duration_ms / steps))
        root.attributes("-alpha", 1.0)
    except tk.TclError:
        # If alpha not supported, just swap
        swap_callback()


def format_phone_mask(raw: str) -> str:
    """Format phone to '+7-XXX-XXX-XX-XX' or '8-XXX-XXX-XX-XX' for display, accepting various inputs."""
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return (raw or "").strip()

    prefix = ""
    tail = ""

    if len(digits) >= 11:
        # Take first digit as prefix if it's 7 or 8
        if digits[0] == "7":
            prefix = "+7"
            tail = digits[1:11]
        elif digits[0] == "8":
            prefix = "8"
            tail = digits[1:11]
        else:
            # Unknown leading, fallback to use last 10 with default '8'
            prefix = "8"
            tail = digits[-10:]
    elif len(digits) == 10:
        # Local format, default to '8'
        prefix = "8"
        tail = digits
    else:
        # Not enough digits to format, return original trimmed
        return (raw or "").strip()

    return f"{prefix}-{tail[0:3]}-{tail[3:6]}-{tail[6:8]}-{tail[8:10]}"


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

        # Init app settings with default export path (Desktop if exists)
        try:
            import os
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            default_export = desktop if os.path.isdir(desktop) else os.getcwd()
        except Exception:
            default_export = None
        if not hasattr(self.master, "app_settings"):
            self.master.app_settings = {"export_path": default_export}
        else:
            # Ensure key exists
            self.master.app_settings.setdefault("export_path", default_export)

        # Init SQLite DB once and attach to root
        try:
            db_file = os.path.join(os.getcwd(), "data.db")
            self.master.db = AppDB(db_file)
        except Exception as e:
            messagebox.showerror("База данных", f"Ошибка инициализации БД:\n{e}")
            # Fallback in-memory stub
            self.master.db = None

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

        # Accent button style (for primary actions like Back)
        accent_hover = "#2563eb"  # darker blue
        self.style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            font=("Segoe UI", 12, "bold"),
            padding=(16, 12),
            borderwidth=1
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", accent_hover)],
            foreground=[("disabled", "#ffffff"), ("!disabled", "#ffffff")]
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
        # Плавный переход на представление заказов внутри главного окна
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            MKLOrdersView(self.master, on_back=lambda: MainWindow(self.master))
        fade_transition(self.master, swap)

    def _on_order_meridian(self):
        # Плавный переход на заказы 'Меридиан'
        def swap():
            try:
                self.destroy()
            except Exception:
                pass
            MeridianOrdersView(self.master, on_back=lambda: MainWindow(self.master))
        fade_transition(self.master, swap)

    def _on_settings(self):
        SettingsWindow(self.master)


class SettingsWindow(tk.Toplevel):
    """Настройки приложения: путь сохранения экспорта по умолчанию."""
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.title("Настройки")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=560, min_h=240, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        # Read current settings from root
        self.app_settings = getattr(master, "app_settings", {"export_path": None})
        current_path = self.app_settings.get("export_path") or ""

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Путь сохранения экспорта (по умолчанию)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", columnspan=3)
        self.path_var = tk.StringVar(value=current_path)
        ttk.Label(card, text="Папка:", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        entry = ttk.Entry(card, textvariable=self.path_var)
        entry.grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(card, text="Обзор…", style="Menu.TButton", command=self._browse_dir).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Separator(card).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=3, column=0, columnspan=3, sticky="e")
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    def _browse_dir(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Выберите папку для сохранения экспорта")
        if path:
            self.path_var.set(path)

    def _save(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showinfo("Настройки", "Укажите папку для сохранения.")
            return
        try:
            import os
            if not os.path.isdir(path):
                messagebox.showinfo("Настройки", "Указанный путь не существует.")
                return
            # Persist in root settings
            self.master.app_settings["export_path"] = path
            messagebox.showinfo("Настройки", "Сохранено.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Настройки", f"Ошибка сохранения:\n{e}")

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

        # Fill window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # In-memory dataset
        # Each order: {"title": str, "status": str, "date": str, "items": [item,...]}
        # item: {"product": str, "sph": str, "cyl": str, "ax": str, "d": str, "qty": str}
        self.orders: list[dict] = []

        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")

        btn_back = ttk.Button(toolbar, text="← Главное меню", style="Accent.TButton", command=self._go_back)

        btn_new_order = ttk.Button(toolbar, text="Новый заказ", style="Menu.TButton", command=self._new_order)
        btn_edit_order = ttk.Button(toolbar, text="Редактировать", style="Menu.TButton", command=self._edit_order)
        btn_delete_order = ttk.Button(toolbar, text="Удалить", style="Menu.TButton", command=self._delete_order)
        btn_change_status = ttk.Button(toolbar, text="Сменить статус", style="Menu.TButton", command=self._change_status)
        btn_export = ttk.Button(toolbar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt)

        btn_back.pack(side="left")
        btn_new_order.pack(side="left", padx=(8, 0))
        btn_edit_order.pack(side="left", padx=(8, 0))
        btn_delete_order.pack(side="left", padx=(8, 0))
        btn_change_status.pack(side="left", padx=(8, 0))
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
            width = {"title": 380, "items_count": 120, "status": 140, "date": 160}[col]
            self.tree.column(col, width=width, anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Status tag colors (light theme)
        self.tree.tag_configure("status_Не заказан", background="#fee2e2", foreground="#7f1d1d")
        self.tree.tag_configure("status_Заказан", background="#fef3c7", foreground="#7c2d12")

        # Context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Редактировать", command=self._edit_order)
        self.menu.add_command(label="Удалить", command=self._delete_order)
        self.menu.add_separator()
        status_menu = tk.Menu(self.menu, tearoff=0)
        for s in self.STATUSES:
            status_menu.add_command(label=s, command=lambda st=s: self._set_status(st))
        self.menu.add_cascade(label="Статус", menu=status_menu)
        self.tree.bind("<Button-3>", self._show_context_menu)
        # Double-click to edit
        self.tree.bind("<Double-1>", lambda e: self._edit_order())

    def _show_context_menu(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.tree.selection_set(iid)
                self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

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
        MeridianOrderForm(self, on_save=self._save_order)

    def _save_order(self, order: dict):
        # Автогенерация имени заказа по порядку, если не задано
        title = (order.get("title", "") or "").strip()
        if not title:
            title = f"Заказ Меридиан #{len(self.orders) + 1}"
            order["title"] = title
        self.orders.append(order)
        self._refresh_orders_view()

    def _edit_order(self):
        idx = self._selected_index()
        if idx is None:
            return
        current = self.orders[idx].copy()

        def on_save(updated: dict):
            # Keep status/date logic: if title/items changed, status stays
            self.orders[idx] = updated
            self._refresh_orders_view()

        MeridianOrderForm(self, on_save=on_save, initial=current)

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

    def _refresh_orders_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, o in enumerate(self.orders):
            values = (
                o.get("title", ""),
                len(o.get("items", [])),
                o.get("status", ""),
                o.get("date", ""),
            )
            tag = f"status_{o.get('status','Не заказан')}"
            self.tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))

    def _export_txt(self):
        """Export items from orders with status 'Не заказан' to TXT. Grouped by product name."""
        import os
        from datetime import datetime

        groups: dict[str, list[dict]] = {}
        for order in self.orders:
            if (order.get("status", "") or "").strip() == "Не заказан":
                for it in order.get("items", []):
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
                for key, label in (("sph", "Sph"), ("cyl", "Cyl"), ("ax", "Ax")):
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


class MeridianOrderForm(tk.Toplevel):
    """Форма создания/редактирования заказа Меридиан (с несколькими позициями)."""
    def __init__(self, master, on_save=None, initial: dict | None = None):
        super().__init__(master)
        self.title("Редактирование заказа" if initial else "Новый заказ")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=900, min_h=700, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        # Order-level vars (без ручного ввода имени)
        self.title_var = tk.StringVar(value=(initial or {}).get("title", ""))
        self.statuses = ["Не заказан", "Заказан"]
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))
        self.is_new = initial is None

        # Items dataset
        self.items: list[dict] = []
        for it in (initial or {}).get("items", []):
            self.items.append(it.copy())

        self._build_ui()

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        # Order status: для новых заказов вовсе не показываем блок статуса
        if not self.is_new:
            header = ttk.Frame(card, style="Card.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            ttk.Label(header, text="Статус заказа", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Combobox(header, textvariable=self.status_var, values=self.statuses, height=4).grid(row=1, column=0, sticky="ew")
            header.columnconfigure(0, weight=1)

        ttk.Separator(card).grid(row=1, column=0, sticky="ew", pady=(12, 12))

        # Items table
        items_frame = ttk.Frame(card, style="Card.TFrame")
        items_frame.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(2, weight=1)

        cols = ("product", "sph", "cyl", "ax", "d", "qty")
        self.items_tree = ttk.Treeview(items_frame, columns=cols, show="headings", style="Data.Treeview")
        headers = {
            "product": "Товар",
            "sph": "SPH",
            "cyl": "CYL",
            "ax": "AX",
            "d": "D (мм)",
            "qty": "Количество",
        }
        widths = {"product": 240, "sph": 90, "cyl": 90, "ax": 90, "d": 90, "qty": 120}
        for c in cols:
            self.items_tree.heading(c, text=headers[c], anchor="w")
            self.items_tree.column(c, width=widths[c], anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(items_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscroll=y_scroll.set)

        self.items_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(0, weight=1)

        # Items toolbar
        items_toolbar = ttk.Frame(card, style="Card.TFrame")
        items_toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(items_toolbar, text="Добавить позицию", style="Menu.TButton", command=self._add_item).pack(side="left")
        ttk.Button(items_toolbar, text="Редактировать позицию", style="Menu.TButton", command=self._edit_item).pack(side="left", padx=(8, 0))
        ttk.Button(items_toolbar, text="Удалить позицию", style="Menu.TButton", command=self._delete_item).pack(side="left", padx=(8, 0))

        # Footer buttons
        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить заказ", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

        # Fill items
        self._refresh_items_view()

    def _refresh_items_view(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, it in enumerate(self.items):
            values = (
                it.get("product", ""),
                it.get("sph", ""),
                it.get("cyl", ""),
                it.get("ax", ""),
                it.get("d", ""),
                it.get("qty", ""),
            )
            self.items_tree.insert("", "end", iid=str(idx), values=values)

    def _selected_item_index(self):
        sel = self.items_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Пожалуйста, выберите позицию.")
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _add_item(self):
        MeridianItemForm(self, on_save=lambda it: (self.items.append(it), self._refresh_items_view()))

    def _edit_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        current = self.items[idx].copy()
        MeridianItemForm(self, initial=current, on_save=lambda it: (self._apply_item_update(idx, it), self._refresh_items_view()))

    def _apply_item_update(self, idx: int, it: dict):
        self.items[idx] = it

    def _delete_item(self):
        idx = self._selected_item_index()
        if idx is None:
            return
        if messagebox.askyesno("Удалить", "Удалить выбранную позицию?"):
            self.items.pop(idx)
            self._refresh_items_view()

    def _save(self):
        status = (self.status_var.get() or "Не заказан").strip()
        from datetime import datetime
        order = {
            "title": (self.title_var.get() or "").strip(),  # может быть пустым, имя назначит родитель
            "status": status,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": self.items.copy(),
        }
        if self.on_save:
            self.on_save(order)
        self.destroy()


class MeridianItemForm(tk.Toplevel):
    """Форма позиции товара для Меридиан."""
    def __init__(self, master, on_save=None, initial: dict | None = None):
        super().__init__(master)
        self.title("Позиция товара")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=600, min_h=420, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

        self.on_save = on_save
        # Vars
        self.product_var = tk.StringVar(value=(initial or {}).get("product", ""))
        self.sph_var = tk.StringVar(value=(initial or {}).get("sph", ""))
        self.cyl_var = tk.StringVar(value=(initial or {}).get("cyl", ""))
        self.ax_var = tk.StringVar(value=(initial or {}).get("ax", ""))
        self.d_var = tk.StringVar(value=(initial or {}).get("d", ""))
        self.qty_var = tk.IntVar(value=int((initial or {}).get("qty", 1)) or 1)

        self._build_ui()

    def _build_ui(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Товар", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.product_var).grid(row=1, column=0, sticky="ew")

        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.sph_entry = ttk.Entry(card, textvariable=self.sph_var)
        self.sph_entry.grid(row=3, column=0, sticky="ew")
        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))

        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=2, column=1, sticky="w", pady=(8, 0))
        self.cyl_entry = ttk.Entry(card, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=3, column=1, sticky="ew")
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=5, column=0, sticky="ew")
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))

        ttk.Label(card, text="D (40…90, шаг 5) — в экспорте добавляется 'мм'", style="Subtitle.TLabel").grid(row=4, column=1, sticky="w", pady=(8, 0))
        self.d_entry = ttk.Entry(card, textvariable=self.d_var)
        self.d_entry.grid(row=5, column=1, sticky="ew")
        # Relaxed validation: allow digits while typing; bounds/step applied on focus out
        d_vcmd = (self.register(self._vc_int_relaxed), "%P")
        self.d_entry.configure(validate="key", validatecommand=d_vcmd)
        self.d_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("d"))

        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=7, column=0, sticky="w")

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить позицию", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    # Validation helpers (local to item form)
    def _vc_decimal(self, new_value: str, min_v: float, max_v: float) -> bool:
        v = (new_value or "").replace(",", ".")
        if v == "":
            return True
        if v in {"+", "-", ".", "-.", "+.", ",", "-,", "+,"}:
            return True
        try:
            num = float(v)
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _vc_int(self, new_value: str, min_v: int, max_v: int) -> bool:
        v = (new_value or "").strip()
        if v == "":
            return True
        if v in {"+", "-"}:
            return True
        try:
            num = int(float(v.replace(",", ".")))
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _vc_int_relaxed(self, new_value: str) -> bool:
        """Allow empty or digits during typing without range enforcement."""
        v = (new_value or "").strip()
        if v == "":
            return True
        # allow plus/minus temporarily
        if v in {"+", "-"}:
            return True
        # allow digits only (no range)
        return v.isdigit()

    def _apply_snap_for(self, field: str):
        if field == "sph":
            self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True))
        elif field == "cyl":
            self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True))
        elif field == "ax":
            self.ax_var.set(self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True))
        elif field == "d":
            # step 5
            v = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
            # ensure multiples of 5
            if v != "":
                try:
                    iv = int(v)
                except Exception:
                    iv = 40
                iv = max(40, min(90, iv))
                # round to nearest multiple of 5
                iv = int(round(iv / 5.0) * 5)
                self.d_var.set(str(iv))
            else:
                self.d_var.set("")

    @staticmethod
    def _snap(value_str: str, min_v: float, max_v: float, step: float, allow_empty: bool = False) -> str:
        text = (value_str or "").replace(",", ".").strip()
        if allow_empty and text == "":
            return ""
        try:
            v = float(text)
        except ValueError:
            v = 0.0 if min_v <= 0.0 <= max_v else min_v
        v = max(min_v, min(max_v, v))
        steps = round((v - min_v) / step)
        snapped = min_v + steps * step
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

    def _save(self):
        product = (self.product_var.get() or "").strip()
        sph = self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True)
        cyl = self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True)
        ax = self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True)
        # D already snapped to multiples of 5
        d = self._snap_int(self.d_var.get(), 40, 90, allow_empty=True)
        if d != "":
            try:
                iv = int(d)
                iv = int(round(iv / 5.0) * 5)
                d = str(iv)
            except Exception:
                pass
        qty = self._snap_int(str(self.qty_var.get()), 1, 20, allow_empty=False)

        if not product:
            messagebox.showinfo("Проверка", "Введите название товара.")
            return

        item = {
            "product": product,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "d": d,
            "qty": qty,
        }
        if self.on_save:
            self.on_save(item)
        self.destroy()


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
        self.db: AppDB | None = getattr(self.master, "db", None)

        # Make the frame fill the window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        # Datasets synced from DB
        self.orders: list[dict] = []
        # Build UI
        self._build_toolbar()
        self._build_table()
        # Initial load from DB into table
        self._refresh_orders_view()

    def _load_orders(self):
        """Compatibility: load orders from DB and render."""
        self._refresh_orders_view()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")

        # Back to main menu (accented)
        btn_back = ttk.Button(toolbar, text="← Главное меню", style="Accent.TButton", command=self._go_back)

        # Order: Новый заказ, Редактировать, Удалить, Сменить статус, Клиент, Добавить Товар, Экспорт TXT
        btn_new_order = ttk.Button(toolbar, text="Новый заказ", style="Menu.TButton", command=self._new_order)
        btn_edit_order = ttk.Button(toolbar, text="Редактировать", style="Menu.TButton", command=self._edit_order)
        btn_delete_order = ttk.Button(toolbar, text="Удалить", style="Menu.TButton", command=self._delete_order)
        btn_change_status = ttk.Button(toolbar, text="Сменить статус", style="Menu.TButton", command=self._change_status)
        btn_clients = ttk.Button(toolbar, text="Клиент", style="Menu.TButton", command=self._open_clients)
        btn_products = ttk.Button(toolbar, text="Добавить Товар", style="Menu.TButton", command=self._open_products)
        btn_export = ttk.Button(toolbar, text="Экспорт TXT", style="Menu.TButton", command=self._export_txt)

        btn_back.pack(side="left")
        btn_new_order.pack(side="left", padx=(8, 0))
        btn_edit_order.pack(side="left", padx=(8, 0))
        btn_delete_order.pack(side="left", padx=(8, 0))
        btn_change_status.pack(side="left", padx=(8, 0))
        btn_clients.pack(side="left", padx=(8, 0))
        btn_products.pack(side="left", padx=(8, 0))
        btn_export.pack(side="left", padx=(8, 0))

    def _go_back(self):
        # Destroy current view and call provided on_back to re-create main menu
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
        # Окно клиентов работает напрямую с БД
        ClientsWindow(self, getattr(self.master, "db", None))

    def _open_products(self):
        # Окно товаров работает напрямую с БД
        ProductsWindow(self, getattr(self.master, "db", None))

    def _new_order(self):
        # Fetch latest clients/products from DB for suggestions
        clients = self.db.list_clients() if self.db else []
        products = self.db.list_products() if self.db else []
        OrderForm(self, clients=clients, products=products, on_save=self._save_order)

    def _save_order(self, order: dict):
        # Persist to DB
        if self.db:
            try:
                self.db.add_mkl_order(order)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось сохранить заказ МКЛ:\n{e}")
        # Reload from DB
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
        order_id = current.get("id")

        # Suggestions from DB
        clients = self.db.list_clients() if self.db else []
        products = self.db.list_products() if self.db else []

        def on_save(updated: dict):
            # Если статус изменился — обновить дату
            new_status = updated.get("status", old_status)
            if new_status != old_status:
                updated["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Persist changes
            if self.db and order_id:
                try:
                    self.db.update_mkl_order(order_id, updated)
                except Exception as e:
                    messagebox.showerror("База данных", f"Не удалось обновить заказ МКЛ:\n{e}")
            # Reload
            self._refresh_orders_view()

        OrderForm(self, clients=clients, products=products, on_save=on_save, initial=current, statuses=self.STATUSES)

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

    def _change_status(self):
        """Open a small dialog to change status of selected order."""
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

    def _export_txt(self):
        """Export only orders with status 'Не заказан' grouped by product to TXT. Filename: MKL_DD.MM.YY.txt"""
        import os
        from datetime import datetime

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
                # Append non-empty fields only
                for key, label in (("sph", "Sph"), ("cyl", "Cyl"), ("ax", "Ax"), ("bc", "BC")):
                    val = (o.get(key, "") or "").strip()
                    if val != "":
                        parts.append(f"{label}: {val}")
                qty = (o.get("qty", "") or "").strip()
                if qty != "":
                    parts.append(f"Количество: {qty}")
                # Add line; if no parts, skip empty line
                if parts:
                    lines.append(" ".join(parts))
            lines.append("")  # blank line after product group

        content = "\n".join(lines).strip() + "\n"
        # Filename like MKL_09.10.25.txt (DD.MM.YY)
        date_str = datetime.now().strftime("%d.%m.%y")
        filename = f"MKL_{date_str}.txt"
        # Use settings' export path if configured; fallback to Desktop or CWD
        export_path = getattr(self.master, "app_settings", {}).get("export_path", None)
        if not export_path:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            export_path = desktop if os.path.isdir(desktop) else os.getcwd()
        filepath = os.path.join(export_path, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Экспорт", f"Экспорт выполнен:\n{filepath}")
            # Try to open the file with default editor (Windows: Notepad)
            try:
                import platform, subprocess
                if hasattr(os, "startfile"):
                    os.startfile(filepath)  # Windows
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

    def _refresh_orders_view(self):
        # Reload list from DB if available
        if self.db:
            try:
                self.orders = self.db.list_mkl_orders()
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось загрузить заказы МКЛ:\n{e}")
        # Clear and render
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self.orders):
            masked_phone = format_phone_mask(item.get("phone", ""))
            values = (
                item.get("fio", ""),
                masked_phone,
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
    """Список клиентов с поиском и CRUD (сохранение в SQLite)."""
    def __init__(self, master: tk.Toplevel, db: AppDB | None):
        super().__init__(master)
        self.title("Клиенты")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Esc closes window
        self.bind("<Escape>", lambda e: self.destroy())

        self.db = db
        self._dataset: list[dict] = []   # [{'id', 'fio', 'phone'}, ...]
        self._filtered: list[dict] = []

        self._build_ui()
        self._reload()

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

    def _reload(self):
        """Загрузить список клиентов из БД."""
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
            self._filtered = [
                c for c in self._dataset
                if term in c.get("fio", "").lower() or term in c.get("phone", "").lower()
            ]
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
        # Сохранить в БД
        try:
            if self.db:
                self.db.add_client(data.get("fio", ""), data.get("phone", ""))
            else:
                # если БД недоступна — добавим временно в список
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
                # обновим локально
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
        # Normalize phone to digits only for storage
        data["phone"] = re.sub(r"\D", "", data["phone"])
        if self.on_save:
            self.on_save(data)
        self.destroy()


class ProductsWindow(tk.Toplevel):
    """Список товаров с CRUD (сохранение в SQLite)."""
    def __init__(self, master: tk.Toplevel, db: AppDB | None):
        super().__init__(master)
        self.title("Товары")
        self.configure(bg="#f8fafc")
        set_initial_geometry(self, min_w=840, min_h=600, center_to=master)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Esc closes window
        self.bind("<Escape>", lambda e: self.destroy())

        self.db = db
        self._dataset: list[dict] = []
        self._filtered: list[dict] = []

        self._build_ui()
        self._reload()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        ProductForm(self, initial=item.copy(), on_save=lambda d: self._on_edit_save(item, d))

    def _on_edit_save(self, original_item: dict, data: dict):
        try:
            if self.db and original_item.get("id") is not None:
                self.db.update_product(original_item["id"], data.get("name", ""))
            else:
                original_item.update(data)
        except Exception as e:
            messagebox.showerror("База данных", f"Не удалось обновить товар:\n{e}")
        self._reload()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._filtered[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранный товар?"):
            try:
                if self.db and item.get("id") is not None:
                    self.db.delete_product(item["id"])
                else:
                    self._dataset.remove(item)
            except Exception as e:
                messagebox.showerror("База данных", f"Не удалось удалить товар:\n{e}")
            self._reload()


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
        self.is_new = initial is None

        # Vars
        self.client_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.sph_var = tk.StringVar(value="")
        self.cyl_var = tk.StringVar(value="")
        self.ax_var = tk.StringVar(value="")
        self.bc_var = tk.StringVar(value="")
        self.qty_var = tk.IntVar(value=1)
        self.status_var = tk.StringVar(value=(initial or {}).get("status", "Не заказан"))

        # Prefill from initial
        if initial:
            masked_phone = format_phone_mask(initial.get("phone", ""))
            self.client_var.set(f'{initial.get("fio","")} — {masked_phone}'.strip(" —"))
            self.product_var.set(initial.get("product", ""))
            self.sph_var.set(initial.get("sph", ""))
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

        # Characteristics — ровная таблица 2×2: заголовки в одной строке, поля в следующей
        # Row 3: labels
        ttk.Label(card, text="SPH (−30.0…+30.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Label(card, text="CYL (−10.0…+10.0, шаг 0.25)", style="Subtitle.TLabel").grid(row=3, column=1, sticky="w", padx=(8, 0))
        # Row 4: entries
        self.sph_entry = ttk.Entry(card, textvariable=self.sph_var)
        self.sph_entry.grid(row=4, column=0, sticky="ew", padx=(0, 8))
        self.cyl_entry = ttk.Entry(card, textvariable=self.cyl_var)
        self.cyl_entry.grid(row=4, column=1, sticky="ew", padx=(8, 0))
        # Validation
        sph_vcmd = (self.register(lambda v: self._vc_decimal(v, -30.0, 30.0)), "%P")
        self.sph_entry.configure(validate="key", validatecommand=sph_vcmd)
        self.sph_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("sph"))
        cyl_vcmd = (self.register(lambda v: self._vc_decimal(v, -10.0, 10.0)), "%P")
        self.cyl_entry.configure(validate="key", validatecommand=cyl_vcmd)
        self.cyl_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("cyl"))

        # Row 5: labels
        ttk.Label(card, text="AX (0…180, шаг 1)", style="Subtitle.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Label(card, text="BC (8.0…9.0, шаг 0.1)", style="Subtitle.TLabel").grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        # Row 6: entries
        self.ax_entry = ttk.Entry(card, textvariable=self.ax_var)
        self.ax_entry.grid(row=6, column=0, sticky="ew", padx=(0, 8))
        self.bc_entry = ttk.Entry(card, textvariable=self.bc_var)
        self.bc_entry.grid(row=6, column=1, sticky="ew", padx=(8, 0))
        # Validation
        ax_vcmd = (self.register(lambda v: self._vc_int(v, 0, 180)), "%P")
        self.ax_entry.configure(validate="key", validatecommand=ax_vcmd)
        self.ax_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("ax"))
        bc_vcmd = (self.register(lambda v: self._vc_decimal(v, 8.0, 9.0)), "%P")
        self.bc_entry.configure(validate="key", validatecommand=bc_vcmd)
        self.bc_entry.bind("<FocusOut>", lambda e: self._apply_snap_for("bc"))

        # Bind clear shortcuts (Delete) for inputs
        for w in (self.client_combo, self.product_combo, self.sph_entry, self.cyl_entry, self.ax_entry, self.bc_entry):
            self._bind_clear_shortcuts(w)

        # Row 7: QTY (без выбора статуса)
        ttk.Label(card, text="Количество (1…20)", style="Subtitle.TLabel").grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.qty_spin = ttk.Spinbox(card, from_=1, to=20, textvariable=self.qty_var, width=8)
        self.qty_spin.grid(row=8, column=0, sticky="w")

        # Footer and save
        footer = ttk.Label(card, text="Дата устанавливается автоматически при создании/смене статуса", style="Subtitle.TLabel")
        footer.grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=10, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(btns, text="Отмена", style="Menu.TButton", command=self.destroy).pack(side="right", padx=(8, 0))

    # Helpers: values for combo and filtering
    def _client_values(self):
        values = []
        for c in self.clients:
            fio = c.get("fio", "")
            phone = format_phone_mask(c.get("phone", ""))
            values.append(f"{fio} — {phone}".strip(" —"))
        return values

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

    # Validation helpers
    def _vc_decimal(self, new_value: str, min_v: float, max_v: float) -> bool:
        """Allow empty or partial numeric like '-', '+', '.', ',', within range."""
        v = (new_value or "").replace(",", ".")
        if v == "":
            return True
        if v in {"+", "-", ".", "-.", "+.", ",", "-,", "+,"}:
            return True
        try:
            num = float(v)
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _vc_int(self, new_value: str, min_v: int, max_v: int) -> bool:
        v = (new_value or "").strip()
        if v == "":
            return True
        # Allow partial '-' while typing
        if v == "-" or v == "+":
            return True
        try:
            num = int(float(v.replace(",", ".")))
        except ValueError:
            return False
        return (min_v <= num <= max_v)

    def _apply_snap_for(self, field: str):
        if field == "sph":
            self.sph_var.set(self._snap(self.sph_var.get(), -30.0, 30.0, 0.25, allow_empty=True))
        elif field == "cyl":
            self.cyl_var.set(self._snap(self.cyl_var.get(), -10.0, 10.0, 0.25, allow_empty=True))
        elif field == "ax":
            self.ax_var.set(self._snap_int(self.ax_var.get(), 0, 180, allow_empty=True))
        elif field == "bc":
            self.bc_var.set(self._snap(self.bc_var.get(), 8.0, 9.0, 0.1, allow_empty=True))

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
        """Return (fio, normalized phone digits) from 'FIO — phone' or direct input."""
        t = (text or "").strip()
        if "—" in t:
            parts = t.split("—", 1)
            fio = parts[0].strip()
            phone_digits = re.sub(r"\D", "", parts[1])
            return fio, phone_digits
        # Try find match from dataset
        term = t.lower()
        for c in self.clients:
            if term in c.get("fio", "").lower() or term in c.get("phone", "").lower():
                return c.get("fio", ""), c.get("phone", "")
        # If user typed a phone directly, normalize digits
        return t, re.sub(r"\D", "", t)

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
        # Status: default to 'Не заказан' for new orders; keep existing for edits
        status = "Не заказан" if self.is_new else (self.status_var.get() or "Не заказан").strip()

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