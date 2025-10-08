import os
import sys
import sqlite3
import zipfile
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# NOTE: This app uses only PySide6 (Qt) for UI and sqlite3 from the stdlib.
# UI strings are Russian; export uses Sph/Cyl/Ax/BC/D in English and "Количество" in Russian.

try:
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QAction, QIcon, QPalette, QColor
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTabWidget, QFileDialog, QMessageBox, QLineEdit, QComboBox,
        QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
        QFormLayout, QToolBar, QStatusBar
    )
except Exception as e:
    sys.stderr.write(
        "PySide6 is required to run this application.\n"
        "Install with: python -m pip install pyside6\n"
        f"Import error: {e}\n"
    )
    raise


APP_NAME = "УссурОЧки.рф"
MKL_STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]
MER_STATUSES = ["Не заказан", "Заказан"]


def app_dirs() -> Dict[str, str]:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    root = os.path.join(base, "Ussurochki")
    data = os.path.join(root, "data")
    exports = os.path.join(root, "exports")
    backups = os.path.join(root, "backups")
    logs = os.path.join(root, "logs")
    for d in (root, data, exports, backups, logs):
        os.makedirs(d, exist_ok=True)
    return {"root": root, "data": data, "exports": exports, "backups": backups, "logs": logs}


DIRS = app_dirs()
DB_PATH = os.path.join(DIRS["data"], "app.db")


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_version(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        );
        INSERT OR IGNORE INTO schema_version(id, version) VALUES (1, 0);

        CREATE TABLE IF NOT EXISTS clients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products_mkl(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products_meridian(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS orders_mkl(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS order_items_mkl(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            eye TEXT NOT NULL,                  -- OD / OS
            sph REAL NOT NULL,                  -- -30..+30, step 0.25
            cyl REAL,                           -- -10..+10, step 0.25 (optional)
            ax INTEGER,                         -- 0..180 (optional, only with cyl)
            bc REAL,                            -- 8.0..9.0, step 0.1 (optional)
            quantity INTEGER NOT NULL,          -- 1..20
            FOREIGN KEY(order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products_mkl(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS orders_meridian(
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- номер заказа
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items_meridian(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            eye TEXT NOT NULL,
            sph REAL NOT NULL,
            cyl REAL,
            ax INTEGER,
            d INTEGER,                           -- 45..90, step 5 (optional)
            quantity INTEGER NOT NULL,           -- 1..20
            FOREIGN KEY(order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products_meridian(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    # Initialize default settings if not set
    defaults = {
        "theme": "system",              # system|light|dark
        "export_folder": DIRS["exports"],
        "export_show_eye": "0",
        "export_show_bc_mkl": "0",
        "export_aggregate": "1"
    }
    for k, v in defaults.items():
        cur = conn.execute("SELECT 1 FROM settings WHERE key = ?", (k,))
        if cur.fetchone() is None:
            conn.execute("INSERT INTO settings(key, value) VALUES (?,?)", (k, v))
    conn.commit()


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_phone(s: str) -> str:
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+{}".format(digits)
    if digits.startswith("+7") and len(digits) == 12:
        return digits
    # fallback: return original trimmed
    return s.strip()


def get_setting(conn: sqlite3.Connection, key: str, default: Optional[str] = None) -> str:
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    if row is None:
        return default if default is not None else ""
    return row["value"]


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def ensure_product(conn: sqlite3.Connection, table: str, name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Название товара не может быть пустым")
    if table not in ("products_mkl", "products_meridian"):
        raise ValueError("Неверная таблица товаров")
    cur = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute(f"INSERT INTO {table}(name) VALUES(?)", (name,))
    conn.commit()
    return cur.lastrowid


def ensure_client(conn: sqlite3.Connection, full_name: str, phone: str) -> int:
    full_name = full_name.strip()
    phone_norm = normalize_phone(phone)
    if not full_name:
        raise ValueError("ФИО клиента обязательно")
    # Try to find by normalized phone if valid
    if phone_norm.startswith("+7") and len(phone_norm) == 12:
        cur = conn.execute("SELECT id FROM clients WHERE phone = ?", (phone_norm,))
        row = cur.fetchone()
        if row:
            # Update name if changed
            conn.execute(
                "UPDATE clients SET full_name=?, updated_at=? WHERE id=?",
                (full_name, now_iso(), row["id"]),
            )
            conn.commit()
            return row["id"]
    # Create new
    cur = conn.execute(
        "INSERT INTO clients(full_name, phone, created_at, updated_at) VALUES (?,?,?,?)",
        (full_name, phone_norm, now_iso(), now_iso()),
    )
    conn.commit()
    return cur.lastrowid


def float_to_str(val: float) -> str:
    return f"{val:.2f}"


def export_mkl_by_product(conn: sqlite3.Connection, status: str) -> str:
    export_folder = get_setting(conn, "export_folder", DIRS["exports"]) or DIRS["exports"]
    show_eye = get_setting(conn, "export_show_eye", "0") == "1"
    show_bc = get_setting(conn, "export_show_bc_mkl", "0") == "1"
    aggregate = get_setting(conn, "export_aggregate", "1") == "1"

    # Fetch items joined with product names and order status
    cur = conn.execute(
        """
        SELECT p.name AS product_name, i.sph, i.cyl, i.ax, i.bc, i.eye, i.quantity
        FROM order_items_mkl i
        JOIN orders_mkl o ON o.id = i.order_id
        JOIN products_mkl p ON p.id = i.product_id
        WHERE o.status = ?
        """,
        (status,),
    )
    rows = cur.fetchall()

    # Group by product_name
    from collections import defaultdict

    grouped: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        grouped[r["product_name"]].append(r)

    # Build lines
    lines: List[str] = []
    for product in sorted(grouped.keys(), key=lambda s: s.lower()):
        lines.append(product)
        specs: List[Tuple] = []
        for r in grouped[product]:
            sph = r["sph"]
            cyl = r["cyl"]
            ax = r["ax"]
            bc = r["bc"]
            eye = r["eye"]
            qty = r["quantity"]

            parts: List[str] = []
            parts.append(f"Sph: {float_to_str(sph)}")
            if cyl is not None:
                parts.append(f"Cyl: {float_to_str(cyl)}")
                if ax is not None:
                    parts.append(f"Ax: {int(ax)}")
            if show_bc and (bc is not None):
                parts.append(f"BC: {float_to_str(bc)}")
            if show_eye:
                parts.append(f"Глаз: {eye}")
            parts.append(f"Количество: {int(qty)}")

            specs.append(tuple(parts))

        if aggregate:
            from collections import Counter
            cnt: Counter = Counter()
            for parts in specs:
                # Extract qty at the end
                # parts like ("Sph: -2.00","Cyl: -0.75","Ax: 90","BC: 8.6","Глаз: OD","Количество: 2")
                key = tuple(p for p in parts if not p.startswith("Количество:"))
                qty_str = next(p for p in parts if p.startswith("Количество:"))
                qty = int(qty_str.split(":")[1].strip())
                cnt[key] += qty
            for key, total_qty in cnt.items():
                line = " ".join(key + (f"Количество: {total_qty}",))
                lines.append(line)
        else:
            for parts in specs:
                lines.append(" ".join(parts))
        lines.append("")  # blank line between products

    if lines and lines[-1] == "":
        lines.pop()

    date_str = datetime.now().strftime("%Y%m%d")
    file_name = f"mkl_{status.lower()}_{date_str}_by-product.txt"
    file_path = os.path.join(export_folder, file_name)

    # Ensure folder exists
    os.makedirs(export_folder, exist_ok=True)

    # Write UTF-8 with BOM and CRLF
    with open(file_path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        for line in lines:
            f.write(line + "\r\n")

    return file_path


def export_meridian_notordered(conn: sqlite3.Connection) -> str:
    export_folder = get_setting(conn, "export_folder", DIRS["exports"]) or DIRS["exports"]
    show_eye = get_setting(conn, "export_show_eye", "0") == "1"
    aggregate = get_setting(conn, "export_aggregate", "1") == "1"

    cur = conn.execute(
        """
        SELECT p.name AS product_name, i.sph, i.cyl, i.ax, i.d, i.eye, i.quantity
        FROM order_items_meridian i
        JOIN orders_meridian o ON o.id = i.order_id
        JOIN products_meridian p ON p.id = i.product_id
        WHERE o.status = 'Не заказан'
        """
    )
    rows = cur.fetchall()

    from collections import defaultdict
    grouped: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        grouped[r["product_name"]].append(r)

    lines: List[str] = []
    for product in sorted(grouped.keys(), key=lambda s: s.lower()):
        lines.append(product)
        specs: List[Tuple] = []
        for r in grouped[product]:
            sph = r["sph"]
            cyl = r["cyl"]
            ax = r["ax"]
            d = r["d"]
            eye = r["eye"]
            qty = r["quantity"]

            parts: List[str] = []
            parts.append(f"Sph: {float_to_str(sph)}")
            if cyl is not None:
                parts.append(f"Cyl: {float_to_str(cyl)}")
                if ax is not None:
                    parts.append(f"Ax: {int(ax)}")
            if d is not None:
                parts.append(f"D: {int(d)}")
            if show_eye:
                parts.append(f"Глаз: {eye}")
            parts.append(f"Количество: {int(qty)}")
            specs.append(tuple(parts))

        if aggregate:
            from collections import Counter
            cnt: Counter = Counter()
            for parts in specs:
                key = tuple(p for p in parts if not p.startswith("Количество:"))
                qty_str = next(p for p in parts if p.startswith("Количество:"))
                qty = int(qty_str.split(":")[1].strip())
                cnt[key] += qty
            for key, total_qty in cnt.items():
                line = " ".join(key + (f"Количество: {total_qty}",))
                lines.append(line)
        else:
            for parts in specs:
                lines.append(" ".join(parts))
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    date_str = datetime.now().strftime("%Y%m%d")
    file_name = f"meridian_notordered_{date_str}.txt"
    file_path = os.path.join(export_folder, file_name)
    os.makedirs(export_folder, exist_ok=True)
    with open(file_path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        for line in lines:
            f.write(line + "\r\n")
    return file_path


def create_dark_palette() -> QPalette:
    palette = QPalette()
    base = QColor(37, 37, 38)
    window = QColor(45, 45, 48)
    text = QColor(220, 220, 220)
    link = QColor(86, 156, 214)
    button = QColor(63, 63, 70)
    highlight = QColor(0, 122, 204)
    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, window)
    palette.setColor(QPalette.ToolTipBase, text)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, button)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.Link, link)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    return palette


def is_float_close_to_zero(v: Optional[float]) -> bool:
    return v is None or abs(v) < 1e-9


class ItemRowMKL:
    def __init__(self,
                 product_cb: QComboBox,
                 eye_cb: QComboBox,
                 sph_sp: QDoubleSpinBox,
                 cyl_chk: QCheckBox,
                 cyl_sp: QDoubleSpinBox,
                 ax_sp: QSpinBox,
                 bc_chk: QCheckBox,
                 bc_sp: QDoubleSpinBox,
                 qty_sp: QSpinBox):
        self.product_cb = product_cb
        self.eye_cb = eye_cb
        self.sph_sp = sph_sp
        self.cyl_chk = cyl_chk
        self.cyl_sp = cyl_sp
        self.ax_sp = ax_sp
        self.bc_chk = bc_chk
        self.bc_sp = bc_sp
        self.qty_sp = qty_sp


class ItemRowMeridian:
    def __init__(self,
                 product_cb: QComboBox,
                 eye_cb: QComboBox,
                 sph_sp: QDoubleSpinBox,
                 cyl_chk: QCheckBox,
                 cyl_sp: QDoubleSpinBox,
                 ax_sp: QSpinBox,
                 d_chk: QCheckBox,
                 d_sp: QSpinBox,
                 qty_sp: QSpinBox):
        self.product_cb = product_cb
        self.eye_cb = eye_cb
        self.sph_sp = sph_sp
        self.cyl_chk = cyl_chk
        self.cyl_sp = cyl_sp
        self.ax_sp = ax_sp
        self.d_chk = d_chk
        self.d_sp = d_sp
        self.qty_sp = qty_sp


class OrderMKLDialog(QWidget):
    def __init__(self, conn: sqlite3.Connection, on_saved=None):
        super().__init__()
        self.setWindowTitle("Новый заказ МКЛ")
        self.conn = conn
        self.on_saved = on_saved
        self.rows: List[ItemRowMKL] = []

        # Client section
        client_box = QGroupBox("Клиент")
        form = QFormLayout()
        self.client_name = QLineEdit()
        self.client_phone = QLineEdit()
        form.addRow("ФИО:", self.client_name)
        form.addRow("Телефон:", self.client_phone)
        client_box.setLayout(form)

        # Status
        status_box = QGroupBox("Статус")
        hst = QHBoxLayout()
        self.status_cb = QComboBox()
        self.status_cb.addItems(MKL_STATUSES)
        hst.addWidget(self.status_cb)
        status_box.setLayout(hst)

        # Items table
        items_box = QGroupBox("Позиции")
        vbox_items = QVBoxLayout()
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["Товар", "Глаз", "Sph", "Cyl", "Ax", "BC", "Количество", "", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        vbox_items.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить позицию")
        self.btn_remove = QPushButton("Удалить выбранную")
        self.btn_both = QPushButton("Добавить для обоих глаз")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addWidget(self.btn_both)
        btn_row.addStretch(1)
        vbox_items.addLayout(btn_row)
        items_box.setLayout(vbox_items)

        # Save/Cancel
        ctrl = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_cancel = QPushButton("Отмена")
        ctrl.addStretch(1)
        ctrl.addWidget(self.btn_save)
        ctrl.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addWidget(client_box)
        layout.addWidget(status_box)
        layout.addWidget(items_box)
        layout.addLayout(ctrl)
        self.setLayout(layout)
        self.resize(980, 600)

        # Connections
        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove.clicked.connect(self.remove_selected_row)
        self.btn_both.clicked.connect(self.add_both_eyes)
        self.btn_save.clicked.connect(self.save_order)
        self.btn_cancel.clicked.connect(self.close)

        # Start with one row
        self.add_row()

    def add_row(self, copy_from: Optional[ItemRowMKL] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Product (editable combobox with suggestions)
        product_cb = QComboBox()
        product_cb.setEditable(True)
        self.fill_products(product_cb, "products_mkl")
        if copy_from:
            product_cb.setEditText(copy_from.product_cb.currentText())

        # Eye
        eye_cb = QComboBox()
        eye_cb.addItems(["OD", "OS"])
        if copy_from:
            eye_cb.setCurrentText(copy_from.eye_cb.currentText())

        # Sph
        sph_sp = QDoubleSpinBox()
        sph_sp.setRange(-30.0, 30.0)
        sph_sp.setSingleStep(0.25)
        sph_sp.setDecimals(2)
        sph_sp.setValue(0.00)
        if copy_from:
            sph_sp.setValue(copy_from.sph_sp.value())

        # Cyl checkbox + value
        cyl_chk = QCheckBox("есть")
        cyl_sp = QDoubleSpinBox()
        cyl_sp.setRange(-10.0, 10.0)
        cyl_sp.setSingleStep(0.25)
        cyl_sp.setDecimals(2)
        cyl_sp.setEnabled(False)
        ax_sp = QSpinBox()
        ax_sp.setRange(0, 180)
        ax_sp.setEnabled(False)

        def cyl_toggled(state):
            enabled = state == Qt.Checked
            cyl_sp.setEnabled(enabled)
            ax_sp.setEnabled(enabled)

        cyl_chk.stateChanged.connect(cyl_toggled)
        if copy_from and copy_from.cyl_chk.isChecked():
            cyl_chk.setChecked(True)
            cyl_sp.setValue(copy_from.cyl_sp.value())
            ax_sp.setValue(copy_from.ax_sp.value())

        # BC checkbox + value
        bc_chk = QCheckBox("есть")
        bc_sp = QDoubleSpinBox()
        bc_sp.setRange(8.0, 9.0)
        bc_sp.setSingleStep(0.1)
        bc_sp.setDecimals(1)
        bc_sp.setEnabled(False)

        def bc_toggled(state):
            bc_sp.setEnabled(state == Qt.Checked)

        bc_chk.stateChanged.connect(bc_toggled)
        if copy_from and copy_from.bc_chk.isChecked():
            bc_chk.setChecked(True)
            bc_sp.setValue(copy_from.bc_sp.value())

        # Quantity
        qty_sp = QSpinBox()
        qty_sp.setRange(1, 20)
        qty_sp.setValue(1)
        if copy_from:
            qty_sp.setValue(copy_from.qty_sp.value())

        # Place widgets
        self.table.setCellWidget(row, 0, product_cb)
        self.table.setCellWidget(row, 1, eye_cb)
        self.table.setCellWidget(row, 2, sph_sp)
        self.table.setCellWidget(row, 3, cyl_chk)
        self.table.setCellWidget(row, 4, ax_sp)
        self.table.setCellWidget(row, 5, bc_chk)
        self.table.setCellWidget(row, 6, qty_sp)
        # Hidden storage for the spin widgets we need access to
        self.table.setCellWidget(row, 7, cyl_sp)
        self.table.setCellWidget(row, 8, bc_sp)

        self.rows.append(ItemRowMKL(product_cb, eye_cb, sph_sp, cyl_chk, cyl_sp, ax_sp, bc_chk, bc_sp, qty_sp))

    def remove_selected_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.rows.pop(r)

    def add_both_eyes(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, APP_NAME, "Сначала выберите строку")
            return
        src = self.rows[r]
        # Duplicate row and set other eye
        self.add_row(copy_from=src)
        new_row = self.rows[-1]
        new_row.eye_cb.setCurrentText("OS" if src.eye_cb.currentText() == "OD" else "OD")

    def fill_products(self, combo: QComboBox, table: str):
        combo.clear()
        cur = self.conn.execute(f"SELECT name FROM {table} ORDER BY name COLLATE NOCASE")
        names = [r["name"] for r in cur.fetchall()]
        combo.addItems(names)

    def save_order(self):
        # Validate client
        name = self.client_name.text().strip()
        if not name:
            QMessageBox.warning(self, APP_NAME, "Заполните ФИО клиента")
            return
        phone = self.client_phone.text().strip()

        # Validate at least one row
        if not self.rows:
            QMessageBox.warning(self, APP_NAME, "Добавьте хотя бы одну позицию")
            return

        # Insert client, order, items
        try:
            client_id = ensure_client(self.conn, name, phone)
            cur = self.conn.execute(
                "INSERT INTO orders_mkl(client_id, status, created_at, updated_at) VALUES (?,?,?,?)",
                (client_id, self.status_cb.currentText(), now_iso(), now_iso()),
            )
            order_id = cur.lastrowid

            for row in self.rows:
                product_name = row.product_cb.currentText().strip()
                if not product_name:
                    raise ValueError("Пустое название товара")
                product_id = ensure_product(self.conn, "products_mkl", product_name)

                sph = round(row.sph_sp.value() / 0.25) * 0.25
                cyl = None
                ax = None
                if row.cyl_chk.isChecked():
                    cyl_value = row.cyl_sp.value()
                    cyl = round(cyl_value / 0.25) * 0.25
                    ax = row.ax_sp.value()
                bc = None
                if row.bc_chk.isChecked():
                    bc = round(row.bc_sp.value(), 1)
                qty = row.qty_sp.value()
                eye = row.eye_cb.currentText()

                self.conn.execute(
                    """
                    INSERT INTO order_items_mkl(order_id, product_id, eye, sph, cyl, ax, bc, quantity)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (order_id, product_id, eye, sph, cyl, ax, bc, qty),
                )

            self.conn.commit()
            QMessageBox.information(self, APP_NAME, "Заказ сохранён")
            self.close()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, APP_NAME, f"Ошибка сохранения: {e}")


class OrderMeridianDialog(QWidget):
    def __init__(self, conn: sqlite3.Connection, on_saved=None):
        super().__init__()
        self.setWindowTitle("Новый заказ Меридиан")
        self.conn = conn
        self.on_saved = on_saved
        self.rows: List[ItemRowMeridian] = []

        # Status
        status_box = QGroupBox("Статус")
        hst = QHBoxLayout()
        self.status_cb = QComboBox()
        self.status_cb.addItems(MER_STATUSES)
        hst.addWidget(self.status_cb)
        status_box.setLayout(hst)

        # Items
        items_box = QGroupBox("Позиции")
        vbox_items = QVBoxLayout()
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(["Товар", "Глаз", "Sph", "Cyl", "Ax", "D", "Количество", "", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        vbox_items.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить позицию")
        self.btn_remove = QPushButton("Удалить выбранную")
        self.btn_both = QPushButton("Добавить для обоих глаз")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addWidget(self.btn_both)
        btn_row.addStretch(1)
        vbox_items.addLayout(btn_row)
        items_box.setLayout(vbox_items)

        # Save/Cancel
        ctrl = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_cancel = QPushButton("Отмена")
        ctrl.addStretch(1)
        ctrl.addWidget(self.btn_save)
        ctrl.addWidget(self.btn_cancel)

        layout = QVBoxLayout()
        layout.addWidget(status_box)
        layout.addWidget(items_box)
        layout.addLayout(ctrl)
        self.setLayout(layout)
        self.resize(900, 560)

        # Connections
        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove.clicked.connect(self.remove_selected_row)
        self.btn_both.clicked.connect(self.add_both_eyes)
        self.btn_save.clicked.connect(self.save_order)
        self.btn_cancel.clicked.connect(self.close)

        self.add_row()

    def add_row(self, copy_from: Optional[ItemRowMeridian] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        product_cb = QComboBox()
        product_cb.setEditable(True)
        self.fill_products(product_cb, "products_meridian")
        if copy_from:
            product_cb.setEditText(copy_from.product_cb.currentText())

        eye_cb = QComboBox()
        eye_cb.addItems(["OD", "OS"])
        if copy_from:
            eye_cb.setCurrentText(copy_from.eye_cb.currentText())

        sph_sp = QDoubleSpinBox()
        sph_sp.setRange(-30.0, 30.0)
        sph_sp.setSingleStep(0.25)
        sph_sp.setDecimals(2)
        sph_sp.setValue(0.00)
        if copy_from:
            sph_sp.setValue(copy_from.sph_sp.value())

        cyl_chk = QCheckBox("есть")
        cyl_sp = QDoubleSpinBox()
        cyl_sp.setRange(-10.0, 10.0)
        cyl_sp.setSingleStep(0.25)
        cyl_sp.setDecimals(2)
        cyl_sp.setEnabled(False)
        ax_sp = QSpinBox()
        ax_sp.setRange(0, 180)
        ax_sp.setEnabled(False)

        def cyl_toggled(state):
            enabled = state == Qt.Checked
            cyl_sp.setEnabled(enabled)
            ax_sp.setEnabled(enabled)

        cyl_chk.stateChanged.connect(cyl_toggled)
        if copy_from and copy_from.cyl_chk.isChecked():
            cyl_chk.setChecked(True)
            cyl_sp.setValue(copy_from.cyl_sp.value())
            ax_sp.setValue(copy_from.ax_sp.value())

        d_chk = QCheckBox("есть")
        d_sp = QSpinBox()
        d_sp.setRange(45, 90)
        d_sp.setSingleStep(5)
        d_sp.setEnabled(False)

        def d_toggled(state):
            d_sp.setEnabled(state == Qt.Checked)

        d_chk.stateChanged.connect(d_toggled)
        if copy_from and copy_from.d_chk.isChecked():
            d_chk.setChecked(True)
            d_sp.setValue(copy_from.d_sp.value())

        qty_sp = QSpinBox()
        qty_sp.setRange(1, 20)
        qty_sp.setValue(1)
        if copy_from:
            qty_sp.setValue(copy_from.qty_sp.value())

        self.table.setCellWidget(row, 0, product_cb)
        self.table.setCellWidget(row, 1, eye_cb)
        self.table.setCellWidget(row, 2, sph_sp)
        self.table.setCellWidget(row, 3, cyl_chk)
        self.table.setCellWidget(row, 4, ax_sp)
        self.table.setCellWidget(row, 5, d_chk)
        self.table.setCellWidget(row, 6, qty_sp)
        self.table.setCellWidget(row, 7, cyl_sp)
        self.table.setCellWidget(row, 8, d_sp)

        self.rows.append(ItemRowMeridian(product_cb, eye_cb, sph_sp, cyl_chk, cyl_sp, ax_sp, d_chk, d_sp, qty_sp))

    def remove_selected_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.rows.pop(r)

    def add_both_eyes(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, APP_NAME, "Сначала выберите строку")
            return
        src = self.rows[r]
        self.add_row(copy_from=src)
        new_row = self.rows[-1]
        new_row.eye_cb.setCurrentText("OS" if src.eye_cb.currentText() == "OD" else "OD")

    def fill_products(self, combo: QComboBox, table: str):
        combo.clear
        cur = self.conn.execute(f"SELECT name FROM {table} ORDER BY name COLLATE NOCASE")
        names = [r["name"] for r in cur.fetchall()]
        combo.addItems(names)

    def save_order(self):
        try:
            cur = self.conn.execute(
                "INSERT INTO orders_meridian(status, created_at, updated_at) VALUES (?,?,?)",
                (self.status_cb.currentText(), now_iso(), now_iso()),
            )
            order_id = cur.lastrowid

            for row in self.rows:
                product_name = row.product_cb.currentText().strip()
                if not product_name:
                    raise ValueError("Пустое название товара")
                product_id = ensure_product(self.conn, "products_meridian", product_name)

                sph = round(row.sph_sp.value() / 0.25) * 0.25
                cyl = None
                ax = None
                if row.cyl_chk.isChecked():
                    cyl_value = row.cyl_sp.value()
                    cyl = round(cyl_value / 0.25) * 0.25
                    ax = row.ax_sp.value()
                d_val = None
                if row.d_chk.isChecked():
                    d_val = row.d_sp.value()
                qty = row.qty_sp.value()
                eye = row.eye_cb.currentText()

                self.conn.execute(
                    """
                    INSERT INTO order_items_meridian(order_id, product_id, eye, sph, cyl, ax, d, quantity)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (order_id, product_id, eye, sph, cyl, ax, d_val, qty),
                )

            self.conn.commit()
            QMessageBox.information(self, APP_NAME, "Заказ сохранён")
            self.close()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, APP_NAME, f"Ошибка сохранения: {e}")


class OrdersMKLPage(QWidget):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn

        v = QVBoxLayout()

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Статус фильтра:"))
        self.filter_status = QComboBox()
        self.filter_status.addItem("Все")
        self.filter_status.addItems(MKL_STATUSES)
        ctrl.addWidget(self.filter_status)

        self.btn_new = QPushButton("Новый заказ")
        self.btn_delete = QPushButton("Удалить")
        self.btn_export = QPushButton("Экспорт (свод по товарам)")
        ctrl.addStretch(1)
        ctrl.addWidget(self.btn_new)
        ctrl.addWidget(self.btn_delete)
        ctrl.addWidget(self.btn_export)
        v.addLayout(ctrl)

        # Orders table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Клиент", "Телефон", "Статус", "Дата", "Позиции"])
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table)

        self.setLayout(v)

        self.btn_new.clicked.connect(self.new_order)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_export.clicked.connect(self.export_grouped)
        self.filter_status.currentIndexChanged.connect(self.refresh)

        self.refresh()

    def refresh(self):
        status_filter = self.filter_status.currentText()
        if status_filter == "Все":
            cur = self.conn.execute(
                """
                SELECT o.id, c.full_name, c.phone, o.status, o.created_at,
                       (SELECT COUNT(*) FROM order_items_mkl i WHERE i.order_id = o.id) AS items
                FROM orders_mkl o
                LEFT JOIN clients c ON c.id = o.client_id
                ORDER BY o.id DESC
                """
            )
        else:
            cur = self.conn.execute(
                """
                SELECT o.id, c.full_name, c.phone, o.status, o.created_at,
                       (SELECT COUNT(*) FROM order_items_mkl i WHERE i.order_id = o.id) AS items
                FROM orders_mkl o
                LEFT JOIN clients c ON c.id = o.client_id
                WHERE o.status = ?
                ORDER BY o.id DESC
                """,
                (status_filter,),
            )
        rows = cur.fetchall()
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["full_name"] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(r["phone"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(r["status"]))
            self.table.setItem(row, 4, QTableWidgetItem(r["created_at"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(r["items"])))

    def new_order(self):
        dlg = OrderMKLDialog(self.conn, on_saved=self.refresh)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()

    def delete_selected(self):
        r = self.table.currentRow()
        if r < 0:
            return
        order_id = int(self.table.item(r, 0).text())
        if QMessageBox.question(self, APP_NAME, "Удалить заказ? Это действие нельзя отменить.") != QMessageBox.Yes:
            return
        self.conn.execute("DELETE FROM orders_mkl WHERE id = ?", (order_id,))
        self.conn.commit()
        self.refresh()

    def export_grouped(self):
        status_filter = self.filter_status.currentText()
        if status_filter == "Все":
            QMessageBox.information(self, APP_NAME, "Выберите конкретный статус для экспорта.")
            return
        path = export_mkl_by_product(self.conn, status_filter)
        QMessageBox.information(self, APP_NAME, f"Экспорт завершён:\n{path}")


class OrdersMeridianPage(QWidget):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn

        v = QVBoxLayout()
        ctrl = QHBoxLayout()
        self.btn_new = QPushButton("Новый заказ")
        self.btn_delete = QPushButton("Удалить")
        self.btn_export = QPushButton("Экспорт (Не заказан)")
        ctrl.addStretch(1)
        ctrl.addWidget(self.btn_new)
        ctrl.addWidget(self.btn_delete)
        ctrl.addWidget(self.btn_export)
        v.addLayout(ctrl)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["№ заказа", "Статус", "Дата", "Позиции"])
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table)

        self.setLayout(v)

        self.btn_new.clicked.connect(self.new_order)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_export.clicked.connect(self.export_notordered)

        self.refresh()

    def refresh(self):
        cur = self.conn.execute(
            """
            SELECT o.id, o.status, o.created_at,
                   (SELECT COUNT(*) FROM order_items_meridian i WHERE i.order_id = o.id) AS items
            FROM orders_meridian o
            ORDER BY o.id DESC
            """
        )
        rows = cur.fetchall()
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["status"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["created_at"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(r["items"])))

    def new_order(self):
        dlg = OrderMeridianDialog(self.conn, on_saved=self.refresh)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()

    def delete_selected(self):
        r = self.table.currentRow()
        if r < 0:
            return
        order_id = int(self.table.item(r, 0).text())
        if QMessageBox.question(self, APP_NAME, "Удалить заказ Меридиан? Это действие нельзя отменить.") != QMessageBox.Yes:
            return
        self.conn.execute("DELETE FROM orders_meridian WHERE id = ?", (order_id,))
        self.conn.commit()
        self.refresh()

    def export_notordered(self):
        path = export_meridian_notordered(self.conn)
        QMessageBox.information(self, APP_NAME, f"Экспорт завершён:\n{path}")


class SettingsPage(QWidget):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn

        layout = QVBoxLayout()

        # Theme
        theme_box = QGroupBox("Тема")
        hb = QHBoxLayout()
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["Системная", "Светлая", "Тёмная"])
        theme = get_setting(conn, "theme", "system")
        self.cb_theme.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(theme, 0))
        hb.addWidget(QLabel("Тема интерфейса:"))
        hb.addWidget(self.cb_theme)
        theme_box.setLayout(hb)

        # Export options
        export_box = QGroupBox("Экспорт")
        form = QFormLayout()
        self.export_folder = QLineEdit()
        self.export_folder.setText(get_setting(conn, "export_folder", DIRS["exports"]) or DIRS["exports"])
        btn_choose = QPushButton("Выбрать папку…")
        btn_choose.clicked.connect(self.choose_export_folder)
        h1 = QHBoxLayout()
        h1.addWidget(self.export_folder)
        h1.addWidget(btn_choose)

        self.chk_show_eye = QCheckBox("Показывать OD/OS (Глаз) в строках экспорта")
        self.chk_show_eye.setChecked(get_setting(conn, "export_show_eye", "0") == "1")
        self.chk_show_bc = QCheckBox("Показывать BC в экспорте МКЛ")
        self.chk_show_bc.setChecked(get_setting(conn, "export_show_bc_mkl", "0") == "1")
        self.chk_aggregate = QCheckBox("Агрегировать одинаковые спецификации (складывать количество)")
        self.chk_aggregate.setChecked(get_setting(conn, "export_aggregate", "1") == "1")

        form.addRow(QLabel("Папка для экспорта:"), QWidget())
        form.addRow(h1)
        form.addRow(self.chk_show_eye)
        form.addRow(self.chk_show_bc)
        form.addRow(self.chk_aggregate)
        export_box.setLayout(form)

        # Backup
        backup_box = QGroupBox("Резервное копирование")
        hb2 = QHBoxLayout()
        self.btn_backup = QPushButton("Сделать бэкап")
        self.btn_restore = QPushButton("Восстановить из бэкапа")
        hb2.addWidget(self.btn_backup)
        hb2.addWidget(self.btn_restore)
        backup_box.setLayout(hb2)

        # Save
        ctrl = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить настройки")
        ctrl.addStretch(1)
        ctrl.addWidget(self.btn_save)

        layout.addWidget(theme_box)
        layout.addWidget(export_box)
        layout.addWidget(backup_box)
        layout.addLayout(ctrl)
        self.setLayout(layout)

        # Connections
        self.btn_save.clicked.connect(self.save)
        self.btn_backup.clicked.connect(self.backup_db)
        self.btn_restore.clicked.connect(self.restore_db)

    def choose_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для экспорта", self.export_folder.text() or DIRS["exports"])
        if folder:
            self.export_folder.setText(folder)

    def save(self):
        idx = self.cb_theme.currentIndex()
        theme = {0: "system", 1: "light", 2: "dark"}[idx]
        set_setting(self.conn, "theme", theme)
        set_setting(self.conn, "export_folder", self.export_folder.text().strip() or DIRS["exports"])
        set_setting(self.conn, "export_show_eye", "1" if self.chk_show_eye.isChecked() else "0")
        set_setting(self.conn, "export_show_bc_mkl", "1" if self.chk_show_bc.isChecked() else "0")
        set_setting(self.conn, "export_aggregate", "1" if self.chk_aggregate.isChecked() else "0")
        QMessageBox.information(self, APP_NAME, "Настройки сохранены")

    def backup_db(self):
        # Zip DB file to backups folder
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        backup_name = f"ussurochki_{date_str}.zip"
        backup_path = os.path.join(DIRS["backups"], backup_name)
        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_PATH, arcname="app.db")
        QMessageBox.information(self, APP_NAME, f"Резервная копия создана:\n{backup_path}")

    def restore_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл бэкапа (.zip)", DIRS["backups"], "ZIP (*.zip)")
        if not path:
            return
        if QMessageBox.question(self, APP_NAME, "Восстановить из резервной копии? Текущая база будет заменена.") != QMessageBox.Yes:
            return
        # Extract app.db from zip to DB_PATH
        with zipfile.ZipFile(path, "r") as zf:
            if "app.db" not in zf.namelist():
                QMessageBox.critical(self, APP_NAME, "В бэкапе не найден файл app.db")
                return
            zf.extract("app.db", DIRS["data"])
        QMessageBox.information(self, APP_NAME, "База данных восстановлена.\nПерезапустите приложение.")

class MainWindow(QMainWindow):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 720)

        # Toolbar
        tb = QToolBar("Главное меню")
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        act_mkl = QAction("Заказы МКЛ", self)
        act_mer = QAction("Заказы Меридиан", self)
        act_set = QAction("Настройки", self)
        tb.addAction(act_mkl)
        tb.addAction(act_mer)
        tb.addAction(act_set)

        # Tabs
        self.tabs = QTabWidget()
        self.page_mkl = OrdersMKLPage(conn)
        self.page_mer = OrdersMeridianPage(conn)
        self.page_settings = SettingsPage(conn)
        self.tabs.addTab(self.page_mkl, "Заказы МКЛ")
        self.tabs.addTab(self.page_mer, "Заказы Меридиан")
        self.tabs.addTab(self.page_settings, "Настройки")
        self.setCentralWidget(self.tabs)

        # Statusbar
        self.setStatusBar(QStatusBar(self))

        act_mkl.triggered.connect(lambda: self.tabs.setCurrentWidget(self.page_mkl))
        act_mer.triggered.connect(lambda: self.tabs.setCurrentWidget(self.page_mer))
        act_set.triggered.connect(lambda: self.tabs.setCurrentWidget(self.page_settings))

        self.apply_theme()

    def apply_theme(self):
        theme = get_setting(self.conn, "theme", "system")
        app = QApplication.instance()
        app.setStyle("Fusion")
        if theme == "dark":
            app.setPalette(create_dark_palette())
        elif theme == "light":
            app.setPalette(QPalette())
        else:
            # system -> default palette (Fusion)
            app.setPalette(QPalette())


def main():
    # Create DB and migrate
    conn = connect_db()
    migrate(conn)

    app = QApplication(sys.argv)
    win = MainWindow(conn)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()