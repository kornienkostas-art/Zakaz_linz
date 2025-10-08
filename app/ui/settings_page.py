import os
import sqlite3
from typing import Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QFileDialog,
    QCheckBox,
)

from ..settings_store import SettingsStore


class SettingsPage(QWidget):
    theme_changed = Signal()

    def __init__(self, conn: sqlite3.Connection, settings: SettingsStore) -> None:
        super().__init__()
        self.conn = conn
        self.settings_store = settings
        self.settings = self.settings_store.get()
        self._make_ui()
        self._load()

    def _make_ui(self) -> None:
        layout = QVBoxLayout(self)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Системная"])
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)

        export_row = QHBoxLayout()
        export_row.addWidget(QLabel("Папка экспорта:"))
        self.export_edit = QLineEdit()
        self.browse_btn = QPushButton("Выбрать…")
        export_row.addWidget(self.export_edit, stretch=1)
        export_row.addWidget(self.browse_btn)
        layout.addLayout(export_row)

        self.chk_show_eye = QCheckBox("Показывать OD/OS")
        self.chk_show_bc = QCheckBox("Показывать BC в МКЛ")
        self.chk_aggregate = QCheckBox("Агрегировать одинаковые спецификации")
        layout.addWidget(self.chk_show_eye)
        layout.addWidget(self.chk_show_bc)
        layout.addWidget(self.chk_aggregate)
        layout.addStretch()

        # events
        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        self.browse_btn.clicked.connect(self._browse)
        self.export_edit.editingFinished.connect(self._save_export_folder)
        self.chk_show_eye.toggled.connect(lambda b: self._save_bool("show_eye", b))
        self.chk_show_bc.toggled.connect(lambda b: self._save_bool("show_bc_mkl", b))
        self.chk_aggregate.toggled.connect(lambda b: self._save_bool("aggregate_specs", b))

    def _load(self) -> None:
        theme = self.settings.get("theme", "system")
        idx_map = {"light": 0, "dark": 1, "system": 2}
        self.theme_combo.setCurrentIndex(idx_map.get(theme, 2))
        self.export_edit.setText(self.settings.get("export_folder", "exports"))
        self.chk_show_eye.setChecked(bool(self.settings.get("show_eye", True)))
        self.chk_show_bc.setChecked(bool(self.settings.get("show_bc_mkl", True)))
        self.chk_aggregate.setChecked(bool(self.settings.get("aggregate_specs", True)))

    def _on_theme_change(self) -> None:
        idx = self.theme_combo.currentIndex()
        theme = {0: "light", 1: "dark", 2: "system"}[idx]
        self.settings_store.set("theme", theme)
        self.theme_changed.emit()

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Выберите папку экспорта", self.export_edit.text() or os.getcwd())
        if d:
            self.export_edit.setText(d)
            self._save_export_folder()

    def _save_export_folder(self) -> None:
        folder = self.export_edit.text().strip()
        if not folder:
            return
        self.settings_store.set("export_folder", folder)

    def _save_bool(self, key: str, val: bool) -> None:
        self.settings_store.set(key, val)