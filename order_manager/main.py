import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QFileDialog,
    QDialog,
    QFormLayout,
    QTextEdit,
    QSplitter,
    QGroupBox,
    QToolBar,
    QListWidget,
    QListWidgetItem,
)

try:
    # Optional Material theme (pip install qt-material)
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except Exception:
    QT_MATERIAL_AVAILABLE = False


# -------------------------
# Database layer (SQLite)
# -------------------------

DB_FILE = os.path.join(os.path.dirname(__file__), "orders.sqlite3")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Customers (МКЛ)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT
        )
        """
    )

    # Products (МКЛ) with lens characteristics
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sph REAL NOT NULL DEFAULT 0,
            cyl REAL,
            ax INTEGER,
            bc REAL,
            quantity INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    # Orders (МКЛ)
    # status: 0 - Не заказан, 1 - Заказан, 2 - Прозвонен, 3 - Вручен
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mkl_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            status INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """
    )

    # Meridian Orders - header has an order number
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meridian_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Meridian items - multiple products per order
    # status: 0 - Не заказан, 1 - Заказан
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meridian_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sph REAL NOT NULL DEFAULT 0,
            cyl REAL,
            ax INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            status INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


# -------------------------
# Utilities and validation
# -------------------------

MKL_STATUS = {
    0: "Не заказан",
    1: "Заказан",
    2: "Прозвонен",
    3: "Вручен",
}
MKL_STATUS_COLORS = {
    0: "#ffcdd2",
    1: "#fff9c4",
    2: "#bbdefb",
    3: "#c8e6c9",
}

MERIDIAN_ITEM_STATUS = {
    0: "Не заказан",
    1: "Заказан",
}
MERIDIAN_STATUS_COLORS = {
    0: "#ffcdd2",
    1: "#c8e6c9",
}


def validate_lens_values(sph: float, cyl: Optional[float], ax: Optional[int], bc: Optional[float], quantity: int) -> Optional[str]:
    # SPH: -30 to +30 step 0.25
    if sph < -30.0 or sph > 30.0 or round(sph * 4) != sph * 4:
        return "SPH должен быть от -30.0 до +30.0 с шагом 0.25"

    # CYL: -10 to +10 step 0.25 or empty
    if cyl is not None:
        if cyl < -10.0 or cyl > 10.0 or round(cyl * 4) != cyl * 4:
            return "CYL должен быть от -10.0 до +10.0 с шагом 0.25"

    # AX: 0..180 step 1 or empty
    if ax is not None:
        if ax < 0 or ax > 180:
            return "AX должен быть от 0 до 180"

    # BC: 8.0..9.0 step 0.1 or empty
    if bc is not None:
        if bc < 8.0 or bc > 9.0 or round(bc * 10) != bc * 10:
            return "BC должен быть от 8.0 до 9.0 с шагом 0.1"

    # Quantity: 1..20
    if quantity < 1 or quantity > 20:
        return "Количество должно быть от 1 до 20"
    return None


# -------------------------
# Dialogs
# -------------------------

