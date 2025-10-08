import os
import sys
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QMessageBox,
    QFormLayout, QDialog, QDialogButtonBox, QSpinBox, QDoubleSpinBox, QFileDialog,
    QListWidget, QListWidgetItem, QSplitter, QGroupBox, QTextEdit, QMenu
)

import qdarktheme

from db import init_db, fetchall, fetchone, execute, executemany, backup_db
from utils import (
    validate_phone,
    normalize_sph, normalize_cyl, normalize_ax, normalize_bc, normalize_qty,
    export_txt
)


APP_TITLE = "УссурОЧки.рф — система управления заказами"
MCL_STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]
MER_STATUSES = ["Не заказан", "Заказан"]


def info(parent, title, text):
    QMessageBox.information(parent, title, text)


def warn(parent, title, text):
    QMessageBox.warning(parent, title, text)


class ClientDialog(QDialog):
    def __init__(self, parent=None, full_name: str = "", phone: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(full_name)
        self.phone_edit = QLineEdit(phone)
        self.phone_edit.setPlaceholderText("+7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX")
        form.addRow("ФИО*", self.name_edit)
        form.addRow("Телефон", self.phone_edit)
        lay.addLayout(form)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        lay.addWidget(self.buttons)

    def get_data(self) -> Optional[Tuple[str, str]]:
        if self.exec() == QDialog.Accepted:
            name = self.name_edit.text().strip()
            phone = self.phone_edit.text().strip()
            if not name:
                warn(self, "Ошибка", "ФИО обязательно")
                return None
            if phone and not validate_phone(phone):
                warn(self, "Ошибка", "Телефон должен быть в формате +7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX")
                return None
            return name, phone
        return None


class ProductDialog(QDialog):
    def __init__(self, parent=None, name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Товар")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(name)
        form.addRow("Название*", self.name_edit)
        lay.addLayout(form)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        lay.addWidget(self.buttons)

    def get_data(self) -> Optional[str]:
        if self.exec() == QDialog.Accepted:
            name = self.name_edit.text().strip()
            if not name:
                warn(self, "Ошибка", "Название обязательно")
                return None
            return name
        return None


class MclItemEditor(QWidget):
    def __init__(self, products: List[str], parent=None, preset=None):
        super().__init__(parent)
        form = QHBoxLayout(self)
        self.product = QComboBox()
        self.product.setEditable(True)
        self.product.addItems(products)
        self.sph = QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setDecimals(2)
        self.sph.setValue(0.0)
        self.cyl = QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setDecimals(2)
        self.cyl.setSpecialValueText("")  # использовать пустое значение
        self.cyl.setValue(0.0)
        self.ax = QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setSpecialValueText("")
        self.ax.setValue(0)
        self.bc = QDoubleSpinBox()
        self.bc.setRange(8.0, 9.0)
        self.bc.setSingleStep(0.1)
        self.bc.setDecimals(1)
        self.bc.setSpecialValueText("")
        self.bc.setValue(8.0)
        self.qty = QSpinBox()
        self.qty.setRange(1, 20)
        self.qty.setValue(1)

        form.addWidget(QLabel("Товар"))
        form.addWidget(self.product, 2)
        form.addWidget(QLabel("SPH"))
        form.addWidget(self.sph)
        form.addWidget(QLabel("CYL"))
        form.addWidget(self.cyl)
        form.addWidget(QLabel("AX"))
        form.addWidget(self.ax)
        form.addWidget(QLabel("BC"))
        form.addWidget(self.bc)
        form.addWidget(QLabel("Кол-во"))
        form.addWidget(self.qty)

        if preset:
            self.product.setCurrentText(preset.get("product_name", ""))
            self.sph.setValue(float(preset.get("sph") or 0))
            if preset.get("cyl") is None:
                self.cyl.clear()
            else:
                self.cyl.setValue(float(preset.get("cyl")))
            if preset.get("ax") is None:
                self.ax.clear()
            else:
                self.ax.setValue(int(preset.get("ax")))
            if preset.get("bc") is None:
                self.bc.clear()
            else:
                self.bc.setValue(float(preset.get("bc")))
            self.qty.setValue(int(preset.get("qty") or 1))

    def value(self):
        cyl_val = None if self.cyl.text() == "" else float(self.cyl.value())
        ax_val = None if self.ax.text() == "" else int(self.ax.value())
        bc_val = None if self.bc.text() == "" else float(self.bc.value())
        return {
            "product_name": self.product.currentText().strip(),
            "sph": normalize_sph(float(self.sph.value())),
            "cyl": normalize_cyl(cyl_val),
            "ax": normalize_ax(ax_val),
            "bc": normalize_bc(bc_val),
            "qty": normalize_qty(int(self.qty.value())),
        }


class MerItemEditor(QWidget):
    def __init__(self, products: List[str], parent=None, preset=None):
        super().__init__(parent)
        form = QHBoxLayout(self)
        self.product = QComboBox()
        self.product.setEditable(True)
        self.product.addItems(products)
        self.sph = QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setDecimals(2)
        self.sph.setValue(0.0)
        self.cyl = QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setDecimals(2)
        self.cyl.setSpecialValueText("")
        self.cyl.setValue(0.0)
        self.ax = QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setSpecialValueText("")
        self.ax.setValue(0)
        self.qty = QSpinBox()
        self.qty.setRange(1, 20)
        self.qty.setValue(1)

        form.addWidget(QLabel("Товар"))
        form.addWidget(self.product, 2)
        form.addWidget(QLabel("SPH"))
        form.addWidget(self.sph)
        form.addWidget(QLabel("CYL"))
        form.addWidget(self.cyl)
        form.addWidget(QLabel("AX"))
        form.addWidget(self.ax)
        form.addWidget(QLabel("Кол-во"))
        form.addWidget(self.qty)

        if preset:
            self.product.setCurrentText(preset.get("product_name", ""))
            self.sph.setValue(float(preset.get("sph") or 0))
            if preset.get("cyl") is None:
                self.cyl.clear()
            else:
                self.cyl.setValue(float(preset.get("cyl")))
            if preset.get("ax") is None:
                self.ax.clear()
            else:
                self.ax.setValue(int(preset.get("ax")))
            self.qty.setValue(int(preset.get("qty") or 1))

    def value(self):
        cyl_val = None if self.cyl.text() == "" else float(self.cyl.value())
        ax_val = None if self.ax.text() == "" else int(self.ax.value())
        return {
            "product_name": self.product.currentText().strip(),
            "sph": normalize_sph(float(self.sph.value())),
            "cyl": normalize_cyl(cyl_val),
            "ax": normalize_ax(ax_val),
            "qty": normalize_qty(int(self.qty.value())),
        }


class OrderDialog(QDialog):
    def __init__(self, parent=None, domain: str = "mcl", clients: Optional[List[dict]] = None, products: Optional[List[str]] = None, preset=None):
        super().__init__(parent)
        self.domain = domain
        self.setWindowTitle("Заказ")
        self.resize(900, 300)
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        if domain == "mcl":
            self.client = QComboBox()
            self.client.setEditable(False)
            self.client_items = clients or []
            for c in self.client_items:
                self.client.addItem(f"{c['full_name']} ({c.get('phone') or ''})", c["id"])
            top.addWidget(QLabel("Клиент"))
            top.addWidget(self.client)
        self.status = QComboBox()
        self.status.addItems(MCL_STATUSES if domain == "mcl" else MER_STATUSES)
        top.addWidget(QLabel("Статус"))
        top.addWidget(self.status)
        lay.addLayout(top)

        self.items_box = QGroupBox("Товары")
        items_lay = QVBoxLayout(self.items_box)
        self.items_list: List[QWidget] = []
        self.products = products or []
        btns = QHBoxLayout()
        add_btn = QPushButton("Добавить позицию")
        add_btn.clicked.connect(self.add_item)
        btns.addWidget(add_btn)
        items_lay.addLayout(btns)
        self.items_container = QVBoxLayout()
        items_lay.addLayout(self.items_container)
        lay.addWidget(self.items_box)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        lay.addWidget(self.buttons)

        if preset:
            # fill preset
            if domain == "mcl":
                # set client
                idx = 0
                for i, c in enumerate(self.client_items):
                    if c["id"] == preset.get("client_id"):
                        idx = i
                        break
                self.client.setCurrentIndex(idx)
                self.status.setCurrentText(preset.get("status", "Не заказан"))
            else:
                self.status.setCurrentText(preset.get("status", "Не заказан"))
            for it in preset.get("items", []):
                self.add_item(preset=it)
        else:
            self.add_item()

    def add_item(self, preset=None):
        if self.domain == "mcl":
            w = MclItemEditor(self.products, self, preset=preset)
        else:
            w = MerItemEditor(self.products, self, preset=preset)
        self.items_container.addWidget(w)
        self.items_list.append(w)

    def get_data(self):
        if self.exec() == QDialog.Accepted:
            status = self.status.currentText()
            items = [w.value() for w in self.items_list]
            if any(not it["product_name"] for it in items):
                warn(self, "Ошибка", "Укажите название товара для каждой позиции")
                return None
            data = {"status": status, "items": items}
            if self.domain == "mcl":
                data["client_id"] = self.client.currentData()
            return data
        return None


class MclPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Search and filter
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по ФИО или телефону...")
        self.search.textChanged.connect(self.refresh_orders)
        self.filter = QComboBox()
        self.filter.addItem("Все статусы")
        self.filter.addItems(MCL_STATUSES)
        self.filter.currentIndexChanged.connect(self.refresh_orders)
        export_btn = QPushButton("Экспорт по статусу")
        export_btn.clicked.connect(self.export_by_status)
        top.addWidget(self.search, 2)
        top.addWidget(self.filter, 1)
        top.addWidget(export_btn, 1)
        layout.addLayout(top)

        # Splitter: left lists (clients, products), right orders
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_lay = QVBoxLayout(left)

        # Clients
        clients_box = QGroupBox("Клиенты")
        c_lay = QVBoxLayout(clients_box)
        self.clients_list = QListWidget()
        self.clients_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clients_list.customContextMenuRequested.connect(self.client_ctx_menu)
        c_btns = QHBoxLayout()
        add_c = QPushButton("Добавить")
        add_c.clicked.connect(self.add_client)
        c_btns.addWidget(add_c)
        c_lay.addWidget(self.clients_list)
        c_lay.addLayout(c_btns)
        left_lay.addWidget(clients_box)

        # Products
        products_box = QGroupBox("Товары")
        p_lay = QVBoxLayout(products_box)
        self.products_list = QListWidget()
        self.products_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_list.customContextMenuRequested.connect(self.product_ctx_menu)
        p_btns = QHBoxLayout()
        add_p = QPushButton("Добавить")
        add_p.clicked.connect(self.add_product)
        p_btns.addWidget(add_p)
        p_lay.addWidget(self.products_list)
        p_lay.addLayout(p_btns)
        left_lay.addWidget(products_box)

        splitter.addWidget(left)

        # Orders
        right = QWidget()
        right_lay = QVBoxLayout(right)

        btns = QHBoxLayout()
        add_o = QPushButton("Создать заказ")
        add_o.clicked.connect(self.create_order)
        btns.addWidget(add_o)
        right_lay.addLayout(btns)

        self.orders_table = QTableWidget(0, 6)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Клиент", "Телефон", "Статус", "Дата", "Позиции"])
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.order_ctx_menu)
        right_lay.addWidget(self.orders_table)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.refresh_clients()
        self.refresh_products()
        self.refresh_orders()

    # region Clients
    def refresh_clients(self):
        self.clients_list.clear()
        for c in fetchall("SELECT * FROM mcl_clients ORDER BY full_name"):
            item = QListWidgetItem(f"{c['full_name']}  [{c.get('phone') or ''}]")
            item.setData(Qt.UserRole, c)
            self.clients_list.addItem(item)

    def add_client(self):
        dlg = ClientDialog(self)
        res = dlg.get_data()
        if res:
            name, phone = res
            execute("INSERT INTO mcl_clients(full_name, phone) VALUES(?, ?)", (name, phone))
            self.refresh_clients()

    def client_ctx_menu(self, pos):
        item = self.clients_list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_act = menu.addAction("Редактировать")
        del_act = menu.addAction("Удалить")
        act = menu.exec(self.clients_list.mapToGlobal(pos))
        if act == edit_act:
            dlg = ClientDialog(self, data["full_name"], data.get("phone") or "")
            res = dlg.get_data()
            if res:
                name, phone = res
                execute("UPDATE mcl_clients SET full_name=?, phone=? WHERE id=?", (name, phone, data["id"]))
                self.refresh_clients()
                self.refresh_orders()
        elif act == del_act:
            if QMessageBox.question(self, "Удалить", "Удалить клиента и его заказы?") == QMessageBox.Yes:
                execute("DELETE FROM mcl_clients WHERE id=?", (data["id"],))
                self.refresh_clients()
                self.refresh_orders()
    # endregion

    # region Products
    def refresh_products(self):
        self.products_list.clear()
        for p in fetchall("SELECT * FROM mcl_products ORDER BY name"):
            item = QListWidgetItem(p["name"])
            item.setData(Qt.UserRole, p)
            self.products_list.addItem(item)

    def add_product(self):
        dlg = ProductDialog(self)
        name = dlg.get_data()
        if name:
            try:
                execute("INSERT INTO mcl_products(name) VALUES(?)", (name,))
            except Exception as e:
                warn(self, "Ошибка", f"Не удалось добавить товар: {e}")
            self.refresh_products()

    def product_ctx_menu(self, pos):
        item = self.products_list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_act = menu.addAction("Редактировать")
        del_act = menu.addAction("Удалить")
        act = menu.exec(self.products_list.mapToGlobal(pos))
        if act == edit_act:
            dlg = ProductDialog(self, data["name"])
            name = dlg.get_data()
            if name:
                try:
                    execute("UPDATE mcl_products SET name=? WHERE id=?", (name, data["id"]))
                except Exception as e:
                    warn(self, "Ошибка", f"Не удалось сохранить: {e}")
                self.refresh_products()
        elif act == del_act:
            if QMessageBox.question(self, "Удалить", "Удалить товар?") == QMessageBox.Yes:
                execute("DELETE FROM mcl_products WHERE id=?", (data["id"],))
                self.refresh_products()
    # endregion

    # region Orders
    def refresh_orders(self):
        text = (self.search.text() or "").strip()
        status = self.filter.currentText()
        where = []
        params = []
        if text:
            where.append("(c.full_name LIKE ? OR c.phone LIKE ?)")
            like = f"%{text}%"
            params += [like, like]
        if status != "Все статусы":
            where.append("o.status = ?")
            params.append(status)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        rows = fetchall(
            f"""
            SELECT o.id, o.status, o.created_at, c.full_name, c.phone
            FROM mcl_orders o
            JOIN mcl_clients c ON c.id = o.client_id
            {where_sql}
            ORDER BY o.created_at DESC
            """,
            params
        )
        self.orders_table.setRowCount(0)
        for r in rows:
            items = fetchall("SELECT * FROM mcl_order_items WHERE order_id=? ORDER BY id", (r["id"],))
            items_str = "; ".join(
                [f"{it['product_name']} [SPH {it['sph']}, CYL {'' if it['cyl'] is None else it['cyl']}, AX {'' if it['ax'] is None else it['ax']}, BC {'' if it['bc'] is None else it['bc']}] x{it['qty']}" for it in items]
            )
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(r["full_name"]))
            self.orders_table.setItem(row, 2, QTableWidgetItem(r.get("phone") or ""))
            status_item = QTableWidgetItem(r["status"])
            # color by status
            color = {
                "Не заказан": Qt.red,
                "Заказан": Qt.green,
                "Прозвонен": Qt.yellow,
                "Вручен": Qt.darkGreen
            }.get(r["status"], Qt.white)
            status_item.setForeground(color)
            self.orders_table.setItem(row, 3, status_item)
            self.orders_table.setItem(row, 4, QTableWidgetItem(r["created_at"]))
            self.orders_table.setItem(row, 5, QTableWidgetItem(items_str))
        self.orders_table.resizeColumnsToContents()

    def create_order(self):
        clients = fetchall("SELECT * FROM mcl_clients ORDER BY full_name")
        if not clients:
            warn(self, "Нет клиентов", "Сначала добавьте клиента")
            return
        products = [p["name"] for p in fetchall("SELECT * FROM mcl_products ORDER BY name")]
        dlg = OrderDialog(self, domain="mcl", clients=clients, products=products)
        data = dlg.get_data()
        if data:
            order_id = execute("INSERT INTO mcl_orders(client_id, status) VALUES(?, ?)", (data["client_id"], data["status"]))
            params = []
            for it in data["items"]:
                params.append(
                    (order_id, it["product_name"], it["sph"], it["cyl"], it["ax"], it["bc"], it["qty"])
                )
            if params:
                executemany(
                    "INSERT INTO mcl_order_items(order_id, product_name, sph, cyl, ax, bc, qty) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    params
                )
            self.refresh_orders()

    def order_ctx_menu(self, pos):
        row = self.orders_table.currentRow()
        if row < 0:
            return
        order_id = int(self.orders_table.item(row, 0).text())
        menu = QMenu(self)
        edit_act = menu.addAction("Редактировать")
        del_act = menu.addAction("Удалить")
        chg_stat = menu.addMenu("Сменить статус")
        for s in MCL_STATUSES:
            a = chg_stat.addAction(s)
            a.setData(s)
        act = menu.exec(self.orders_table.mapToGlobal(pos))
        if not act:
            return
        if act == edit_act:
            self.edit_order(order_id)
        elif act == del_act:
            if QMessageBox.question(self, "Удалить", "Удалить заказ?") == QMessageBox.Yes:
                execute("DELETE FROM mcl_orders WHERE id=?", (order_id,))
                self.refresh_orders()
        elif act.parentWidget() == chg_stat:
            new_status = act.data()
            execute("UPDATE mcl_orders SET status=? WHERE id=?", (new_status, order_id))
            self.refresh_orders()

    def edit_order(self, order_id: int):
        o = fetchone("SELECT * FROM mcl_orders WHERE id=?", (order_id,))
        items = fetchall("SELECT * FROM mcl_order_items WHERE order_id=? ORDER BY id", (order_id,))
        clients = fetchall("SELECT * FROM mcl_clients ORDER BY full_name")
        products = [p["name"] for p in fetchall("SELECT * FROM mcl_products ORDER BY name")]
        dlg = OrderDialog(self, domain="mcl", clients=clients, products=products, preset={"client_id": o["client_id"], "status": o["status"], "items": items})
        data = dlg.get_data()
        if data:
            execute("UPDATE mcl_orders SET client_id=?, status=? WHERE id=?", (data["client_id"], data["status"], order_id))
            execute("DELETE FROM mcl_order_items WHERE order_id=?", (order_id,))
            params = []
            for it in data["items"]:
                params.append(
                    (order_id, it["product_name"], it["sph"], it["cyl"], it["ax"], it["bc"], it["qty"])
                )
            if params:
                executemany(
                    "INSERT INTO mcl_order_items(order_id, product_name, sph, cyl, ax, bc, qty) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    params
                )
            self.refresh_orders()

    def export_by_status(self):
        status = self.filter.currentText()
        if status == "Все статусы":
            warn(self, "Выбор статуса", "Выберите конкретный статус для экспорта")
            return
        orders = fetchall(
            """
            SELECT o.id, o.status, o.created_at, c.full_name, c.phone
            FROM mcl_orders o
            JOIN mcl_clients c ON c.id = o.client_id
            WHERE o.status = ?
            ORDER BY o.created_at DESC
            """,
            (status,)
        )
        rows = []
        for o in orders:
            items = fetchall("SELECT * FROM mcl_order_items WHERE order_id=? ORDER BY id", (o["id"],))
            items_str = "; ".join(
                [f"{it['product_name']} [SPH {it['sph']}, CYL {'' if it['cyl'] is None else it['cyl']}, AX {'' if it['ax'] is None else it['ax']}, BC {'' if it['bc'] is None else it['bc']}] x{it['qty']}" for it in items]
            )
            rows.append({
                "ФИО": o["full_name"],
                "Телефон": o.get("phone") or "",
                "Товары": items_str,
                "Статус": o["status"],
                "Дата": o["created_at"]
            })
        path = self.window().export_path
        fname = export_txt(path, f"mcl_{status}", rows, ["ФИО", "Телефон", "Товары", "Статус", "Дата"])
        info(self, "Экспорт", f"Экспорт выполнен: {fname}")
    # endregion


class MeridianPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        export_btn = QPushButton("Экспорт незаказанных товаров")
        export_btn.clicked.connect(self.export_unordered)
        top.addStretch(1)
        top.addWidget(export_btn)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_lay = QVBoxLayout(left)

        products_box = QGroupBox("Товары")
        p_lay = QVBoxLayout(products_box)
        self.products_list = QListWidget()
        self.products_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_list.customContextMenuRequested.connect(self.product_ctx_menu)
        p_btns = QHBoxLayout()
        add_p = QPushButton("Добавить")
        add_p.clicked.connect(self.add_product)
        p_btns.addWidget(add_p)
        p_lay.addWidget(self.products_list)
        p_lay.addLayout(p_btns)
        left_lay.addWidget(products_box)

        splitter.addWidget(left)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        btns = QHBoxLayout()
        add_o = QPushButton("Создать заказ")
        add_o.clicked.connect(self.create_order)
        btns.addWidget(add_o)
        right_lay.addLayout(btns)

        self.orders_table = QTableWidget(0, 5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "№", "Статус", "Дата", "Позиции"])
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.order_ctx_menu)
        right_lay.addWidget(self.orders_table)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.refresh_products()
        self.refresh_orders()

    def refresh_products(self):
        self.products_list.clear()
        for p in fetchall("SELECT * FROM mer_products ORDER BY name"):
            item = QListWidgetItem(p["name"])
            item.setData(Qt.UserRole, p)
            self.products_list.addItem(item)

    def add_product(self):
        dlg = ProductDialog(self)
        name = dlg.get_data()
        if name:
            try:
                execute("INSERT INTO mer_products(name) VALUES(?)", (name,))
            except Exception as e:
                warn(self, "Ошибка", f"Не удалось добавить товар: {e}")
            self.refresh_products()

    def product_ctx_menu(self, pos):
        item = self.products_list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_act = menu.addAction("Редактировать")
        del_act = menu.addAction("Удалить")
        act = menu.exec(self.products_list.mapToGlobal(pos))
        if act == edit_act:
            dlg = ProductDialog(self, data["name"])
            name = dlg.get_data()
            if name:
                try:
                    execute("UPDATE mer_products SET name=? WHERE id=?", (name, data["id"]))
                except Exception as e:
                    warn(self, "Ошибка", f"Не удалось сохранить: {e}")
                self.refresh_products()
        elif act == del_act:
            if QMessageBox.question(self, "Удалить", "Удалить товар?") == QMessageBox.Yes:
                execute("DELETE FROM mer_products WHERE id=?", (data["id"],))
                self.refresh_products()

    def refresh_orders(self):
        rows = fetchall(
            """
            SELECT * FROM mer_orders
            ORDER BY created_at DESC
            """
        )
        self.orders_table.setRowCount(0)
        for r in rows:
            items = fetchall("SELECT * FROM mer_order_items WHERE order_id=? ORDER BY id", (r["id"],))
            items_str = "; ".join(
                [f"{it['product_name']} [SPH {it['sph']}, CYL {'' if it['cyl'] is None else it['cyl']}, AX {'' if it['ax'] is None else it['ax']}] x{it['qty']}" for it in items]
            )
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(str(r["number"])))
            status_item = QTableWidgetItem(r["status"])
            color = {"Не заказан": Qt.red, "Заказан": Qt.green}.get(r["status"], Qt.white)
            status_item.setForeground(color)
            self.orders_table.setItem(row, 2, status_item)
            self.orders_table.setItem(row, 3, QTableWidgetItem(r["created_at"]))
            self.orders_table.setItem(row, 4, QTableWidgetItem(items_str))
        self.orders_table.resizeColumnsToContents()

    def next_number(self) -> int:
        row = fetchone("SELECT MAX(number) AS m FROM mer_orders")
        m = row["m"] if row and row["m"] is not None else 0
        return int(m) + 1

    def create_order(self):
        products = [p["name"] for p in fetchall("SELECT * FROM mer_products ORDER BY name")]
        dlg = OrderDialog(self, domain="mer", products=products)
        data = dlg.get_data()
        if data:
            num = self.next_number()
            order_id = execute("INSERT INTO mer_orders(number, status) VALUES(?, ?)", (num, data["status"]))
            params = []
            for it in data["items"]:
                params.append(
                    (order_id, it["product_name"], it["sph"], it["cyl"], it["ax"], it["qty"])
                )
            if params:
                executemany(
                    "INSERT INTO mer_order_items(order_id, product_name, sph, cyl, ax, qty) VALUES(?, ?, ?, ?, ?, ?)",
                    params
                )
            self.refresh_orders()

    def order_ctx_menu(self, pos):
        row = self.orders_table.currentRow()
        if row < 0:
            return
        order_id = int(self.orders_table.item(row, 0).text())
        menu = QMenu(self)
        edit_act = menu.addAction("Редактировать")
        del_act = menu.addAction("Удалить")
        chg_stat = menu.addMenu("Сменить статус")
        for s in MER_STATUSES:
            a = chg_stat.addAction(s)
            a.setData(s)
        act = menu.exec(self.orders_table.mapToGlobal(pos))
        if not act:
            return
        if act == edit_act:
            self.edit_order(order_id)
        elif act == del_act:
            if QMessageBox.question(self, "Удалить", "Удалить заказ?") == QMessageBox.Yes:
                execute("DELETE FROM mer_orders WHERE id=?", (order_id,))
                self.refresh_orders()
        elif act.parentWidget() == chg_stat:
            new_status = act.data()
            execute("UPDATE mer_orders SET status=? WHERE id=?", (new_status, order_id))
            self.refresh_orders()

    def edit_order(self, order_id: int):
        o = fetchone("SELECT * FROM mer_orders WHERE id=?", (order_id,))
        items = fetchall("SELECT * FROM mer_order_items WHERE order_id=? ORDER BY id", (order_id,))
        products = [p["name"] for p in fetchall("SELECT * FROM mer_products ORDER BY name")]
        dlg = OrderDialog(self, domain="mer", products=products, preset={"status": o["status"], "items": items})
        data = dlg.get_data()
        if data:
            execute("UPDATE mer_orders SET status=? WHERE id=?", (data["status"], order_id))
            execute("DELETE FROM mer_order_items WHERE order_id=?", (order_id,))
            params = []
            for it in data["items"]:
                params.append(
                    (order_id, it["product_name"], it["sph"], it["cyl"], it["ax"], it["qty"])
                )
            if params:
                executemany(
                    "INSERT INTO mer_order_items(order_id, product_name, sph, cyl, ax, qty) VALUES(?, ?, ?, ?, ?, ?)",
                    params
                )
            self.refresh_orders()

    def export_unordered(self):
        orders = fetchall(
            """
            SELECT * FROM mer_orders WHERE status='Не заказан' ORDER BY created_at DESC
            """
        )
        rows = []
        for o in orders:
            items = fetchall("SELECT * FROM mer_order_items WHERE order_id=? ORDER BY id", (o["id"],))
            for it in items:
                rows.append({
                    "№": o["number"],
                    "Товар": it["product_name"],
                    "SPH": it["sph"],
                    "CYL": "" if it["cyl"] is None else it["cyl"],
                    "AX": "" if it["ax"] is None else it["ax"],
                    "Кол-во": it["qty"],
                    "Статус": o["status"]
                })
        path = self.window().export_path
        fname = export_txt(path, "mer_unordered", rows, ["№", "Товар", "SPH", "CYL", "AX", "Кол-во", "Статус"])
        info(self, "Экспорт", f"Экспорт выполнен: {fname}")


