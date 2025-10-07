from typing import Optional
from PyQt5 import QtWidgets, QtCore
from database import (
    list_meridian_products,
    add_meridian_product,
    delete_meridian_product,
    create_meridian_order,
    list_meridian_orders,
    add_meridian_item,
    list_meridian_items,
    set_meridian_item_ordered,
    delete_meridian_order,
    delete_meridian_item,
)


class MeridianProductsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Товары (названия)", parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["ID", "Название"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.layout().addWidget(self.table)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Добавить")
        self.del_btn = QtWidgets.QPushButton("Удалить")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)
        self.layout().addLayout(btns)

        self.add_btn.clicked.connect(self.add_dialog)
        self.del_btn.clicked.connect(self.delete_selected)

        self.refresh()

    def current_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        return int(self.table.item(r, 0).text())

    def refresh(self):
        data = list_meridian_products()
        self.table.setRowCount(0)
        for row in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["name"]))

    def add_dialog(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Новый товар", "Название:")
        if not ok or not name.strip():
            return
        add_meridian_product(name.strip())
        self.refresh()

    def delete_selected(self):
        pid = self.current_id()
        if not pid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить товар?") == QtWidgets.QMessageBox.Yes:
            delete_meridian_product(pid)
            self.refresh()


class MeridianOrderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый заказ Меридиан")
        layout = QtWidgets.QFormLayout(self)

        self.number = QtWidgets.QLineEdit()
        layout.addRow("Номер заказа:", self.number)

        self.product_combo = QtWidgets.QComboBox()
        self._load_products()
        layout.addRow("Товар:", self.product_combo)

        self.sph = QtWidgets.QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setValue(0.0)
        layout.addRow("SPH:", self.sph)

        self.cyl = QtWidgets.QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setValue(0.0)
        layout.addRow("CYL:", self.cyl)

        self.ax = QtWidgets.QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setValue(0)
        layout.addRow("AX:", self.ax)

        self.qty = QtWidgets.QSpinBox()
        self.qty.setRange(1, 20)
        self.qty.setValue(1)
        layout.addRow("Количество:", self.qty)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def _load_products(self):
        self.product_combo.clear
        self.product_combo.clear()
        for row in list_meridian_products():
            self.product_combo.addItem(row["name"], row["name"])

    def data(self):
        return {
            "number": self.number.text().strip(),
            "name": self.product_combo.currentData(),
            "sph": float(self.sph.value()),
            "cyl": float(self.cyl.value()),
            "ax": int(self.ax.value()),
            "qty": int(self.qty.value()),
        }


class MeridianInterface(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # Top controls
        top = QtWidgets.QHBoxLayout()
        self.new_order_btn = QtWidgets.QPushButton("Новый заказ")
        self.export_btn = QtWidgets.QPushButton("Экспорт незаказанных")
        top.addWidget(self.new_order_btn)
        top.addWidget(self.export_btn)
        top.addStretch(1)
        layout.addLayout(top)

        # Split
        split = QtWidgets.QSplitter()
        left = QtWidgets.QWidget()
        left.setLayout(QtWidgets.QVBoxLayout())
        self.products_panel = MeridianProductsPanel()
        left.layout().addWidget(self.products_panel)

        right = QtWidgets.QWidget()
        right.setLayout(QtWidgets.QVBoxLayout())
        self.orders_table = QtWidgets.QTableWidget(0, 2)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Номер"])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.orders_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.orders_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self._orders_menu)
        right.layout().addWidget(self.orders_table)

        self.items_table = QtWidgets.QTableWidget(0, 7)
        self.items_table.setHorizontalHeaderLabels(["ID", "Товар", "SPH", "CYL", "AX", "Qty", "Статус"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.items_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self._items_menu)
        right.layout().addWidget(self.items_table)

        item_btns = QtWidgets.QHBoxLayout()
        self.add_item_btn = QtWidgets.QPushButton("Добавить позицию")
        self.toggle_status_btn = QtWidgets.QPushButton("Переключить статус")
        item_btns.addWidget(self.add_item_btn)
        item_btns.addWidget(self.toggle_status_btn)
        right.layout().addLayout(item_btns)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        layout.addWidget(split)

        # Connections
        self.new_order_btn.clicked.connect(self.create_order)
        self.export_btn.clicked.connect(self.export_unordered)
        self.orders_table.itemSelectionChanged.connect(self.refresh_items)
        self.add_item_btn.clicked.connect(self.add_item)
        self.toggle_status_btn.clicked.connect(self.toggle_item_status)

        self.refresh_orders()

    def current_order_id(self) -> Optional[int]:
        rows = self.orders_table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        return int(self.orders_table.item(r, 0).text())

    def current_item_id(self) -> Optional[int]:
        rows = self.items_table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        return int(self.items_table.item(r, 0).text())

    def refresh_orders(self):
        data = list_meridian_orders()
        self.orders_table.setRowCount(0)
        for row in data:
            r = self.orders_table.rowCount()
            self.orders_table.insertRow(r)
            self.orders_table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.orders_table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["number"]))
        if self.orders_table.rowCount():
            self.orders_table.selectRow(0)

    def refresh_items(self):
        oid = self.current_order_id()
        self.items_table.setRowCount(0)
        if not oid:
            return
        data = list_meridian_items(oid)
        for row in data:
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            self.items_table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.items_table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["product_name"]))
            self.items_table.setItem(r, 2, QtWidgets.QTableWidgetItem(_val(row["sph"])))
            self.items_table.setItem(r, 3, QtWidgets.QTableWidgetItem(_val(row["cyl"])))
            self.items_table.setItem(r, 4, QtWidgets.QTableWidgetItem(_val(row["ax"])))
            self.items_table.setItem(r, 5, QtWidgets.QTableWidgetItem(str(row["qty"])))
            st = "Заказан" if int(row["ordered"]) else "Не заказан"
            it = QtWidgets.QTableWidgetItem(st)
            it.setBackground(QtCore.Qt.green if int(row["ordered"]) else QtCore.Qt.yellow)
            self.items_table.setItem(r, 6, it)

    def create_order(self):
        dlg = MeridianOrderDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            d = dlg.data()
            if not d["number"]:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Номер заказа обязателен.")
                return
            oid = create_meridian_order(d["number"])
            add_meridian_item(oid, d["name"], d["sph"], d["cyl"], d["ax"], d["qty"])
            self.refresh_orders()

    def add_item(self):
        oid = self.current_order_id()
        if not oid:
            return
        # reuse dialog but ignore number
        dlg = MeridianOrderDialog(self)
        dlg.setWindowTitle("Добавить позицию")
        dlg.number.setVisible(False)
        dlg.layout().labelForField(dlg.number).setVisible(False)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            d = dlg.data()
            add_meridian_item(oid, d["name"], d["sph"], d["cyl"], d["ax"], d["qty"])
            self.refresh_items()

    def toggle_item_status(self):
        iid = self.current_item_id()
        if not iid:
            return
        # determine current
        r = self.items_table.currentRow()
        st = self.items_table.item(r, 6).text()
        new_val = 0 if st == "Заказан" else 1
        set_meridian_item_ordered(iid, bool(new_val))
        self.refresh_items()

    def delete_order(self):
        oid = self.current_order_id()
        if not oid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить заказ и позиции?") == QtWidgets.QMessageBox.Yes:
            delete_meridian_order(oid)
            self.refresh_orders()
            self.items_table.setRowCount(0)

    def delete_item(self):
        iid = self.current_item_id()
        if not iid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить позицию?") == QtWidgets.QMessageBox.Yes:
            delete_meridian_item(iid)
            self.refresh_items()

    def _orders_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_new = menu.addAction("Новый заказ")
        act_delete = menu.addAction("Удалить заказ")
        act_export = menu.addAction("Экспорт незаказанных")
        action = menu.exec_(self.orders_table.mapToGlobal(pos))
        if action == act_new:
            self.create_order()
        elif action == act_delete:
            self.delete_order()
        elif action == act_export:
            self.export_unordered()

    def _items_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_add = menu.addAction("Добавить позицию")
        act_toggle = menu.addAction("Переключить статус")
        act_delete = menu.addAction("Удалить позицию")
        action = menu.exec_(self.items_table.mapToGlobal(pos))
        if action == act_add:
            self.add_item()
        elif action == act_toggle:
            self.toggle_item_status()
        elif action == act_delete:
            self.delete_item()

    def export_unordered(self):
        # export all items with ordered=0 across all orders
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", "meridian_unordered.txt", "Text (*.txt)")
        if not path:
            return
        from database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT o.number, i.product_name, i.sph, i.cyl, i.ax, i.qty
            FROM meridian_order_items i
            JOIN meridian_orders o ON o.id = i.order_id
            WHERE i.ordered = 0
            ORDER BY o.created_at DESC, i.id
            """
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            QtWidgets.QMessageBox.information(self, "Экспорт", "Нет незаказанных позиций.")
            return
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                line = "|".join(
                    [
                        r["number"],
                        r["product_name"],
                        _val(r["sph"]),
                        _val(r["cyl"]),
                        _val(r["ax"]),
                        str(r["qty"]),
                    ]
                )
                f.write(line + "\n")
        QtWidgets.QMessageBox.information(self, "Экспорт", f"Экспортировано в файл:\n{path}")


def _val(v) -> str:
    return "" if v is None else str(v)