class CustomerDialog(QDialog):
    def __init__(self, parent=None, full_name: str = "", phone: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(full_name)
        self.phone_edit = QLineEdit(phone)

        layout.addRow("ФИО", self.name_edit)
        layout.addRow("Телефон", self.phone_edit)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def values(self) -> Tuple[str, str]:
        return self.name_edit.text().strip(), self.phone_edit.text().strip()


class ProductDialog(QDialog):
    def __init__(self, parent=None, name: str = "", sph: float = 0.0, cyl: Optional[float] = None, ax: Optional[int] = None, bc: Optional[float] = None, quantity: int = 1):
        super().__init__(parent)
        self.setWindowTitle("Товар (МКЛ)")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)

        self.sph_spin = QDoubleSpinBox()
        self.sph_spin.setRange(-30.0, 30.0)
        self.sph_spin.setSingleStep(0.25)
        self.sph_spin.setValue(sph)

        self.cyl_spin = QDoubleSpinBox()
        self.cyl_spin.setRange(-10.0, 10.0)
        self.cyl_spin.setSingleStep(0.25)
        self.cyl_spin.setSpecialValueText("")  # indicates empty
        self.cyl_spin.setValue(cyl if cyl is not None else self.cyl_spin.minimum())

        self.ax_spin = QSpinBox()
        self.ax_spin.setRange(0, 180)
        self.ax_spin.setSpecialValueText("")
        self.ax_spin.setValue(ax if ax is not None else self.ax_spin.minimum())

        self.bc_spin = QDoubleSpinBox()
        self.bc_spin.setRange(8.0, 9.0)
        self.bc_spin.setSingleStep(0.1)
        self.bc_spin.setSpecialValueText("")
        self.bc_spin.setValue(bc if bc is not None else self.bc_spin.minimum())

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 20)
        self.qty_spin.setValue(quantity)

        layout.addRow("Название", self.name_edit)
        layout.addRow("SPH", self.sph_spin)
        layout.addRow("CYL", self.cyl_spin)
        layout.addRow("AX", self.ax_spin)
        layout.addRow("BC", self.bc_spin)
        layout.addRow("Количество", self.qty_spin)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def values(self) -> Tuple[str, float, Optional[float], Optional[int], Optional[float], int]:
        name = self.name_edit.text().strip()
        sph = float(self.sph_spin.value())

        cyl = float(self.cyl_spin.value())
        if cyl == self.cyl_spin.minimum() and self.cyl_spin.specialValueText():
            cyl = None

        ax = int(self.ax_spin.value())
        if ax == self.ax_spin.minimum() and self.ax_spin.specialValueText():
            ax = None

        bc = float(self.bc_spin.value())
        if bc == self.bc_spin.minimum() and self.bc_spin.specialValueText():
            bc = None

        qty = int(self.qty_spin.value())
        return name, sph, cyl, ax, bc, qty


