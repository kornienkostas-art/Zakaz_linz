import tkinter as tk
from tkinter import ttk, filedialog, font

from app.db import AppDB
from app.utils import set_initial_geometry, fade_transition, resolve_asset_path


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("УссурОЧки.рф — Заказ линз")

        # Geometry
        set_initial_geometry(self.root, min_w=1100, min_h=760)

        # Ensure DB exists on root (created in main.py), but allow fallback
        if not hasattr(self.root, "db") or not isinstance(self.root.db, AppDB):
            self.root.db = AppDB("data.db")

        # Load settings dict (set in main.py)
        self.app_settings = getattr(self.root, "app_settings", {})

        self._build_ui()
        self._refresh_stats()

    def _try_load_logo(self, size=48):
        # Try to load a square logo from assets; return PhotoImage or None
        candidates = [
            self.app_settings.get("tray_logo_path") or "",
            "app/assets/android-chrome-192x192.png",
            "app/assets/apple-touch-icon.png",
            "app/assets/logo.png",
            "app/assets/favicon-32x32.png",
            "app/assets/favicon-16x16.png",
        ]
        path = None
        for rel in candidates:
            p = resolve_asset_path(rel)
            if p:
                path = p
                break
        if not path:
            return None
        # Prefer PIL for resize
        try:
            from PIL import Image, ImageTk  # type: ignore
            img = Image.open(path).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            # Keep ref
            self._logo_img = photo
            return photo
        except Exception:
            try:
                photo = tk.PhotoImage(file=path)
                self._logo_img = photo
                return photo
            except Exception:
                return None

    def _build_ui(self):
        # Try to use ttkbootstrap buttons if available
        try:
            from ttkbootstrap import Button as TBButton  # type: ignore
            ButtonCls = TBButton
            use_bootstyle = True
        except Exception:
            ButtonCls = ttk.Button
            use_bootstyle = False

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # HEADER with logo + title
        header = ttk.Frame(container, style="Header.TFrame")
        header.pack(fill="x", padx=32, pady=(24, 8))
        logo = self._try_load_logo(48)
        if logo:
            ttk.Label(header, image=logo, style="Header.TLabel").pack(side="left", padx=(8, 16))
        title_block = ttk.Frame(header, style="Header.TFrame")
        title_block.pack(side="left")
        ttk.Label(title_block, text="УссурОЧки.рф", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="Заказы контактных линз • МКЛ и «Меридиан»", style="Subtitle.TLabel").pack(anchor="w")

        # TILES
        tiles = ttk.Frame(container, style="Card.TFrame", padding=24)
        tiles.pack(fill="both", expand=True, padx=32, pady=(8, 32))
        # Make equal-size tiles
        for i in range(3):
            tiles.columnconfigure(i, weight=1)

        # Create tile helper
        def add_tile(col: int, text: str, command, bootstyle: str = "primary"):
            frame = ttk.Frame(tiles, style="Card.TFrame", padding=16)
            frame.grid(row=0, column=col, sticky="nsew", padx=12, pady=12)
            # Big button fills tile
            btn_kwargs = dict(text=text, command=command)
            if use_bootstyle:
                btn_kwargs["bootstyle"] = bootstyle  # type: ignore
            ButtonCls(frame, **btn_kwargs).pack(fill="both", expand=True, ipady=18)

        add_tile(0, "Заказы МКЛ", self._open_mkl, "primary")
        add_tile(1, "Заказы «Меридиан»", self._open_meridian, "info")
        add_tile(2, "Настройки", self._open_settings, "secondary")

    def _refresh_stats(self):
        # На главном экране счётчики скрыты; оставим заглушку для совместимости.
        try:
            _ = self.root.db
        except Exception:
            pass

    # Navigation
    def _open_clients(self):
        def swap():
            self._clear_root_frames()
            from app.views.clients import ClientsView
            ClientsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_products(self):
        def swap():
            self._clear_root_frames()
            from app.views.products import ProductsView
            ProductsView(self.root, self.root.db, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_mkl(self):
        def swap():
            self._clear_root_frames()
            from app.views.orders_mkl import MKLOrdersView
            MKLOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_meridian(self):
        def swap():
            self._clear_root_frames()
            from app.views.orders_meridian import MeridianOrdersView
            MeridianOrdersView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _open_settings(self):
        # Открывать настройки во встроенном виде (не отдельным окном)
        def swap():
            self._clear_root_frames()
            from app.views.settings import SettingsView
            SettingsView(self.root, on_back=lambda: MainWindow(self.root))
        fade_transition(self.root, swap)

    def _clear_root_frames(self):
        try:
            for child in self.root.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    