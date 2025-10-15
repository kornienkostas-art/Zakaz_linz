from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk, settings: dict | None = None) -> None:
    """
    Apply a modern-looking theme to all ttk widgets.
    If ttkbootstrap is present and active, skip heavy overrides to avoid conflicts.
    """
    # If ttkbootstrap is in use, do minimal tweaks only
    try:
        import ttkbootstrap  # type: ignore
        # Bootstrap already provides a modern theme; we keep only a few style aliases expected by views.
        style = ttk.Style(root)
        # Ensure aliases exist with decent fonts
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 12))
        style.configure("Card.TFrame")
        style.configure("Menu.TButton")
        style.configure("Back.TButton")
        style.configure("Data.Treeview")
        style.configure("Data.Treeview.Heading", font=("Segoe UI", 11, "bold"))
        return
    except Exception:
        pass

    # Fallback: native ttk modernized palette
    style = ttk.Style(root)

    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    bg = "#f8fafc"
    card_bg = "#ffffff"
    border = "#e2e8f0"
    text = "#0f172a"
    subtext = "#475569"
    muted = "#94a3b8"
    primary = "#2563eb"
    primary_hover = "#1d4ed8"
    accent = "#10b981"
    selection_bg = "#dbeafe"

    try:
        root.configure(bg=bg)
    except Exception:
        pass

    style.configure(".", background=bg, foreground=text)

    style.configure("Card.TFrame", background=card_bg, bordercolor=border, relief="solid", borderwidth=1)
    style.configure("Header.TFrame", background=card_bg, bordercolor=border, relief="flat", borderwidth=0)

    style.configure("TLabel", background=bg, foreground=text)
    style.configure("Title.TLabel", background=card_bg, foreground=text, font=("Segoe UI", 18, "bold"))
    style.configure("Subtitle.TLabel", background=card_bg, foreground=subtext, font=("Segoe UI", 12))
    style.configure("Hero.TLabel", background=card_bg, foreground=text, font=("Segoe UI", 22, "bold"))

    style.configure("TButton", padding=(14, 10), relief="flat", background=primary, foreground="#ffffff")
    style.map("TButton",
              background=[("active", primary_hover), ("pressed", primary_hover)],
              foreground=[("disabled", muted)])

    style.configure("Menu.TButton", padding=(12, 8), relief="flat", background="#eef2ff", foreground=primary,
                    bordercolor="#c7d2fe")
    style.map("Menu.TButton",
              background=[("active", "#e0e7ff"), ("pressed", "#e0e7ff")])
    style.configure("Back.TButton", padding=(12, 8), relief="flat", background=accent, foreground="#062c23")
    style.map("Back.TButton",
              background=[("active", "#0ea37a"), ("pressed", "#0ea37a")])

    style.configure("Data.Treeview",
                    background=card_bg,
                    fieldbackground=card_bg,
                    foreground=text,
                    bordercolor=border,
                    lightcolor=border,
                    darkcolor=border,
                    rowheight=int(style.lookup("Treeview", "rowheight") or 28))
    style.configure("Data.Treeview.Heading",
                    background=card_bg, foreground=subtext,
                    relief="flat", bordercolor=border, font=("Segoe UI", 11, "bold"))
    style.map("Data.Treeview",
              background=[("selected", selection_bg)],
              foreground=[("selected", text)])

    style.configure("Vertical.TScrollbar", gripcount=0, background=card_bg, darkcolor=border, lightcolor=border,
                    troughcolor=bg, bordercolor=border)
    style.configure("Horizontal.TScrollbar", gripcount=0, background=card_bg, darkcolor=border, lightcolor=border,
                    troughcolor=bg, bordercolor=border)

    style.configure("TSeparator", background=border)

    style.configure("TCombobox", fieldbackground=card_bg, background=card_bg, bordercolor=border, lightcolor=border,
                    darkcolor=border)
    style.map("TCombobox",
              fieldbackground=[("readonly", card_bg), ("!disabled", card_bg)],
              selectbackground=[("readonly", selection_bg)],
              selectforeground=[("readonly", text)])

    style.configure("TCheckbutton", background=card_bg, foreground=text)
    style.configure("TRadiobutton", background=card_bg, foreground=text)