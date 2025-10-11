import tkinter as tk
from tkinter import ttk

from app.assets import load_logo


class Shell(ttk.Frame):
    """
    App shell layout that provides:
      - Left sidebar with logo and navigation buttons
      - Top header (title + subtitle) above content
      - Content area (self.content) where views are mounted
    """
    def __init__(self, master: tk.Misc):
        super().__init__(master, padding=16, style="Card.TFrame")
        self.master = master

        # Grid inside given parent (parent should manage its own weights)
        self.grid(sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Sidebar
        self.sidebar = ttk.Frame(self, style="Card.TFrame", padding=12)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        self.sidebar.columnconfigure(0, weight=1)

        # Brand (logo + name)
        brand = ttk.Frame(self.sidebar, style="Card.TFrame")
        brand.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        brand.columnconfigure(1, weight=1)

        self._logo_img = load_logo(self.master)
        if self._logo_img is not None:
            ttk.Label(brand, image=self._logo_img).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8))

        ttk.Label(brand, text="УссурОЧки.рф", style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(brand, text="Управление заказами", style="Subtitle.TLabel").grid(row=1, column=1, sticky="w")

        ttk.Separator(self.sidebar).grid(row=1, column=0, sticky="ew", pady=(8, 8))

        # Nav buttons
        self.btn_home = ttk.Button(self.sidebar, text="🏠 Главное меню", style="Menu.TButton")
        self.btn_mkl = ttk.Button(self.sidebar, text="📦 Заказ МКЛ", style="Menu.TButton")
        self.btn_meridian = ttk.Button(self.sidebar, text="📚 Заказ Меридиан", style="Menu.TButton")
        self.btn_settings = ttk.Button(self.sidebar, text="⚙ Настройки", style="Menu.TButton")

        self.btn_home.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.btn_mkl.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.btn_meridian.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.btn_settings.grid(row=5, column=0, sticky="ew")

        # Header (title + subtitle)
        self.header = ttk.Frame(self, style="Card.TFrame", padding=(8, 4))
        self.header.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.header.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(self.header, text="Главное меню", style="Title.TLabel")
        self.subtitle_label = ttk.Label(self.header, text="Выберите раздел", style="Subtitle.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label.grid(row=1, column=0, sticky="w")

        # Content
        self.content = ttk.Frame(self, style="Card.TFrame", padding=12)
        self.content.grid(row=1, column=1, sticky="nsew")

        # Propagate commonly used attrs to content (from toplevel, not the parent frame)
        top = self.winfo_toplevel()
        for attr in ("db", "app_settings", "tray_icon"):
            if hasattr(top, attr):
                setattr(self.content, attr, getattr(top, attr))

    def set_nav_callbacks(self, on_home, on_mkl, on_meridian, on_settings):
        self.btn_home.configure(command=on_home)
        self.btn_mkl.configure(command=on_mkl)
        self.btn_meridian.configure(command=on_meridian)
        self.btn_settings.configure(command=on_settings)

    def set_header(self, title: str, subtitle: str):
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

    def mount(self, builder):
        """Clear content and mount a new view/frame built by builder(parent_frame)."""
        for child in self.content.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        # Re-propagate attrs to content (ensure db/app_settings exist on the content's master)
        top = self.winfo_toplevel()
        for attr in ("db", "app_settings", "tray_icon"):
            if hasattr(top, attr):
                setattr(self.content, attr, getattr(top, attr))
        return builder(self.content)