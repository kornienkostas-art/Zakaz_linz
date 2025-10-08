# -*- coding: utf-8 -*-
#
# Десктоп-приложение "УссурОЧки.рф" для управления заказами
# Стек: Python 3.10+, PySide6, SQLite (локально, без сервера)
#
# Функциональность (MVP):
# - Главное окно: "Заказы МКЛ", "Заказы Меридиан", "Настройки"
# - CRUD для МКЛ: клиенты, товары, заказы (цветовая подсветка по статусам)
# - CRUD для Меридиан: заказы с автонумерацией, товары внутри заказа (свободный ввод), цветовая подсветка по статусам
# - Экспорт TXT по статусам
# - Тёмная/светлая тема, базовые анимации при смене страниц
#
# Примечание: приложение старается быть компактным и самодостаточным в одном файле.
# Для полноценного продакшен-уровня можно разнести на модули, добавить тесты и упаковку в exe.
#
# Запуск:
#   pip install PySide6
#   python ussurochki_app.py
#
# Автор: Genie (Cosine)

import os
import sys
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QAction, QIcon, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLineEdit,
    QComboBox,
    QDateTimeEdit,
    QMessageBox,
    QFileDialog,
    QDialog,
    QFormLayout,
    QSpinBox,
    QSplitter,
    QGroupBox,
)

APP_TITLE = "УссурОЧки.рф"
DB_FILE = "ussurochki_local.db"

# Цвета статусов
STATUS_STYLES_MKL = {
    "не заказан": QColor(255, 220, 220),  # светло-красный
    "заказан": QColor(255, 245, 204),     # светло-жёлтый
    "прозвонен": QColor(204, 229, 255),   # светло-синий
    "вручен": QColor(204, 255, 204),      # светло-зелёный
}
STATUS_ORDER_MKL = ["не заказан", "заказан", "прозвонен", "вручен"]

STATUS_STYLES_MER = {
    "не заказан": QColor(255, 220, 220),
    "заказан": QColor(204, 255, 204),
}
STATUS_ORDER_MER = ["не заказан", "заказан"]

DARK_QSS = """
QWidget {
    background-color: #1e1f22;
    color: #e6e6e6;
    font-size: 12pt;
}
QPushButton {
    background-color: #2b2d31;
    border: 1px solid #3a3c40;
    padding: 8px 12px;
    border-radius: 6px;
}
QPushButton:hover {
    background-color: #34363b;
}
QPushButton:pressed {
    background-color: #222327;
}
QLineEdit, QComboBox, QDateTimeEdit, QListWidget {
    background-color: #2b2d31;
    border: 1px solid #3a3c40;
    border-radius: 6px;
    padding: 6px;
}
QGroupBox {
    border: 1px solid #3a3c40;
    border-radius: 8px;
    margin-top: 12px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 6px;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f5f6f8;
    color: #202020;
    font-size: 12pt;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    padding: 8px 12px;
    border-radius: 6px;
}
QPushButton:hover {
    background-color: #f0f0f0;
}
QPushButton:pressed {
    background-color: #e6e6e6;
}
QLineEdit, QComboBox, QDateTimeEdit, QListWidget {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 6px;
    padding: 6px;
}
QGroupBox {
    border: 1px solid #dddddd;
    border-radius: 8px;
    margin-top: 12px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 6px;
}
"""

def ensure_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Клиенты
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT
    );
    """)

    # Товары (общий каталог для МКЛ)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL DEFAULT 0
    );
    """)

    # Заказы МКЛ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders_mkl (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_mkl_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    # Заказы Меридиан (автонумерация number)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders_meridian (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_meridian_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ---------- Диалоги ----------

