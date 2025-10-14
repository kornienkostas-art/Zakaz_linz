import tkinter as tk
from tkinter import ttk, messagebox

def _play_sound(master: tk.Tk):
    try:
        settings = getattr(master, "app_settings", {}) or {}
        if bool(settings.get("notify_sound_enabled", True)):
            mode = (settings.get("notify_sound_mode") or "alias")
            try:
                import os as _os
                if _os.name == "nt":
                    import winsound
                    if mode == "file":
                        wav = (settings.get("notify_sound_file") or "").strip()
                        if wav:
                            winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        else:
                            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    else:
                        alias = (settings.get("notify_sound_alias") or "SystemAsterisk")
                        winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
                else:
                    master.bell()
            except Exception:
                try:
                    master.bell()
                except Exception:
                    pass
    except Exception:
        pass

def show_meridian_notification(master: tk.Tk, pending_orders: list[dict], on_snooze, on_mark_ordered):
    """Popup notification for Meridian orders with status 'Не заказан'."""
    _play_sound(master)
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

def show_mkl_notification(master: tk.Tk, pending_orders: list[dict], on_snooze_days, on_mark_ordered):
    """Popup notification for MKL orders with status 'Не заказан' (aged)."""
    _play_sound(master)
    try:
        win = tk.Toplevel(master)
        win.title("Уведомление • Заказы МКЛ")
        win.configure(bg="#f8fafc")
        win.transient(master)
        win.grab_set()
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass

        card = ttk.Frame(win, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(0, weight=1)

        header = ttk.Label(card, text="Есть заказы МКЛ со статусом «Не заказан» (просроченные)", style="Title.TLabel")
        header.grid(row=0, column=0, sticky="w")
        sub = ttk.Label(card, text=f"Всего: {len(pending_orders)}. Вы можете отложить, отметить «Заказан» или закрыть уведомление.", style="Subtitle.TLabel")
        sub.grid(row=1, column=0, sticky="w", pady=(4, 8))

        # Show sample: fio, phone, product, date
        try:
            cols = ("fio", "product", "status", "date")
            tree = ttk.Treeview(card, columns=cols, show="headings", height=6, style="Data.Treeview")
            tree.heading("fio", text="Клиент", anchor="w")
            tree.heading("product", text="Товар", anchor="w")
            tree.heading("status", text="Статус", anchor="w")
            tree.heading("date", text="Дата", anchor="w")
            tree.column("fio", width=240, anchor="w")
            tree.column("product", width=240, anchor="w")
            tree.column("status", width=120, anchor="w")
            tree.column("date", width=160, anchor="w")
            for o in pending_orders[:10]:
                tree.insert("", "end", values=(o.get("fio",""), o.get("product",""), o.get("status",""), o.get("date","")))
            tree.grid(row=2, column=0, sticky="nsew")
            card.rowconfigure(2, weight=1)
        except Exception:
            pass

        ttk.Separator(card).grid(row=3, column=0, sticky="ew", pady=(8, 8))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="e")
        ttk.Button(btns, text="Отложить 1 день", style="Menu.TButton", command=lambda: (_safe(on_snooze_days, 1), win.destroy())).pack(side="right")
        ttk.Button(btns, text="Отложить 3 дня", style="Menu.TButton", command=lambda: (_safe(on_snooze_days, 3), win.destroy())).pack(side="right", padx=(8, 0))
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
    except Exception:
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