import tkinter as tk
from tkinter import ttk, messagebox

def show_meridian_notification(master: tk.Tk, pending_orders: list[dict], on_snooze, on_mark_ordered):
    """Popup notification for Meridian orders with status 'Не заказан'."""
    # Play sound if enabled
    try:
        settings = getattr(master, "app_settings", {}) or {}
        if bool(settings.get("notify_sound_enabled", True)):
            alias = (settings.get("notify_sound_alias") or "SystemAsterisk")
            try:
                import os as _os
                if _os.name == "nt":
                    import winsound
                    # Play selected system sound alias asynchronously
                    winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
                else:
                    # Fallback bell on non-Windows
                    master.bell()
            except Exception:
                try:
                    master.bell()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        win = tk.Toplevel(master)
        win.title("Уведомление • Заказы Меридиан")
        win.configure(bg="#f8fafc")
        win.transient(master)
        win.grab_set()
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass

        # Layout
        card = ttk.Frame(win, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        header = ttk.Label(card, text="Есть заказы Меридиан со статусом «Не заказан»", style="Title.TLabel")
        header.grid(row=0, column=0, sticky="w")
        sub = ttk.Label(card, text=f"Всего: {len(pending_orders)}. Вы можете отложить, отметить «Заказан» или закрыть уведомление.", style="Subtitle.TLabel")
        sub.grid(row=1, column=0, sticky="w", pady=(4, 8))

        # Show sample of orders (first 5)
        try:
            tree = ttk.Treeview(card, columns=("title", "status", "date"), show="headings", height=6, style="Data.Treeview")
            tree.heading("title", text="Название", anchor="w")
            tree.heading("status", text="Статус", anchor="w")
            tree.heading("date", text="Дата", anchor="w")
            tree.column("title", width=400, anchor="w")
            tree.column("status", width=120, anchor="w")
            tree.column("date", width=160, anchor="w")
            for o in pending_orders[:10]:
                tree.insert("", "end", values=(o.get("title",""), o.get("status",""), o.get("date","")))
            tree.grid(row=2, column=0, sticky="nsew")
            card.rowconfigure(2, weight=1)
        except Exception:
            pass

        ttk.Separator(card).grid(row=3, column=0, sticky="ew", pady=(8, 8))

        # Buttons
        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e")
        ttk.Button(btns, text="Отложить 15 мин", style="Menu.TButton", command=lambda: (_safe(on_snooze, 15), win.destroy())).pack(side="right")
        ttk.Button(btns, text="Отложить 30 мин", style="Menu.TButton", command=lambda: (_safe(on_snooze, 30), win.destroy())).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Отметить «Заказан»", style="Menu.TButton", command=lambda: (_safe(on_mark_ordered), win.destroy())).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Закрыть", style="Back.TButton", command=win.destroy).pack(side="right", padx=(8, 0))

        # Center relative to master
        try:
            master.update_idletasks()
            win.update_idletasks()
            sw = master.winfo_rootx()
            sh = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            ww = win.winfo_width()
            wh = win.winfo_height()
            x = sw + (mw // 2) - (ww // 2)
            y = sh + (mh // 2) - (wh // 2)
            win.geometry(f"+{x}+{y}")
        except Exception:
            pass
    except Exception as e:
        try:
            messagebox.showinfo("Уведомление", f"Есть заказы «Не заказан»: {len(pending_orders)}")
        except Exception:
            pass

def _safe(fn, *args, **kwargs):
    try:
        if callable(fn):
            fn(*args, **kwargs)
    except Exception:
        pass