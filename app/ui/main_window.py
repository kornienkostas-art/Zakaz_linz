import sqlite3
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QStackedWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QToolBar,
    QComboBox,
    QFileDialog,
    QMessageBox,
)

from ..settings_store import SettingsStore
from ..themes import apply_theme
from ..models import OrderStatus
from .mkl_orders_page import MklOrdersPage
from .meridian_orders_page import MeridianOrdersPage
from .settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, conn: sqlite3.Connection, settings: SettingsStore) -> None:
        super().__init__()
        self.conn = conn
        self.settings_store = settings
        self.settings = self.settings_store.get()

        self.setWindowTitle("УссурОЧки.рф")
        self.resize(1100, 700)

        self._make_ui()
        self._wire_events()

    def _make_ui(self) -> None:
        self.header_label = QLabel("УссурОЧки.рф")
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 6px;")

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Системная", "Светлая", "Тёмная"])
        current = self.settings.get("theme", "system")
        self.theme_combo.setCurrentIndex(["system", "light", "dark"].index(current))

        header_buttons = QHBoxLayout()
        self.btn_orders_mkl = QPushButton("Заказы МКЛ")
        self.btn_orders_meridian = QPushButton("Заказы Меридиан")
        self.btn_settings = QPushButton("Настройки")
        header_buttons.addWidget(self.btn_orders_mkl)
        header_buttons.addWidget(self.btn_orders_meridian)
        header_buttons.addWidget(self.btn_settings)
        header_buttons.addStretch()
        header_buttons.addWidget(QLabel("Тема:"))
        header_buttons.addWidget(self.theme_combo)

        header = QHBoxLayout()
        header.addWidget(self.header_label)
        header.addLayout(header_buttons)

        self.stack = QStackedWidget()
        self.page_mkl = MklOrdersPage(self.conn, self.settings_store)
        self.page_meridian = MeridianOrdersPage(self.conn, self.settings_store)
        self.page_settings = SettingsPage(self.conn, self.settings_store)

        self.stack.addWidget(self.page_mkl)
        self.stack.addWidget(self.page_meridian)
        self.stack.addWidget(self.page_settings)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(header)
        layout.addWidget(self.stack)
        self.setCentralWidget(root)

        self._switch_to("Заказы МКЛ")

    def _wire_events(self) -> None:
        self.btn_orders_mkl.clicked.connect(lambda: self._switch_to("Заказы МКЛ"))
        self.btn_orders_meridian.clicked.connect(lambda: self._switch_to("Заказы Меридиан"))
        self.btn_settings.clicked.connect(lambda: self._switch_to("Настройки"))

        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        self.page_settings.theme_changed.connect(self._on_theme_change_settings)

    def _switch_to(self, name: str) -> None:
        if name == "Заказы МКЛ":
            self.stack.setCurrentWidget(self.page_mkl)
        elif name == "Заказы Меридиан":
            self.stack.setCurrentWidget(self.page_meridian)
        else:
            self.stack.setCurrentWidget(self.page_settings)

    def _on_theme_change(self) -> None:
        idx = self.theme_combo.currentIndex()
        theme = ["system", "light", "dark"][idx]
        self.settings_store.set("theme", theme)
        apply_theme(theme)

    def _on_theme_change_settings(self) -> None:
        # Keep header combo synced with settings page
        self.settings = self.settings_store.get()
        theme = self.settings.get("theme", "system")
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(["system", "light", "dark"].index(theme))
        self.theme_combo.blockSignals(False)
        apply_theme(theme)