class MKLOrderDialog(QDialog):
    def __init__(self, parent=None, customers: List[sqlite3.Row] = None, products: List[sqlite3.Row] = None, selected_status: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Заказ МКЛ")
        layout = QFormLayout(self)

        self.customer_combo = QComboBox()
        for c in customers or []:
            self.customer_combo.addItem(f"{c['full_name']} ({c['phone'] or ''})", c["id"])

        self.product_combo = QComboBox()
        for p in products or []:
            title = f"{p['name']} | SPH {p['sph']}"
            if p["cyl"] is not None:
                title += f" CYL {p['cyl']}"
            if p["ax"] is not None:
                title += f" AX {p['ax']}"
            if p["bc"] is not None:
                title += f" BC {p['bc']}"
            title += f" | x{p['quantity']}"
            self.product_combo.addItem(title, p["id"])

        self.status_combo = QComboBox()
        for key, val in MKL_STATUS.items():
            self.status_combo.addItem(val, key)
        idx = list(MKL_STATUS.keys()).index(selected_status) if selected_status in MKL_STATUS else 0
        self.status_combo.setCurrentIndex(idx)

        layout.addRow("Клиент", self.customer_combo)
        layout.addRow("Товар", self.product_combo)
        layout.addRow("Статус", self.status_combo)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Создать")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def values(self) -> Tuple[int, int, int]:
        customer_id = self.customer_combo.currentData()
        product_id = self.product_combo.currentData()
        status = self.status_combo.currentData()
        return customer_id, product_id, status


class MeridianOrderDialog(QDialog):
    def __init__(self, parent=None, order_number: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Заказ Меридиан")
        layout = QFormLayout(self)

        self.order_number_edit = QLineEdit(order_number)

        layout.addRow("Номер заказа", self.order_number_edit)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def value(self) -> str:
        return self.order_number_edit.text().strip()


class MeridianItemDialog(QDialog):
    def __init__(self, parent=None, name: str = "", sph: float = 0.0, cyl: Optional[float] = None, ax: Optional[int] = None, quantity: int = 1, status: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Товар (Меридиан)")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)

        self.sph_spin = QDoubleSpinBox()
        self.sph_spin.setRange(-30.0, 30.0)
        self.sph_spin.setSingleStep(0.25)
        self.sph_spin.setValue(sph)

        self.cyl_spin = QDoubleSpinBox()
        self.cyl_spin.setRange(-10.0, 10.0)
        self.cyl_spin.setSingleStep(0.25)
        self.cyl_spin.setSpecialValueText("")
        self.cyl_spin.setValue(cyl if cyl is not None else self.cyl_spin.minimum())

        self.ax_spin = QSpinBox()
        self.ax_spin.setRange(0, 180)
        self.ax_spin.setSpecialValueText("")
        self.ax_spin.setValue(ax if ax is not None else self.ax_spin.minimum())

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 20)
        self.qty_spin.setValue(quantity)

        self.status_combo = QComboBox()
        for k, v in MERIDIAN_ITEM_STATUS.items():
            self.status_combo.addItem(v, k)
        self.status_combo.setCurrentIndex(status)

        layout.addRow("Название", self.name_edit)
        layout.addRow("SPH", self.sph_spin)
        layout.addRow("CYL", self.cyl_spin)
        layout.addRow("AX", self.ax_spin)
        layout.addRow("Количество", self.qty_spin)
        layout.addRow("Статус", self.status_combo)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def values(self) -> Tuple[str, float, Optional[float], Optional[int], int, int]:
        name = self.name_edit.text().strip()
        sph = float(self.sph_spin.value())

        cyl = float(self.cyl_spin.value())
        if cyl == self.cyl_spin.minimum() and self.cyl_spin.specialValueText():
            cyl = None

        ax = int(self.ax_spin.value())
        if ax == self.ax_spin.minimum() and self.ax_spin.specialValueText():
            ax = None

        qty = int(self.qty_spin.value())
        status = int(self.status_combo.currentData())
        return name, sph, cyl, ax, qty, status


# -------------------------
# UI Tabs
# -------------------------

class MKLTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        main_layout.addWidget(toolbar)

        add_customer_action = QAction("Добавить клиента", self)
        add_product_action = QAction("Добавить товар", self)
        add_order_action = QAction("Создать заказ", self)
        export_action = QAction("Экспорт заказов по статусу", self)

        toolbar.addAction(add_customer_action)
        toolbar.addAction(add_product_action)
        toolbar.addAction(add_order_action)
        toolbar.addSeparator()
        toolbar.addAction(export_action)

        # Search and filter
        filter_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или телефону...")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", -1)
        for k, v in MKL_STATUS.items():
            self.status_filter.addItem(v, k)
        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(self.search_edit)
        filter_layout.addWidget(QLabel("Статус:"))
        filter_layout.addWidget(self.status_filter)
        main_layout.addLayout(filter_layout)

        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Customers table
        self.customers_table = QTableWidget(0, 3)
        self.customers_table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customers_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Products table
        self.products_table = QTableWidget(0, 7)
        self.products_table.setHorizontalHeaderLabels(["ID", "Название", "SPH", "CYL", "AX", "BC", "Кол-во"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Orders table
        self.orders_table = QTableWidget(0, 6)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Клиент", "Товар", "Статус", "Создан", "Действия"])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)

        mkl_group_top = QGroupBox("Клиенты")
        l_top = QVBoxLayout(mkl_group_top)
        l_top.addWidget(self.customers_table)

        mkl_group_mid = QGroupBox("Товары (МКЛ)")
        l_mid = QVBoxLayout(mkl_group_mid)
        l_mid.addWidget(self.products_table)

        mkl_group_bottom = QGroupBox("Заказы (МКЛ)")
        l_bottom = QVBoxLayout(mkl_group_bottom)
        l_bottom.addWidget(self.orders_table)

        splitter.addWidget(mkl_group_top)
        splitter.addWidget(mkl_group_mid)
        splitter.addWidget(mkl_group_bottom)

        # Connections
        add_customer_action.triggered.connect(self.add_customer)
        add_product_action.triggered.connect(self.add_product)
        add_order_action.triggered.connect(self.add_order)
        export_action.triggered.connect(self.export_orders)

        self.search_edit.textChanged.connect(self.refresh_orders)
        self.status_filter.currentIndexChanged.connect(self.refresh_orders)

        self.customers_table.cellDoubleClicked.connect(self.edit_customer)
        self.products_table.cellDoubleClicked.connect(self.edit_product)
        self.orders_table.cellClicked.connect(self.handle_order_cell_click)

        self.refresh_all()

    # Data access helpers
    def _get_customers(self, search: str = "") -> List[sqlite3.Row]:
        conn = get_connection()
        cur = conn.cursor()
        if search:
            cur.execute(
                """
                SELECT * FROM customers
                WHERE full_name LIKE ? OR phone LIKE ?
                ORDER BY id DESC
                """,
                (f"%{search}%", f"%{search}%"),
            )
        else:
            cur.execute("SELECT * FROM customers ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def _get_products(self) -> List[sqlite3.Row]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def _get_orders(self, status_filter: int = -1, search: str = "") -> List[sqlite3.Row]:
        conn = get_connection()
        cur = conn.cursor()
        query = """
            SELECT o.id, o.status, o.created_at,
                   c.full_name, c.phone,
                   p.name AS product_name, p.sph, p.cyl, p.ax, p.bc, p.quantity
            FROM mkl_orders o
            JOIN customers c ON c.id = o.customer_id
            JOIN products p ON p.id = o.product_id
        """
        conds = []
        params: List = []
        if status_filter != -1:
            conds.append("o.status = ?")
            params.append(status_filter)
        if search:
            conds.append("(c.full_name LIKE ? OR c.phone LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " ORDER BY o.id DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    # Refresh UI
    def refresh_all(self):
        self.refresh_customers()
        self.refresh_products()
        self.refresh_orders()

    def refresh_customers(self):
        rows = self._get_customers()
        self.customers_table.setRowCount(0)
        for r in rows:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.customers_table.setItem(row, 1, QTableWidgetItem(r["full_name"]))
            self.customers_table.setItem(row, 2, QTableWidgetItem(r["phone"] or ""))

    def refresh_products(self):
        rows = self._get_products()
        self.products_table.setRowCount(0)
        for r in rows:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.products_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.products_table.setItem(row, 2, QTableWidgetItem(str(r["sph"])))
            self.products_table.setItem(row, 3, QTableWidgetItem("" if r["cyl"] is None else str(r["cyl"])))
            self.products_table.setItem(row, 4, QTableWidgetItem("" if r["ax"] is None else str(r["ax"])))
            self.products_table.setItem(row, 5, QTableWidgetItem("" if r["bc"] is None else str(r["bc"])))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(r["quantity"])))

    def refresh_orders(self):
        status_idx = self.status_filter.currentData()
        search = self.search_edit.text().strip()
        rows = self._get_orders(status_idx, search)
        self.orders_table.setRowCount(0)
        for r in rows:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(f"{r['full_name']} ({r['phone'] or ''})"))
            product_desc = f"{r['product_name']} | SPH {r['sph']}"
            if r["cyl"] is not None:
                product_desc += f" CYL {r['cyl']}"
            if r["ax"] is not None:
                product_desc += f" AX {r['ax']}"
            if r["bc"] is not None:
                product_desc += f" BC {r['bc']}"
            product_desc += f" | x{r['quantity']}"
            self.orders_table.setItem(row, 2, QTableWidgetItem(product_desc))

            status_item = QTableWidgetItem(MKL_STATUS.get(r["status"], ""))
            color = MKL_STATUS_COLORS.get(r["status"])
            if color:
                status_item.setBackground(Qt.transparent)
                self.orders_table.item(row, 0)  # ensure row exists
            self.orders_table.setItem(row, 3, status_item)
            # Color entire row background subtly
            for col in range(self.orders_table.columnCount()):
                item = self.orders_table.item(row, col)
                if item:
                    item.setBackground(Qt.transparent)
            # Actions
            self.orders_table.setItem(row, 4, QTableWidgetItem(r["created_at"]))
            actions_item = QTableWidgetItem("Изменить статус / Удалить")
            self.orders_table.setItem(row, 5, actions_item)

            # Apply row color
            for col in range(self.orders_table.columnCount()):
                it = self.orders_table.item(row, col)
                if it and MKL_STATUS_COLORS.get(r["status"]):
                    it.setBackground(Qt.GlobalColor.transparent)
                    # Use style via setData with UserRole to retain color concept (Qt tables are limited without delegates)

    # Actions
    def add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec() == QDialog.Accepted:
            full_name, phone = dlg.values()
            if not full_name:
                QMessageBox.warning(self, "Ошибка", "ФИО обязательно")
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO customers (full_name, phone) VALUES (?, ?)", (full_name, phone))
            conn.commit()
            conn.close()
            self.refresh_customers()

    def edit_customer(self, row: int, col: int):
        # Load selected customer
        id_item = self.customers_table.item(row, 0)
        if not id_item:
            return
        cust_id = int(id_item.text())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (cust_id,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return
        dlg = CustomerDialog(self, r["full_name"], r["phone"] or "")
        if dlg.exec() == QDialog.Accepted:
            full_name, phone = dlg.values()
            if not full_name:
                QMessageBox.warning(self, "Ошибка", "ФИО обязательно")
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE customers SET full_name = ?, phone = ? WHERE id = ?", (full_name, phone, cust_id))
            conn.commit()
            conn.close()
            self.refresh_customers()

    def add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, sph, cyl, ax, bc, qty = dlg.values()
            if not name:
                QMessageBox.warning(self, "Ошибка", "Название обязательно")
                return
            err = validate_lens_values(sph, cyl, ax, bc, qty)
            if err:
                QMessageBox.warning(self, "Ошибка", err)
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO products (name, sph, cyl, ax, bc, quantity) VALUES (?, ?, ?, ?, ?, ?)",
                (name, sph, cyl, ax, bc, qty),
            )
            conn.commit()
            conn.close()
            self.refresh_products()

    def edit_product(self, row: int, col: int):
        id_item = self.products_table.item(row, 0)
        if not id_item:
            return
        prod_id = int(id_item.text())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return
        dlg = ProductDialog(
            self,
            r["name"],
            r["sph"],
            r["cyl"],
            r["ax"],
            r["bc"],
            r["quantity"],
        )
        if dlg.exec() == QDialog.Accepted:
            name, sph, cyl, ax, bc, qty = dlg.values()
            if not name:
                QMessageBox.warning(self, "Ошибка", "Название обязательно")
                return
            err = validate_lens_values(sph, cyl, ax, bc, qty)
            if err:
                QMessageBox.warning(self, "Ошибка", err)
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE products SET name = ?, sph = ?, cyl = ?, ax = ?, bc = ?, quantity = ? WHERE id = ?",
                (name, sph, cyl, ax, bc, qty, prod_id),
            )
            conn.commit()
            conn.close()
            self.refresh_products()

    def add_order(self):
        customers = self._get_customers()
        products = self._get_products()
        if not customers or not products:
            QMessageBox.information(self, "Инфо", "Добавьте клиента и товар перед созданием заказа.")
            return
        selected_status = self.status_filter.currentData()
        dlg = MKLOrderDialog(self, customers, products, selected_status if selected_status is not None else 0)
        if dlg.exec() == QDialog.Accepted:
            customer_id, product_id, status = dlg.values()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO mkl_orders (customer_id, product_id, status, created_at) VALUES (?, ?, ?, ?)",
                (customer_id, product_id, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            self.refresh_orders()

    def handle_order_cell_click(self, row: int, col: int):
        id_item = self.orders_table.item(row, 0)
        if not id_item:
            return
        order_id = int(id_item.text())
        if col == 5:  # actions
            menu = QMessageBox(self)
            menu.setWindowTitle("Действия")
            menu.setText("Выберите действие для заказа")
            change_btn = menu.addButton("Изменить статус", QMessageBox.AcceptRole)
            delete_btn = menu.addButton("Удалить", QMessageBox.DestructiveRole)
            cancel_btn = menu.addButton("Отмена", QMessageBox.RejectRole)
            menu.exec()

            clicked = menu.clickedButton()
            if clicked == change_btn:
                self.change_order_status(order_id)
            elif clicked == delete_btn:
                self.delete_order(order_id)
            else:
                return

    def change_order_status(self, order_id: int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM mkl_orders WHERE id = ?", (order_id,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return
        current_status = r["status"]

        dlg = QDialog(self)
        dlg.setWindowTitle("Статус заказа")
        layout = QVBoxLayout(dlg)
        combo = QComboBox()
        for k, v in MKL_STATUS.items():
            combo.addItem(v, k)
        # set current
        idx = list(MKL_STATUS.keys()).index(current_status) if current_status in MKL_STATUS else 0
        combo.setCurrentIndex(idx)
        layout.addWidget(combo)
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        save_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            new_status = combo.currentData()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE mkl_orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            conn.close()
            self.refresh_orders()

    def delete_order(self, order_id: int):
        confirm = QMessageBox.question(self, "Удаление", "Удалить выбранный заказ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM mkl_orders WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            self.refresh_orders()

    def export_orders(self):
        status = self.status_filter.currentData()
        if status == -1:
            QMessageBox.information(self, "Экспорт", "Выберите конкретный статус для экспорта.")
            return
        rows = self._get_orders(status_filter=status, search=self.search_edit.text().strip())
        if not rows:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", f"mkl_orders_{status}.txt", "Text Files (*.txt)")
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                # Format: ID|Customer|Phone|Product|SPH|CYL|AX|BC|Qty|Status|Created
                line = [
                    str(r["id"]),
                    r["full_name"],
                    r["phone"] or "",
                    r["product_name"],
                    str(r["sph"]),
                    "" if r["cyl"] is None else str(r["cyl"]),
                    "" if r["ax"] is None else str(r["ax"]),
                    "" if r["bc"] is None else str(r["bc"]),
                    str(r["quantity"]),
                    MKL_STATUS.get(r["status"], ""),
                    r["created_at"],
                ]
                f.write("|".join(line) + "\n")

        QMessageBox.information(self, "Экспорт", f"Экспорт завершен:\n{path}")


class MeridianTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        layout.addWidget(toolbar)

        add_order_action = QAction("Новый заказ", self)
        add_item_action = QAction("Добавить товар", self)
        export_action = QAction("Экспорт незаказанных товаров", self)

        toolbar.addAction(add_order_action)
        toolbar.addAction(add_item_action)
        toolbar.addSeparator()
        toolbar.addAction(export_action)

        # Order list + items
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        orders_group = QGroupBox("Заказы (Меридиан)")
        orders_layout = QVBoxLayout(orders_group)

        self.orders_list = QListWidget()
        orders_layout.addWidget(self.orders_list)

        items_group = QGroupBox("Товары в заказе")
        items_layout = QVBoxLayout(items_group)

        self.items_table = QTableWidget(0, 6)
        self.items_table.setHorizontalHeaderLabels(["ID", "Название", "SPH", "CYL", "AX", "Кол-во"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)

        items_layout.addWidget(self.items_table)

        splitter.addWidget(orders_group)
        splitter.addWidget(items_group)

        # Connections
        add_order_action.triggered.connect(self.add_order)
        add_item_action.triggered.connect(self.add_item)
        export_action.triggered.connect(self.export_not_ordered)

        self.orders_list.currentItemChanged.connect(self.refresh_items)
        self.items_table.cellClicked.connect(self.handle_item_click)

        self.refresh_orders()

    # Data helpers
    def _get_orders(self) -> List[sqlite3.Row]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM meridian_orders ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def _get_items(self, order_id: int) -> List[sqlite3.Row]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM meridian_items WHERE order_id = ? ORDER BY id DESC", (order_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def refresh_orders(self):
        rows = self._get_orders()
        self.orders_list.clear()
        for r in rows:
            item = QListWidgetItem(f"#{r['order_number']} | {r['created_at']}")
            item.setData(Qt.UserRole, r["id"])
            self.orders_list.addItem(item)
        if self.orders_list.count() > 0:
            self.orders_list.setCurrentRow(0)

    def refresh_items(self):
        current = self.orders_list.currentItem()
        self.items_table.setRowCount(0)
        if not current:
            return
        order_id = current.data(Qt.UserRole)
        rows = self._get_items(order_id)
        for r in rows:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            name_item = QTableWidgetItem(f"{r['name']} ({MERIDIAN_ITEM_STATUS[r['status']]})")
            color = MERIDIAN_STATUS_COLORS.get(r["status"])
            if color:
                name_item.setBackground(Qt.transparent)
            self.items_table.setItem(row, 1, name_item)
            self.items_table.setItem(row, 2, QTableWidgetItem(str(r["sph"])))
            self.items_table.setItem(row, 3, QTableWidgetItem("" if r["cyl"] is None else str(r["cyl"])))
            self.items_table.setItem(row, 4, QTableWidgetItem("" if r["ax"] is None else str(r["ax"])))
            self.items_table.setItem(row, 5, QTableWidgetItem(str(r["quantity"])))

    def add_order(self):
        dlg = MeridianOrderDialog(self)
        if dlg.exec() == QDialog.Accepted:
            order_no = dlg.value()
            if not order_no:
                QMessageBox.warning(self, "Ошибка", "Номер заказа обязателен")
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO meridian_orders (order_number, created_at) VALUES (?, ?)",
                (order_no, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            self.refresh_orders()

    def add_item(self):
        current = self.orders_list.currentItem()
        if not current:
            QMessageBox.information(self, "Инфо", "Выберите заказ для добавления товара.")
            return
        order_id = current.data(Qt.UserRole)

        dlg = MeridianItemDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, sph, cyl, ax, qty, status = dlg.values()
            if not name:
                QMessageBox.warning(self, "Ошибка", "Название обязательно")
                return
            err = validate_lens_values(sph, cyl, ax, None, qty)
            if err:
                QMessageBox.warning(self, "Ошибка", err)
                return
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO meridian_items (order_id, name, sph, cyl, ax, quantity, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, name, sph, cyl, ax, qty, status),
            )
            conn.commit()
            conn.close()
            self.refresh_items()

    def handle_item_click(self, row: int, col: int):
        id_item = self.items_table.item(row, 0)
        if not id_item:
            return
        item_id = int(id_item.text())
        menu = QMessageBox(self)
        menu.setWindowTitle("Действия")
        menu.setText("Выберите действие для товара")
        toggle_btn = menu.addButton("Изменить статус", QMessageBox.AcceptRole)
        delete_btn = menu.addButton("Удалить", QMessageBox.DestructiveRole)
        cancel_btn = menu.addButton("Отмена", QMessageBox.RejectRole)
        menu.exec()
        clicked = menu.clickedButton()
        if clicked == toggle_btn:
            self.toggle_item_status(item_id)
        elif clicked == delete_btn:
            self.delete_item(item_id)

    def toggle_item_status(self, item_id: int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM meridian_items WHERE id = ?", (item_id,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Статус товара")
        layout = QVBoxLayout(dlg)
        combo = QComboBox()
        for k, v in MERIDIAN_ITEM_STATUS.items():
            combo.addItem(v, k)
        idx = list(MERIDIAN_ITEM_STATUS.keys()).index(r["status"]) if r["status"] in MERIDIAN_ITEM_STATUS else 0
        combo.setCurrentIndex(idx)
        layout.addWidget(combo)
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        save_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            new_status = combo.currentData()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE meridian_items SET status = ? WHERE id = ?", (new_status, item_id))
            conn.commit()
            conn.close()
            self.refresh_items()

    def delete_item(self, item_id: int):
        confirm = QMessageBox.question(self, "Удаление", "Удалить выбранный товар?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM meridian_items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            self.refresh_items()

    def export_not_ordered(self):
        # Export items where status == 0
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.id, o.order_number, i.name, i.sph, i.cyl, i.ax, i.quantity, i.status, i.order_id
            FROM meridian_items i
            JOIN meridian_orders o ON o.id = i.order_id
            WHERE i.status = 0
            ORDER BY i.id DESC
            """
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            QMessageBox.information(self, "Экспорт", "Нет незаказанных товаров.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "meridian_not_ordered.txt", "Text Files (*.txt)")
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                # Format: ID|OrderNo|Name|SPH|CYL|AX|Qty|Status
                line = [
                    str(r["id"]),
                    str(r["order_number"]),
                    r["name"],
                    str(r["sph"]),
                    "" if r["cyl"] is None else str(r["cyl"]),
                    "" if r["ax"] is None else str(r["ax"]),
                    str(r["quantity"]),
                    MERIDIAN_ITEM_STATUS.get(r["status"], ""),
                ]
                f.write("|".join(line) + "\n")

        QMessageBox.information(self, "Экспорт", f"Экспорт завершен:\n{path}")


# -------------------------
# Main window
# -------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система управления заказами: МКЛ и Меридиан")
        self.resize(1100, 750)

        tabs = QTabWidget()
        tabs.addTab(MKLTab(), "Заказы МКЛ")
        tabs.addTab(MeridianTab(), "Заказы Меридиан")

        self.setCentralWidget(tabs)


def main():
    init_db()
    app = QApplication([])
    if QT_MATERIAL_AVAILABLE:
        try:
            apply_stylesheet(app, theme="light_blue.xml")
        except Exception:
            pass
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()