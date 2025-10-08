import tkinter as tk
from tkinter import ttk, messagebox


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

    # Placeholder actions
    def _on_order_mkl(self):
        messagebox.showinfo("Заказ МКЛ", "Раздел 'Заказ МКЛ' будет реализован позже.")

    def _on_order_meridian(self):
        messagebox.showinfo("Заказ Меридиан", "Раздел 'Заказ Меридиан' будет реализован позже.")

    def _on_settings(self):
        messagebox.showinfo("Настройки", "Раздел 'Настройки' будет реализован позже.")


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