class ClientDialog(QDialog):
    def __init__(self, parent=None, client: Optional[Tuple[int, str, str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        layout.addRow("ФИО:", self.name_edit)
        layout.addRow("Телефон:", self.phone_edit)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отменить")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        if client:
            _, name, phone = client
            self.name_edit.setText(name)
            self.phone_edit.setText(phone or "")

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        return self.name_edit.text().strip(), self.phone_edit.text().strip()

class ProductDialog(QDialog):
    def __init__(self, parent=None, product: Optional[Tuple[int, str, float]] = None):
        super().__init__(parent)
        self.setWindowTitle("Товар")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        layout.addRow("Название:", self.name_edit)
        layout.addRow("Цена (₽):", self.price_edit)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отменить")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        if product:
            _, name, price = product
            self.name_edit.setText(name)
            self.price_edit.setText(str(price or 0))

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        name = self.name_edit.text().strip()
        try:
            price = float(self.price_edit.text().strip() or "0")
        except ValueError:
            price = 0.0
        return name, price

class MKLOrderDialog(QDialog):
    def __init__(self, parent=None, order_id: Optional[int] = None):
        super().__init__(parent)
        self.setWindowTitle("Заказ МКЛ")
        self.setModal(True)
        self.order_id = order_id

        main = QVBoxLayout(self)

        # Клиент и статус
        form_box = QGroupBox("Основные данные")
        form = QFormLayout(form_box)
        self.client_combo = QComboBox()
        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUS_ORDER_MKL)
        self.date_edit = QDateTimeEdit(datetime.now())
        self.date_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.date_edit.setCalendarPopup(True)
        self.notes_edit = QLineEdit()
        form.addRow("Клиент:", self.client_combo)
        form.addRow("Статус:", self.status_combo)
        form.addRow("Дата:", self.date_edit)
        form.addRow("Заметки:", self.notes_edit)

        # Товары
        items_box = QGroupBox("Товары в заказе")
        items_layout = QVBoxLayout(items_box)
        self.products_combo = QComboBox()
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999)
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Товар:"))
        add_row.addWidget(self.products_combo, 1)
        add_row.addWidget(QLabel("Кол-во:"))
        add_row.addWidget(self.qty_spin)
        self.add_item_btn = QPushButton("Добавить позицию")
        add_row.addWidget(self.add_item_btn)
        items_layout.addLayout(add_row)

        self.items_list = QListWidget()
        items_layout.addWidget(self.items_list)
        self.remove_item_btn = QPushButton("Удалить позицию")
        items_layout.addWidget(self.remove_item_btn)

        main.addWidget(form_box)
        main.addWidget(items_box)

        # Кнопки
        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отменить")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        main.addLayout(btns)

        # Загрузка данных
        self._load_clients()
        self._load_products()

        if order_id:
            self._load_order(order_id)

        # Сигналы
        self.add_item_btn.clicked.connect(self._add_item)
        self.remove_item_btn.clicked.connect(self._remove_item)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_clients(self):
        conn = db_conn()
        rows = conn.execute("SELECT id, name, phone FROM clients ORDER BY name;").fetchall()
        conn.close()
        self.client_combo.clear()
        for cid, name, phone in rows:
            display = f"{name} ({phone})" if phone else name
            self.client_combo.addItem(display, cid)

    def _load_products(self):
        conn = db_conn()
        rows = conn.execute("SELECT id, name FROM products ORDER BY name;").fetchall()
        conn.close()
        self.products_combo.clear()
        for pid, name in rows:
            self.products_combo.addItem(name, pid)

    def _load_order(self, order_id: int):
        conn = db_conn()
        order = conn.execute(
            "SELECT client_id, status, created_at, notes FROM orders_mkl WHERE id=?;",
            (order_id,)
        ).fetchone()
        items = conn.execute(
            """SELECT p.id, p.name, i.qty
               FROM order_mkl_items i
               JOIN products p ON p.id=i.product_id
               WHERE i.order_id=? ORDER BY i.id;""",
            (order_id,)
        ).fetchall()
        conn.close()

        if not order:
            return

        client_id, status, created_at, notes = order
        # Установить клиента
        idx = max(0, self.client_combo.findData(client_id))
        self.client_combo.setCurrentIndex(idx)

        # Статус, дата, заметки
        self.status_combo.setCurrentText(status)
        try:
            dt = datetime.fromisoformat(created_at)
        except Exception:
            dt = datetime.now()
        self.date_edit.setDateTime(dt)
        self.notes_edit.setText(notes or "")

        # Позиции
        self.items_list.clear()
        for pid, name, qty in items:
            item = QListWidgetItem(f"{name} — {qty} шт.")
            item.setData(Qt.UserRole, (pid, qty))
            self.items_list.addItem(item)

    def _add_item(self):
        pid = self.products_combo.currentData()
        pname = self.products_combo.currentText()
        qty = self.qty_spin.value()
        item = QListWidgetItem(f"{pname} — {qty} шт.")
        item.setData(Qt.UserRole, (pid, qty))
        self.items_list.addItem(item)

    def _remove_item(self):
        row = self.items_list.currentRow()
        if row >= 0:
            self.items_list.takeItem(row)

    def save_to_db(self, order_id: Optional[int] = None) -> int:
        client_id = self.client_combo.currentData()
        status = self.status_combo.currentText()
        created_at = self.date_edit.dateTime().toPython().isoformat()
        notes = self.notes_edit.text().strip()

        conn = db_conn()
        cur = conn.cursor()
        if order_id is None:
            cur.execute(
                "INSERT INTO orders_mkl (client_id, status, created_at, notes) VALUES (?, ?, ?, ?);",
                (client_id, status, created_at, notes)
            )
            order_id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE orders_mkl SET client_id=?, status=?, created_at=?, notes=? WHERE id=?;",
                (client_id, status, created_at, notes, order_id)
            )
            cur.execute("DELETE FROM order_mkl_items WHERE order_id=?;", (order_id,))

        # Сохранение позиций
        for i in range(self.items_list.count()):
            it = self.items_list.item(i)
            pid, qty = it.data(Qt.UserRole)
            cur.execute(
                "INSERT INTO order_mkl_items (order_id, product_id, qty) VALUES (?, ?, ?);",
                (order_id, pid, qty)
            )
        conn.commit()
        conn.close()
        return order_id