class SettingsPage(QWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        layout = QVBoxLayout(self)

        theme_box = QGroupBox("Тема интерфейса")
        t_lay = QHBoxLayout(theme_box)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        t_lay.addWidget(QLabel("Выберите тему:"))
        t_lay.addWidget(self.theme_combo)
        layout.addWidget(theme_box)

        export_box = QGroupBox("Экспорт и резервное копирование")
        e_lay = QVBoxLayout(export_box)
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(self.window().export_path)
        choose_btn = QPushButton("Выбрать папку")
        choose_btn.clicked.connect(self.choose_export_path)
        path_row.addWidget(QLabel("Папка экспорта:"))
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(choose_btn)
        e_lay.addLayout(path_row)

        backup_btn = QPushButton("Сделать резервную копию БД")
        backup_btn.clicked.connect(self.backup)
        e_lay.addWidget(backup_btn)

        layout.addWidget(export_box)
        layout.addStretch(1)

    def change_theme(self):
        theme = "light" if self.theme_combo.currentText() == "Светлая" else "dark"
        self.window().apply_theme(theme)

    def choose_export_path(self):
        d = QFileDialog.getExistingDirectory(self, "Выбор папки экспорта", self.path_edit.text() or os.getcwd())
        if d:
            self.path_edit.setText(d)
            self.window().export_path = d

    def backup(self):
        try:
            dest = backup_db(self.path_edit.text() or os.getcwd())
            info(self, "Резервное копирование", f"Создан файл: {dest}")
        except Exception as e:
            warn(self, "Ошибка", str(e))


class HomePage(QWidget):
    def __init__(self, parent=None, switch_callback=None):
        super().__init__(parent)
        self.switch_callback = switch_callback
        layout = QVBoxLayout(self)

        # Лого (если файл существует: assets/logo.png|jpg|jpeg)
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignHCenter)
        logo_path = self._find_logo_path()
        if logo_path:
            pm = QPixmap(logo_path)
            if not pm.isNull():
                # масштабируем по ширине с сохранением пропорций
                pm = pm.scaledToWidth(260, Qt.SmoothTransformation)
                logo_label.setPixmap(pm)
                layout.addSpacing(8)
                layout.addWidget(logo_label)
                layout.addSpacing(8)

        title = QLabel("УссурОЧки.рф")
        font = title.font()
        font.setPointSize(22)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignHCenter)
        subtitle = QLabel("Система управления заказами")
        subtitle.setAlignment(Qt.AlignHCenter)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        btns = QHBoxLayout()
        b1 = QPushButton("Заказы МКЛ")
        b2 = QPushButton("Заказы Меридиан")
        b3 = QPushButton("Настройки")
        for b in (b1, b2, b3):
            b.setMinimumHeight(48)
        btns.addWidget(b1)
        btns.addWidget(b2)
        btns.addWidget(b3)
        layout.addLayout(btns)
        layout.addStretch(2)

        b1.clicked.connect(lambda: self.switch_callback("mcl"))
        b2.clicked.connect(lambda: self.switch_callback("meridian"))
        b3.clicked.connect(lambda: self.switch_callback("settings"))

    def _find_logo_path(self) -> Optional[str]:
        base = os.getcwd()
        cand = [
            os.path.join(base, "assets", "logo.png"),
            os.path.join(base, "assets", "logo.jpg"),
            os.path.join(base, "assets", "logo.jpeg"),
        ]
        for p in cand:
            if os.path.exists(p):
                return p
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 700)
        init_db()

        # Default settings
        self.theme = "dark"
        self.export_path = os.path.join(os.getcwd(), "export")
        os.makedirs(self.export_path, exist_ok=True)

        # Установим иконку окна, если есть лого
        self._apply_window_icon()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home = HomePage(self, switch_callback=self.switch_page)
        self.mcl = MclPage(self)
        self.mer = MeridianPage(self)
        self.settings = SettingsPage(self, app=QApplication.instance())
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.mcl)
        self.stack.addWidget(self.mer)
        self.stack.addWidget(self.settings)

        # Toolbar actions
        toolbar = self.addToolBar("Навигация")
        toolbar.setMovable(False)
        act_home = QAction("Главная", self)
        act_mcl = QAction("МКЛ", self)
        act_mer = QAction("Меридиан", self)
        act_settings = QAction("Настройки", self)
        # Иконки в тулбар, если есть
        icon = self.windowIcon()
        if not icon.isNull():
            act_home.setIcon(icon)
            act_mcl.setIcon(icon)
            act_mer.setIcon(icon)
            act_settings.setIcon(icon)

        toolbar.addAction(act_home)
        toolbar.addAction(act_mcl)
        toolbar.addAction(act_mer)
        toolbar.addAction(act_settings)

        act_home.triggered.connect(lambda: self.switch_page("home"))
        act_mcl.triggered.connect(lambda: self.switch_page("mcl"))
        act_mer.triggered.connect(lambda: self.switch_page("meridian"))
        act_settings.triggered.connect(lambda: self.switch_page("settings"))

        self.apply_theme(self.theme)

    def apply_theme(self, theme: str):
        self.theme = theme
        if theme == "dark":
            qdarktheme.setup_theme("dark")
        else:
            qdarktheme.setup_theme("light")
        self.repaint()

    def _apply_window_icon(self):
        base = os.getcwd()
        for name in ("logo.png", "logo.jpg", "logo.jpeg"):
            p = os.path.join(base, "assets", name)
            if os.path.exists(p):
                self.setWindowIcon(QIcon(p))
                break

    def switch_page(self, page: str):
        mapping = {"home": 0, "mcl": 1, "meridian": 2, "settings": 3}
        current = self.stack.currentIndex()
        target = mapping.get(page, 0)
        if target == current:
            return

        # Simple slide animation
        old_widget = self.stack.currentWidget()
        new_widget = self.stack.widget(target)
        geom = self.stack.geometry()
        direction = 1 if target > current else -1
        new_widget.setGeometry(QRect(geom.width() * direction, 0, geom.width(), geom.height()))
        self.stack.setCurrentIndex(target)

        anim_old = QPropertyAnimation(old_widget, b"geometry")
        anim_old.setDuration(250)
        anim_old.setEasingCurve(QEasingCurve.InOutCubic)
        anim_old.setStartValue(QRect(0, 0, geom.width(), geom.height()))
        anim_old.setEndValue(QRect(-geom.width() * direction, 0, geom.width(), geom.height()))

        anim_new = QPropertyAnimation(new_widget, b"geometry")
        anim_new.setDuration(250)
        anim_new.setEasingCurve(QEasingCurve.InOutCubic)
        anim_new.setStartValue(QRect(geom.width() * direction, 0, geom.width(), geom.height()))
        anim_new.setEndValue(QRect(0, 0, geom.width(), geom.height()))

        anim_old.start()
        anim_new.start()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("УссурОЧки.рф")
    app.setOrganizationName("УссурОЧки")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()