import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from app.utils import set_initial_geometry


class SettingsView(ttk.Frame):
    """Экран настроек: масштаб интерфейса, папка экспорта, уведомления."""

    def __init__(self, master: tk.Tk, on_back):
        super().__init__(master, style="Card.TFrame", padding=0)
        self.master = master
        self.on_back = on_back

        # Attach settings dict from root
        self.settings = getattr(self.master, "app_settings", {}) or {}

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="← Назад", style="Accent.TButton", command=self._go_back).pack(side="left")

        card = ttk.Frame(self, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        # UI scale
        ttk.Label(card, text="Масштаб интерфейса (tk scaling)", style="Subtitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.ui_scale_var = tk.DoubleVar(value=float(self.settings.get("ui_scale", 1.25)))
        self.ui_scale_spin = ttk.Spinbox(card, from_=0.8, to=2.0, increment=0.05, textvariable=self.ui_scale_var, width=10)
        self.ui_scale_spin.grid(row=0, column=1, sticky="w", padx=(8, 0))

        # Export path
        ttk.Label(card, text="Папка экспорта TXT", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 4))
        self.export_var = tk.StringVar(value=(self.settings.get("export_path") or ""))
        export_row = ttk.Frame(card, style="Card.TFrame")
        export_row.grid(row=1, column=1, sticky="ew")
        entry = ttk.Entry(export_row, textvariable=self.export_var)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(export_row, text="Обзор…", command=self._choose_export_path).pack(side="left", padx=(8, 0))

        # Notifications
        ttk.Separator(card).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 16))
        ttk.Label(card, text="Уведомления по заказам", style="Title.TLabel").grid(row=3, column=0, sticky="w")
        self.notify_enabled_var = tk.BooleanVar(value=bool(self.settings.get("notify_enabled", True)))
        ttk.Checkbutton(card, text="Включить уведомления", variable=self.notify_enabled_var).grid(row=3, column=1, sticky="w")

        ttk.Label(card, text="Интервал проверки (мин.)", style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.notify_interval_var = tk.IntVar(value=int(self.settings.get("notify_interval_minutes", 10)))
        ttk.Spinbox(card, from_=1, to=240, textvariable=self.notify_interval_var, width=10).grid(row=4, column=1, sticky="w", padx=(8, 0))

        ttk.Label(card, text="Возраст заказа для напоминания (час.)", style="Subtitle.TLabel").grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.notify_age_var = tk.IntVar(value=int(self.settings.get("notify_age_hours", 24)))
        ttk.Spinbox(card, from_=1, to=168, textvariable=self.notify_age_var, width=10).grid(row=5, column=1, sticky="w", padx=(8, 0))

        ttk.Separator(card).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 16))

        # Actions
        actions = ttk.Frame(card, style="Card.TFrame")
        actions.grid(row=7, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Сохранить", style="Menu.TButton", command=self._save).pack(side="right")
        ttk.Button(actions, text="Применить", style="Menu.TButton", command=self._apply).pack(side="right", padx=(8, 0))

    def _choose_export_path(self):
        path = filedialog.askdirectory(title="Выберите папку экспорта")
        if path:
            self.export_var.set(path)

    def _save(self):
        data = dict(self.settings)
        data["ui_scale"] = float(self.ui_scale_var.get())
        data["export_path"] = self.export_var.get().strip()
        data["notify_enabled"] = bool(self.notify_enabled_var.get())
        data["notify_interval_minutes"] = int(self.notify_interval_var.get())
        data["notify_age_hours"] = int(self.notify_age_var.get())

        # Persist to settings.json at project root
        try:
            import json
            SETTINGS_FILE = "settings.json"
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Update root
            self.master.app_settings = data
            messagebox.showinfo("Настройки", "Сохранено.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось сохранить:\n{e}")

    def _apply(self):
        # Apply scaling immediately
        try:
            scale = float(self.ui_scale_var.get())
            self.master.tk.call("tk", "scaling", scale)
            # Save in-memory
            self.settings["ui_scale"] = scale
            self.settings["notify_enabled"] = bool(self.notify_enabled_var.get())
            self.settings["notify_interval_minutes"] = int(self.notify_interval_var.get())
            self.settings["notify_age_hours"] = int(self.notify_age_var.get())
            messagebox.showinfo("Настройки", "Изменения применены.")
        except Exception as e:
            messagebox.showerror("Настройки", f"Не удалось применить:\n{e}")

    def _go_back(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_back):
                self.on_back()