class MeridianOrderDialog(QDialog):
    def __init__(self, parent=None, order_id: Optional[int] = None, number: Optional[int] = None):
        super().__init__(parent)
        self.setWindowTitle("Заказ Меридиан")
        self.setModal(True)
        self.order_id = order_id
        self.number = number

        main = QVBoxLayout(self)

        form_box = QGroupBox("Основные данные")
        form = QFormLayout(form_box)
        self.number_label = QLabel("-")
        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUS_ORDER_MER)
        self.date_edit = QDateTimeEdit(datetime.now())
        self.date_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.date_edit.setCalendarPopup(True)
        form.addRow("Номер:", self.number_label)
        form.addRow("Статус:", self.status_combo)
        form.addRow("Дата:", self.date_edit)

        items_box = QGroupBox("Товары в заказе")
        items_layout = QVBoxLayout(items_box)
        add_row = QHBoxLayout()
        self.item_name = QLineEdit()
        self.item_qty = QSpinBox()
        self.item_qty.setRange(1, 999)
        add_row.addWidget(QLabel("Название:"))
        add_row.addWidget(self.item_name, 1)
        add_row.addWidget(QLabel("Кол-во:"))
        add_row.addWidget(self.item_qty)
        self.add_item_btn = QPushButton("Добавить позицию")
        add_row.addWidget(self.add_item_btn)
        items_layout.addLayout(add_row)

        self.items_list = QListWidget()
        items_layout.addWidget(self.items_list)
        self.remove_item_btn = QPushButton("Удалить позицию")
        items_layout.addWidget(self.remove_item_btn)

        main.addWidget(form_box)
        main.addWidget(items_box)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отменить")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        main.addLayout(btns)

        if order_id:
            self._load_order(order_id)
        else:
            if number is not None:
                self.number_label.setText(str(number))

        self.add_item_btn.clicked.connect(self._add_item)
        self.remove_item_btn.clicked.connect(self._remove_item)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_order(self, order_id: int):
        conn = db_conn()
        order = conn.execute(
            "SELECT number, status, created_at FROM orders_meridian WHERE id=?;", (order_id,)
        ).fetchone()
        items = conn.execute(
            "SELECT name, qty FROM order_meridian_items WHERE order_id=? ORDER BY id;", (order_id,)
        ).fetchall()
        conn.close()

        if not order:
            return

        number, status, created_at = order
        self.number_label.setText(str(number))
        self.status_combo.setCurrentText(status)
        try:
            dt = datetime.fromisoformat(created_at)
        except Exception:
            dt = datetime.now()
        self.date_edit.setDateTime(dt)

        self.items_list.clear()
        for name, qty in items:
            item = QListWidgetItem(f"{name} — {qty} шт.")
            item.setData(Qt.UserRole, (name, qty))
            self.items_list.addItem(item)

    def _add_item(self):
        name = self.item_name.text().strip()
        if not name:
            return
        qty = self.item_qty.value()
        item = QListWidgetItem(f"{name} — {qty} шт.")
        item.setData(Qt.UserRole, (name, qty))
        self.items_list.addItem(item)
        self.item_name.clear()
        self.item_qty.setValue(1)

    def _remove_item(self):
        row = self.items_list.currentRow()
        if row >= 0:
            self.items_list.takeItem(row)

    def save_to_db(self, order_id: Optional[int] = None, number: Optional[int] = None) -> int:
        status = self.status_combo.currentText()
        created_at = self.date_edit.dateTime().toPython().isoformat()

        conn = db_conn()
        cur = conn.cursor()
        if order_id is None:
            cur.execute(
                "INSERT INTO orders_meridian (number, status, created_at) VALUES (?, ?, ?);",
                (number, status, created_at)
            )
            order_id = cur.lastrowid
        else:
            cur.execute(
                "UPDATE orders_meridian SET status=?, created_at=? WHERE id=?;",
                (status, created_at, order_id)
            )
            cur.execute("DELETE FROM order_meridian_items WHERE order_id=?;", (order_id,))

        for i in range(self.items_list.count()):
            it = self.items_list.item(i)
            name, qty = it.data(Qt.UserRole)
            cur.execute(
                "INSERT INTO order_meridian_items (order_id, name, qty) VALUES (?, ?, ?);",
                (order_id, name, qty)
            )
        conn.commit()
        conn.close()
        return order_id

