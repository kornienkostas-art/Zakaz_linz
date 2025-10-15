from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk, settings: dict | None = None) -> None:
    """
    Apply a modern-looking theme to all ttk widgets.
    Keeps existing style names used across the app, but improves visuals.
    """
    style = ttk.Style(root)

    # Use a known base theme for better styling support
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    # Colors
    # Light UI with vibrant primary
    bg = "#f8fafc"          # slate-50
    card_bg = "#ffffff"     # white
    border = "#e2e8f0"      # slate-200
    text = "#0f172a"        # slate-900
    subtext = "#475569"     # slate-600
    muted = "#94a3b8"       # slate-400
    primary = "#2563eb"     # blue-600
    primary_hover = "#1d4ed8"  # blue-700
    accent = "#10b981"      # emerald-500
    danger_bg = "#fee2e2"   # red-100
    danger_fg = "#7f1d1d"   # red-900
    warn_bg = "#fef3c7"     # amber-100
    warn_fg = "#7c2d12"     # amber-900
    info_bg = "#dbeafe"     # blue-100
    info_fg = "#1e3a8a"     # blue-900
    success_bg = "#dcfce7"  # green-100
    success_fg = "#065f46"  # green-900
    selection_bg = "#dbeafe"  # soft blue
    selection_border = "#93c5fd"

    # Root background
    try:
        root.configure(bg=bg)
    except Exception:
        pass

    # Common layout padding
    style.configure(".", background=bg, foreground=text)

    # Frames
    style.configure("Card.TFrame", background=card_bg, bordercolor=border, relief="solid", borderwidth=1)
    style.configure("Header.TFrame", background=card_bg, bordercolor=border, relief="flat", borderwidth=0)

    # Labels
    style.configure("TLabel", background=bg, foreground=text)
    style.configure("Title.TLabel", background=card_bg, foreground=text, font=("Segoe UI", 18, "bold"))
    style.configure("Subtitle.TLabel", background=card_bg, foreground=subtext, font=("Segoe UI", 12))
    style.configure("Hero.TLabel", background=card_bg, foreground=text, font=("Segoe UI", 22, "bold"))

    # Buttons
    style.configure("TButton", padding=(14, 10), relief="flat", background=primary, foreground="#ffffff")
    style.map("TButton",
              background=[("active", primary_hover), ("pressed", primary_hover)],
              foreground=[("disabled", muted)])
    # Menu button - secondary/ghost
    style.configure("Menu.TButton", padding=(12, 8), relief="flat", background="#eef2ff", foreground=primary,
                    bordercolor="#c7d2fe")
    style.map("Menu.TButton",
              background=[("active", "#e0e7ff"), ("pressed", "#e0e7ff")])
    # Back button - accent
    style.configure("Back.TButton", padding=(12, 8), relief="flat", background=accent, foreground="#062c23")
    style.map("Back.TButton",
              background=[("active", "#0ea37a"), ("pressed", "#0ea37a")])

    # Treeview
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

    # Scrollbars - slimmer
    style.configure("Vertical.TScrollbar", gripcount=0, background=card_bg, darkcolor=border, lightcolor=border,
                    troughcolor=bg, bordercolor=border, arrowcolor=muted)
    style.configure("Horizontal.TScrollbar", gripcount=0, background=card_bg, darkcolor=border, lightcolor=border,
                    troughcolor=bg, bordercolor=border, arrowcolor=muted)

    # Separators
    style.configure("TSeparator", background=border)

    # Combobox
    style.configure("TCombobox", fieldbackground=card_bg, background=card_bg, bordercolor=border, lightcolor=border,
                    darkcolor=border)
    style.map("TCombobox",
              fieldbackground=[("readonly", card_bg), ("!disabled", card_bg)],
              selectbackground=[("readonly", selection_bg)],
              selectforeground=[("readonly", text)])

    # Checkbutton / Radiobutton
    style.configure("TCheckbutton", background=card_bg, foreground=text)
    style.configure("TRadiobutton", background=card_bg, foreground=text)

    # Tag colors for statuses (Treeview tags configured in views)
    # We leave tags setup in views, but ensure contrasty text is okay on our palette.