# ---------- Основные страницы ----------

class MKLPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        header = QLabel("Заказы МКЛ")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Добавить заказ")
        self.edit_btn = QPushButton("Редактировать")
        self.del_btn = QPushButton("Удалить")
        self.export_btn = QPushButton("Экспорт TXT")
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(QLabel("Фильтр статуса:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("все")
        self.filter_combo.addItems(STATUS_ORDER_MKL)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self.export_btn)
        layout.addLayout(toolbar)

        # Управление сущностями
        entity_bar = QHBoxLayout()
        self.clients_btn = QPushButton("Клиенты")
        self.products_btn = QPushButton("Товары")
        entity_bar.addWidget(self.clients_btn)
        entity_bar.addWidget(self.products_btn)
        layout.addLayout(entity_bar)

        splitter = QSplitter(Qt.Vertical)
        self.orders_list = QListWidget()
        self.orders_list.setSelectionMode(QListWidget.SingleSelection)
        splitter.addWidget(self.orders_list)

        self.details = QLabel("Выберите заказ для просмотра деталей")
        self.details.setAlignment(Qt.AlignTop)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Сигналы
        self.add_btn.clicked.connect(self._add_order)
        self.edit_btn.clicked.connect(self._edit_order)
        self.del_btn.clicked.connect(self._delete_order)
        self.export_btn.clicked.connect(self._export_orders)
        self.clients_btn.clicked.connect(self._manage_clients)
        self.products_btn.clicked.connect(self._manage_products)
        self.orders_list.itemSelectionChanged.connect(self._update_details)
        self.filter_combo.currentTextChanged.connect(self.refresh)

        self.refresh()

    def refresh(self):
        self.orders_list.clear()
        status_filter = self.filter_combo.currentText()
        conn = db_conn()
        cur = conn.cursor()
        if status_filter == "все":
            rows = cur.execute("""
                SELECT o.id, c.name, c.phone, o.status, o.created_at
                FROM orders_mkl o
                JOIN clients c ON c.id=o.client_id
                ORDER BY o.created_at DESC, o.id DESC;
            """).fetchall()
        else:
            rows = cur.execute("""
                SELECT o.id, c.name, c.phone, o.status, o.created_at
                FROM orders_mkl o
                JOIN clients c ON c.id=o.client_id
                WHERE o.status=?
                ORDER BY o.created_at DESC, o.id DESC;
            """, (status_filter,)).fetchall()

        # Для каждого заказа — собрать товары
        items_map = {}
        for (oid,) in cur.execute("SELECT id FROM orders_mkl;").fetchall():
            items = cur.execute("""
                SELECT p.name, i.qty
                FROM order_mkl_items i JOIN products p ON p.id=i.product_id
                WHERE i.order_id=? ORDER BY i.id;
            """, (oid,)).fetchall()
            items_map[oid] = ", ".join([f"{n}×{q}" for n, q in items]) if items else "-"

        conn.close()

        for oid, name, phone, status, created_at in rows:
            text = f"#{oid} • {name} ({phone or '-'}) • {items_map.get(oid, '-')}\n{status} • {self._fmt_date(created_at)}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, oid)
            color = STATUS_STYLES_MKL.get(status, QColor(240, 240, 240))
            item.setBackground(color)
            self.orders_list.addItem(item)

    def _fmt_date(self, iso_str: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return iso_str

    def _update_details(self):
        it = self.orders_list.currentItem()
        if not it:
            self.details.setText("Выберите заказ для просмотра деталей")
            return
        oid = it.data(Qt.UserRole)
        conn = db_conn()
        order = conn.execute("""
            SELECT o.id, c.name, c.phone, o.status, o.created_at, o.notes
            FROM orders_mkl o JOIN clients c ON c.id=o.client_id
            WHERE o.id=?;
        """, (oid,)).fetchone()
        items = conn.execute("""
            SELECT p.name, i.qty FROM order_mkl_items i JOIN products p ON p.id=i.product_id
            WHERE i.order_id=? ORDER BY i.id;
        """, (oid,)).fetchall()
        conn.close()
        if order:
            _, name, phone, status, created_at, notes = order
            items_str = "\n".join([f"• {n} — {q} шт." for n, q in items]) or "-"
            text = f"Клиент: {name}\nТелефон: {phone or '-'}\nСтатус: {status}\nДата: {self._fmt_date(created_at)}\nЗаметки: {notes or '-'}\n\nТовары:\n{items_str}"
            self.details.setText(text)

    def _add_order(self):
        dlg = MKLOrderDialog(self)
        if dlg.exec() == QDialog.Accepted:
            oid = dlg.save_to_db(None)
            self.refresh()
            self._select_order(oid)

    def _edit_order(self):
        it = self.orders_list.currentItem()
        if not it:
            return
        oid = it.data(Qt.UserRole)
        dlg = MKLOrderDialog(self, order_id=oid)
        if dlg.exec() == QDialog.Accepted:
            dlg.save_to_db(oid)
            self.refresh()
            self._select_order(oid)

    def _delete_order(self):
        it = self.orders_list.currentItem()
        if not it:
            return
        oid = it.data(Qt.UserRole)
        if QMessageBox.question(self, "Удалить", "Удалить выбранный заказ?") == QMessageBox.Yes:
            conn = db_conn()
            conn.execute("DELETE FROM orders_mkl WHERE id=?;", (oid,))
            conn.commit()
            conn.close()
            self.refresh()

    def _export_orders(self):
        status_filter = self.filter_combo.currentText()
        conn = db_conn()
        cur = conn.cursor()
        if status_filter == "все":
            rows = cur.execute("""
                SELECT o.id, c.name, c.phone, o.status, o.created_at, o.notes
                FROM orders_mkl o JOIN clients c ON c.id=o.client_id
                ORDER BY o.created_at DESC, o.id DESC;
            """).fetchall()
        else:
            rows = cur.execute("""
                SELECT o.id, c.name, c.phone, o.status, o.created_at, o.notes
                FROM orders_mkl o JOIN clients c ON c.id=o.client_id
                WHERE o.status=? ORDER BY o.created_at DESC, o.id DESC;
            """, (status_filter,)).fetchall()
        items_map = {}
        for (oid,) in cur.execute("SELECT id FROM orders_mkl;").fetchall():
            items = cur.execute("""
                SELECT p.name, i.qty FROM order_mkl_items i JOIN products p ON p.id=i.product_id
                WHERE i.order_id=? ORDER BY i.id;
            """, (oid,)).fetchall()
            items_map[oid] = ", ".join([f"{n}×{q}" for n, q in items]) if items else "-"
        conn.close()

        lines = []
        lines.append(f"Экспорт заказов МКЛ — фильтр: {status_filter}")
        for oid, name, phone, status, created_at, notes in rows:
            lines.append(f"#{oid} | {name} | {phone or '-'} | {status} | {self._fmt_date(created_at)} | {items_map.get(oid, '-')}"
                         + (f" | Заметки: {notes}" if notes else ""))

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить TXT", f"export_mkl_{status_filter}.txt", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{filename}")

    def _manage_clients(self):
        dlg = ClientsManagerDialog(self)
        dlg.exec()
        # На случай если изменились имена клиентов — обновим список
        self.refresh()

    def _manage_products(self):
        dlg = ProductsManagerDialog(self)
        dlg.exec()
        self.refresh()

    def _select_order(self, oid: int):
        for i in range(self.orders_list.count()):
            it = self.orders_list.item(i)
            if it.data(Qt.UserRole) == oid:
                self.orders_list.setCurrentItem(it)
                break

class MeridianPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        header = QLabel("Заказы Меридиан")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Добавить заказ")
        self.edit_btn = QPushButton("Редактировать")
        self.del_btn = QPushButton("Удалить")
        self.export_btn = QPushButton("Экспорт TXT")
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(QLabel("Фильтр статуса:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("все")
        self.filter_combo.addItems(STATUS_ORDER_MER)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self.export_btn)
        layout.addLayout(toolbar)

        self.orders_list = QListWidget()
        self.orders_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.orders_list)

        self.add_btn.clicked.connect(self._add_order)
        self.edit_btn.clicked.connect(self._edit_order)
        self.del_btn.clicked.connect(self._delete_order)
        self.export_btn.clicked.connect(self._export_orders)
        self.filter_combo.currentTextChanged.connect(self.refresh)

        self.refresh()

    def refresh(self):
        self.orders_list.clear()
        status_filter = self.filter_combo.currentText()
        conn = db_conn()
        cur = conn.cursor()
        if status_filter == "все":
            rows = cur.execute("""
                SELECT id, number, status, created_at FROM orders_meridian
                ORDER BY created_at DESC, id DESC;
            """).fetchall()
        else:
            rows = cur.execute("""
                SELECT id, number, status, created_at FROM orders_meridian
                WHERE status=? ORDER BY created_at DESC, id DESC;
            """, (status_filter,)).fetchall()

        items_map = {}
        for (oid,) in cur.execute("SELECT id FROM orders_meridian;").fetchall():
            items = cur.execute("""
                SELECT name, qty FROM order_meridian_items WHERE order_id=? ORDER BY id;
            """, (oid,)).fetchall()
            items_map[oid] = ", ".join([f"{n}×{q}" for n, q in items]) if items else "-"

        conn.close()

        for oid, number, status, created_at in rows:
            text = f"№{number} • {items_map.get(oid, '-')}\n{status} • {self._fmt_date(created_at)}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, (oid, number))
            color = STATUS_STYLES_MER.get(status, QColor(240, 240, 240))
            item.setBackground(color)
            self.orders_list.addItem(item)

    def _fmt_date(self, iso_str: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return iso_str

    def _next_number(self) -> int:
        conn = db_conn()
        row = conn.execute("SELECT MAX(number) FROM orders_meridian;").fetchone()
        conn.close()
        mx = row[0] if row and row[0] is not None else 0
        return mx + 1

    def _add_order(self):
        number = self._next_number()
        dlg = MeridianOrderDialog(self, number=number)
        if dlg.exec() == QDialog.Accepted:
            oid = dlg.save_to_db(None, number)
            self.refresh()
            self._select_order(oid)

    def _edit_order(self):
        it = self.orders_list.currentItem()
        if not it:
            return
        oid, number = it.data(Qt.UserRole)
        dlg = MeridianOrderDialog(self, order_id=oid)
        if dlg.exec() == QDialog.Accepted:
            dlg.save_to_db(order_id=oid)
            self.refresh()
            self._select_order(oid)

    def _delete_order(self):
        it = self.orders_list.currentItem()
        if not it:
            return
        oid, number = it.data(Qt.UserRole)
        if QMessageBox.question(self, "Удалить", f"Удалить заказ №{number}?") == QMessageBox.Yes:
            conn = db_conn()
            conn.execute("DELETE FROM orders_meridian WHERE id=?;", (oid,))
            conn.commit()
            conn.close()
            self.refresh()

    def _export_orders(self):
        status_filter = self.filter_combo.currentText()
        conn = db_conn()
        cur = conn.cursor()
        if status_filter == "все":
            rows = cur.execute("""
                SELECT id, number, status, created_at FROM orders_meridian
                ORDER BY created_at DESC, id DESC;
            """).fetchall()
        else:
            rows = cur.execute("""
                SELECT id, number, status, created_at FROM orders_meridian
                WHERE status=? ORDER BY created_at DESC, id DESC;
            """, (status_filter,)).fetchall()
        items_map = {}
        for (oid,) in cur.execute("SELECT id FROM orders_meridian;").fetchall():
            items = cur.execute("""
                SELECT name, qty FROM order_meridian_items WHERE order_id=? ORDER BY id;
            """, (oid,)).fetchall()
            items_map[oid] = ", ".join([f"{n}×{q}" for n, q in items]) if items else "-"
        conn.close()

        lines = []
        lines.append(f"Экспорт заказов Меридиан — фильтр: {status_filter}")
        for oid, number, status, created_at in rows:
            lines.append(f"№{number} | {status} | {self._fmt_date(created_at)} | {items_map.get(oid, '-')}")

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить TXT", f"export_meridian_{status_filter}.txt", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{filename}")

    def _select_order(self, oid: int):
        for i in range(self.orders_list.count()):
            it = self.orders_list.item(i)
            if it.data(Qt.UserRole)[0] == oid:
                self.orders_list.setCurrentItem(it)
                break

class ClientsManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Клиенты")
        self.setModal(True)

        main = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.del_btn = QPushButton("Удалить")
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        main.addLayout(toolbar)

        self.list = QListWidget()
        main.addWidget(self.list)

        self.add_btn.clicked.connect(self._add)
        self.edit_btn.clicked.connect(self._edit)
        self.del_btn.clicked.connect(self._delete)

        self.refresh()

    def refresh(self):
        self.list.clear()
        conn = db_conn()
        rows = conn.execute("SELECT id, name, phone FROM clients ORDER BY name;").fetchall()
        conn.close()
        for cid, name, phone in rows:
            it = QListWidgetItem(f"{name} ({phone or '-'})")
            it.setData(Qt.UserRole, (cid, name, phone))
            self.list.addItem(it)

    def _add(self):
        dlg = ClientDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, phone = dlg.get_data()
            if not name:
                return
            conn = db_conn()
            conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?);", (name, phone))
            conn.commit()
            conn.close()
            self.refresh()

    def _edit(self):
        it = self.list.currentItem()
        if not it:
            return
        cid, name, phone = it.data(Qt.UserRole)
        dlg = ClientDialog(self, (cid, name, phone))
        if dlg.exec() == QDialog.Accepted:
            name2, phone2 = dlg.get_data()
            conn = db_conn()
            conn.execute("UPDATE clients SET name=?, phone=? WHERE id=?;", (name2, phone2, cid))
            conn.commit()
            conn.close()
            self.refresh()

    def _delete(self):
        it = self.list.currentItem()
        if not it:
            return
        cid, name, _ = it.data(Qt.UserRole)
        if QMessageBox.question(self, "Удалить", f"Удалить клиента «{name}»?\nВсе его заказы будут удалены.") == QMessageBox.Yes:
            conn = db_conn()
            conn.execute("DELETE FROM clients WHERE id=?;", (cid,))
            conn.commit()
            conn.close()
            self.refresh()

class ProductsManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Товары")
        self.setModal(True)

        main = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.del_btn = QPushButton("Удалить")
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        main.addLayout(toolbar)

        self.list = QListWidget()
        main.addWidget(self.list)

        self.add_btn.clicked.connect(self._add)
        self.edit_btn.clicked.connect(self._edit)
        self.del_btn.clicked.connect(self._delete)

        self.refresh()

    def refresh(self):
        self.list.clear()
        conn = db_conn()
        rows = conn.execute("SELECT id, name, price FROM products ORDER BY name;").fetchall()
        conn.close()
        for pid, name, price in rows:
            it = QListWidgetItem(f"{name} — {price:.2f} ₽")
            it.setData(Qt.UserRole, (pid, name, price))
            self.list.addItem(it)

    def _add(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, price = dlg.get_data()
            if not name:
                return
            conn = db_conn()
            conn.execute("INSERT INTO products (name, price) VALUES (?, ?);", (name, price))
            conn.commit()
            conn.close()
            self.refresh()

    def _edit(self):
        it = self.list.currentItem()
        if not it:
            return
        pid, name, price = it.data(Qt.UserRole)
        dlg = ProductDialog(self, (pid, name, price))
        if dlg.exec() == QDialog.Accepted:
            name2, price2 = dlg.get_data()
            conn = db_conn()
            conn.execute("UPDATE products SET name=?, price=? WHERE id=?;", (name2, price2, pid))
            conn.commit()
            conn.close()
            self.refresh()

    def _delete(self):
        it = self.list.currentItem()
        if not it:
            return
        pid, name, _ = it.data(Qt.UserRole)
        if QMessageBox.question(self, "Удалить", f"Удалить товар «{name}»?\nОн исчезнет из заказов.") == QMessageBox.Yes:
            conn = db_conn()
            conn.execute("DELETE FROM products WHERE id=?;", (pid,))
            conn.commit()
            conn.close()
            self.refresh()

# ---------- Главное окно ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        self.header = QLabel(APP_TITLE)
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont("", 18, QFont.Bold))
        root.addWidget(self.header)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # Стартовая страница
        start = QWidget()
        sv = QVBoxLayout(start)
        sv.addStretch(1)
        btns = QHBoxLayout()
        self.mkl_btn = QPushButton("Заказы МКЛ")
        self.mer_btn = QPushButton("Заказы Меридиан")
        self.set_btn = QPushButton("Настройки")
        self.mkl_btn.setMinimumHeight(60)
        self.mer_btn.setMinimumHeight(60)
        self.set_btn.setMinimumHeight(60)
        btns.addWidget(self.mkl_btn)
        btns.addWidget(self.mer_btn)
        btns.addWidget(self.set_btn)
        sv.addLayout(btns)
        sv.addStretch(1)

        # Страницы
        self.page_mkl = MKLPage()
        self.page_mer = MeridianPage()
        self.page_settings = SettingsPage(self)

        self.stack.addWidget(start)        # index 0
        self.stack.addWidget(self.page_mkl)  # index 1
        self.stack.addWidget(self.page_mer)  # index 2
        self.stack.addWidget(self.page_settings)  # index 3

        # Сигналы
        self.mkl_btn.clicked.connect(lambda: self.switch_page(1))
        self.mer_btn.clicked.connect(lambda: self.switch_page(2))
        self.set_btn.clicked.connect(lambda: self.switch_page(3))

        # Меню для темы
        theme_menu = self.menuBar().addMenu("Тема")
        self.act_light = QAction("Светлая", self, checkable=True)
        self.act_dark = QAction("Тёмная", self, checkable=True)
        theme_group = [self.act_light, self.act_dark]
        for a in theme_group:
            theme_menu.addAction(a)
        self.act_dark.setChecked(True)
        self.apply_theme("dark")
        self.act_light.triggered.connect(lambda _: self.apply_theme("light"))
        self.act_dark.triggered.connect(lambda _: self.apply_theme("dark"))

        # Иконки (используем стандартные Qt, чтобы не добавлять бинарные ресурсы)
        self.mkl_btn.setIcon(QIcon.fromTheme("view-list"))
        self.mer_btn.setIcon(QIcon.fromTheme("view-list"))
        self.set_btn.setIcon(QIcon.fromTheme("preferences-system"))

    def switch_page(self, index: int):
        # Анимация плавного появления страницы
        current = self.stack.currentWidget()
        self.stack.setCurrentIndex(index)
        target = self.stack.currentWidget()
        target.setGraphicsEffect(None)
        anim = QPropertyAnimation(target, b"geometry", self)
        rect = target.geometry()
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(QRect(rect.x() + 20, rect.y(), rect.width(), rect.height()))
        anim.setEndValue(rect)
        anim.start()

    def apply_theme(self, theme: str):
        if theme == "dark":
            QApplication.instance().setStyleSheet(DARK_QSS)
            self.act_dark.setChecked(True)
            self.act_light.setChecked(False)
        else:
            QApplication.instance().setStyleSheet(LIGHT_QSS)
            self.act_dark.setChecked(False)
            self.act_light.setChecked(True)

class SettingsPage(QWidget):
    def __init__(self, main: MainWindow):
        super().__init__(main)
        self.main = main
        layout = QVBoxLayout(self)
        header = QLabel("Настройки")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(header)

        # Переключение темы
        theme_box = QGroupBox("Оформление")
        theme_layout = QHBoxLayout(theme_box)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмная", "Светлая"])
        self.theme_combo.setCurrentIndex(0)
        apply_btn = QPushButton("Применить")
        theme_layout.addWidget(QLabel("Тема:"))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addWidget(apply_btn)
        layout.addWidget(theme_box)

        # Имя/логотип (заглушка, т.к. бинарные ресурсы не добавляем)
        info_box = QGroupBox("Информация")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel("Название компании: УссурОЧки.рф"))
        info_layout.addWidget(QLabel("Локальное хранение данных: SQLite (файл ussurochki_local.db)"))
        layout.addWidget(info_box)

        layout.addStretch(1)

        apply_btn.clicked.connect(self._apply_theme)

    def _apply_theme(self):
        theme = self.theme_combo.currentText()
        self.main.apply_theme("dark" if theme == "Тёмная" else "light")

# ---------- Точка входа ----------

def main():
    ensure_db()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()