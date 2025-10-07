from typing import Optional
from PyQt5 import QtWidgets, QtCore, QtGui
from database import (
    list_clients,
    add_client,
    update_client,
    delete_client,
    list_mkl_products,
    add_mkl_product,
    update_mkl_product,
    delete_mkl_product,
    list_mkl_orders,
    create_mkl_order,
    add_mkl_order_item,
    get_mkl_order_items,
    set_mkl_order_status,
    delete_mkl_order,
)


MKL_STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]


class ClientsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Клиенты", parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        # Search
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или телефону")
        self.search_edit.textChanged.connect(self.refresh)
        self.layout().addWidget(self.search_edit)

        # Table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.layout().addWidget(self.table)

        # Controls
        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Добавить")
        self.edit_btn = QtWidgets.QPushButton("Изменить")
        self.del_btn = QtWidgets.QPushButton("Удалить")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        self.layout().addLayout(btns)

        self.add_btn.clicked.connect(self.add_client_dialog)
        self.edit_btn.clicked.connect(self.edit_client_dialog)
        self.del_btn.clicked.connect(self.delete_selected)

        self.refresh()

    def current_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        return int(self.table.item(r, 0).text())

    def refresh(self):
        data = list_clients(self.search_edit.text())
        self.table.setRowCount(0)
        for row in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["full_name"]))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(row["phone"] or ""))

    def add_client_dialog(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Новый клиент", "ФИО:")
        if not ok or not name.strip():
            return
        phone, ok = QtWidgets.QInputDialog.getText(self, "Новый клиент", "Телефон:")
        if not ok:
            return
        add_client(name.strip(), phone.strip())
        self.refresh()

    def edit_client_dialog(self):
        cid = self.current_id()
        if not cid:
            return
        r = self.table.currentRow()
        name0 = self.table.item(r, 1).text()
        phone0 = self.table.item(r, 2).text()
        name, ok = QtWidgets.QInputDialog.getText(self, "Изменить клиента", "ФИО:", text=name0)
        if not ok or not name.strip():
            return
        phone, ok = QtWidgets.QInputDialog.getText(self, "Изменить клиента", "Телефон:", text=phone0)
        if not ok:
            return
        update_client(cid, name.strip(), phone.strip())
        self.refresh()

    def delete_selected(self):
        cid = self.current_id()
        if not cid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить клиента и связанные заказы?") == QtWidgets.QMessageBox.Yes:
            delete_client(cid)
            self.refresh()


class ProductsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Товары (МКЛ)", parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        # Table
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "SPH", "CYL", "AX", "BC"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.layout().addWidget(self.table)

        # Controls
        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Добавить")
        self.edit_btn = QtWidgets.QPushButton("Изменить")
        self.del_btn = QtWidgets.QPushButton("Удалить")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        self.layout().addLayout(btns)

        self.add_btn.clicked.connect(self.add_dialog)
        self.edit_btn.clicked.connect(self.edit_dialog)
        self.del_btn.clicked.connect(self.delete_selected)

        self.refresh()

    def current_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        r = rows[0].row()
        return int(self.table.item(r, 0).text())

    def refresh(self):
        data = list_mkl_products()
        self.table.setRowCount(0)
        for row in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(self._fmt(row["sph"])))
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(self._fmt(row["cyl"])))
            self.table.setItem(r, 4, QtWidgets.QTableWidgetItem(self._fmt(row["ax"])))
            self.table.setItem(r, 5, QtWidgets.QTableWidgetItem(self._fmt(row["bc"])))

    def _fmt(self, v):
        return "" if v is None else str(v)

    def add_dialog(self):
        dlg = ProductDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            add_mkl_product(dlg.name.text(), dlg.sph_value(), dlg.cyl_value(), dlg.ax_value(), dlg.bc_value())
            self.refresh()

    def edit_dialog(self):
        pid = self.current_id()
        if not pid:
            return
        r = self.table.currentRow()
        dlg = ProductDialog(self)
        dlg.name.setText(self.table.item(r, 1).text())
        dlg.sph.setValue(self._float(self.table.item(r, 2).text(), 0.0))
        dlg.cyl.setValue(self._float(self.table.item(r, 3).text(), 0.0))
        dlg.ax.setValue(self._int(self.table.item(r, 4).text(), 0))
        dlg.bc.setValue(self._float(self.table.item(r, 5).text(), 8.6))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            update_mkl_product(pid, dlg.name.text(), dlg.sph_value(), dlg.cyl_value(), dlg.ax_value(), dlg.bc_value())
            self.refresh()

    def delete_selected(self):
        pid = self.current_id()
        if not pid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить товар?") == QtWidgets.QMessageBox.Yes:
            delete_mkl_product(pid)
            self.refresh()

    def _float(self, s: str, default: float) -> float:
        try:
            return float(s)
        except Exception:
            return default

    def _int(self, s: str, default: int) -> int:
        try:
            return int(float(s))
        except Exception:
            return default


class ProductDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Товар (МКЛ)")
        layout = QtWidgets.QFormLayout(self)

        self.name = QtWidgets.QLineEdit()
        layout.addRow("Название:", self.name)

        self.sph = QtWidgets.QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setValue(0.0)
        layout.addRow("SPH:", self.sph)

        # CYL with "Пусто"
        cyl_row = QtWidgets.QHBoxLayout()
        self.cyl = QtWidgets.QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setValue(0.0)
        self.cyl_none = QtWidgets.QCheckBox("пусто")
        self.cyl_none.toggled.connect(lambda v: (self.cyl.setEnabled(not v)))
        cyl_row.addWidget(self.cyl)
        cyl_row.addWidget(self.cyl_none)
        layout.addRow("CYL:", cyl_row)

        # AX with "Пусто"
        ax_row = QtWidgets.QHBoxLayout()
        self.ax = QtWidgets.QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setValue(0)
        self.ax_none = QtWidgets.QCheckBox("пусто")
        self.ax_none.toggled.connect(lambda v: (self.ax.setEnabled(not v)))
        ax_row.addWidget(self.ax)
        ax_row.addWidget(self.ax_none)
        layout.addRow("AX:", ax_row)

        # BC with "Пусто"
        bc_row = QtWidgets.QHBoxLayout()
        self.bc = QtWidgets.QDoubleSpinBox()
        self.bc.setRange(8.0, 9.0)
        self.bc.setSingleStep(0.1)
        self.bc.setValue(8.6)
        self.bc_none = QtWidgets.QCheckBox("пусто")
        self.bc_none.toggled.connect(lambda v: (self.bc.setEnabled(not v)))
        bc_row.addWidget(self.bc)
        bc_row.addWidget(self.bc_none)
        layout.addRow("BC:", bc_row)

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    def sph_value(self):
        return float(self.sph.value())

    def cyl_value(self):
        return None if self.cyl_none.isChecked() else float(self.cyl.value())

    def ax_value(self):
        return None if self.ax_none.isChecked() else int(self.ax.value())

    def bc_value(self):
        return None if self.bc_none.isChecked() else float(self.bc.value())


class MKLAddItemDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить позицию в заказ")
        form = QtWidgets.QFormLayout(self)

        self.product_combo = QtWidgets.QComboBox()
        for row in list_mkl_products():
            self.product_combo.addItem(row["name"], row["id"])
        form.addRow("Товар:", self.product_combo)

        self.sph = QtWidgets.QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setValue(0.0)
        form.addRow("SPH:", self.sph)

        cyl_row = QtWidgets.QHBoxLayout()
        self.cyl = QtWidgets.QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setValue(0.0)
        self.cyl_none = QtWidgets.QCheckBox("пусто")
        self.cyl_none.toggled.connect(lambda v: self.cyl.setEnabled(not v))
        cyl_row.addWidget(self.cyl)
        cyl_row.addWidget(self.cyl_none)
        form.addRow("CYL:", cyl_row)

        ax_row = QtWidgets.QHBoxLayout()
        self.ax = QtWidgets.QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setValue(0)
        self.ax_none = QtWidgets.QCheckBox("пусто")
        self.ax_none.toggled.connect(lambda v: self.ax.setEnabled(not v))
        ax_row.addWidget(self.ax)
        ax_row.addWidget(self.ax_none)
        form.addRow("AX:", ax_row)

        bc_row = QtWidgets.QHBoxLayout()
        self.bc = QtWidgets.QDoubleSpinBox()
        self.bc.setRange(8.0, 9.0)
        self.bc.setSingleStep(0.1)
        self.bc.setValue(8.6)
        self.bc_none = QtWidgets.QCheckBox("пусто")
        self.bc_none.toggled.connect(lambda v: self.bc.setEnabled(not v))
        bc_row.addWidget(self.bc)
        bc_row.addWidget(self.bc_none)
        form.addRow("BC:", bc_row)

        self.qty = QtWidgets.QSpinBox()
        self.qty.setRange(1, 20)
        self.qty.setValue(1)
        form.addRow("Количество:", self.qty)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def data(self):
        return {
            "product_id": int(self.product_combo.currentData()),
            "sph": float(self.sph.value()),
            "cyl": None if self.cyl_none.isChecked() else float(self.cyl.value()),
            "ax": None if self.ax_none.isChecked() else int(self.ax.value()),
            "bc": None if self.bc_none.isChecked() else float(self.bc.value()),
            "qty": int(self.qty.value()),
        }


class MKLOrderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый заказ МКЛ")
        main = QtWidgets.QVBoxLayout(self)

        # Client
        form = QtWidgets.QFormLayout()
        self.client_combo = QtWidgets.QComboBox()
        self._load_clients()
        form.addRow("Клиент:", self.client_combo)

        # Product
        self.product_combo = QtWidgets.QComboBox()
        self._load_products()
        form.addRow("Товар:", self.product_combo)

        # Specs
        self.sph = QtWidgets.QDoubleSpinBox()
        self.sph.setRange(-30.0, 30.0)
        self.sph.setSingleStep(0.25)
        self.sph.setValue(0.0)
        form.addRow("SPH:", self.sph)

        cyl_row = QtWidgets.QHBoxLayout()
        self.cyl = QtWidgets.QDoubleSpinBox()
        self.cyl.setRange(-10.0, 10.0)
        self.cyl.setSingleStep(0.25)
        self.cyl.setValue(0.0)
        self.cyl_none = QtWidgets.QCheckBox("пусто")
        self.cyl_none.toggled.connect(lambda v: self.cyl.setEnabled(not v))
        cyl_row.addWidget(self.cyl)
        cyl_row.addWidget(self.cyl_none)
        form.addRow("CYL:", cyl_row)

        ax_row = QtWidgets.QHBoxLayout()
        self.ax = QtWidgets.QSpinBox()
        self.ax.setRange(0, 180)
        self.ax.setValue(0)
        self.ax_none = QtWidgets.QCheckBox("пусто")
        self.ax_none.toggled.connect(lambda v: self.ax.setEnabled(not v))
        ax_row.addWidget(self.ax)
        ax_row.addWidget(self.ax_none)
        form.addRow("AX:", ax_row)

        bc_row = QtWidgets.QHBoxLayout()
        self.bc = QtWidgets.QDoubleSpinBox()
        self.bc.setRange(8.0, 9.0)
        self.bc.setSingleStep(0.1)
        self.bc.setValue(8.6)
        self.bc_none = QtWidgets.QCheckBox("пусто")
        self.bc_none.toggled.connect(lambda v: self.bc.setEnabled(not v))
        bc_row.addWidget(self.bc)
        bc_row.addWidget(self.bc_none)
        form.addRow("BC:", bc_row)

        self.qty = QtWidgets.QSpinBox()
        self.qty.setRange(1, 20)
        self.qty.setValue(1)
        form.addRow("Количество:", self.qty)

        main.addLayout(form)

        # Buttons
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        main.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    def _load_clients(self):
        self.client_combo.clear()
        for row in list_clients(""):
            self.client_combo.addItem(f'{row["full_name"]} ({row["phone"] or ""})', row["id"])

    def _load_products(self):
        self.product_combo.clear()
        for row in list_mkl_products():
            self.product_combo.addItem(row["name"], row["id"])

    def data(self):
        return {
            "client_id": int(self.client_combo.currentData()),
            "product_id": int(self.product_combo.currentData()),
            "sph": float(self.sph.value()),
            "cyl": None if self.cyl_none.isChecked() else float(self.cyl.value()),
            "ax": None if self.ax_none.isChecked() else int(self.ax.value()),
            "bc": None if self.bc_none.isChecked() else float(self.bc.value()),
            "qty": int(self.qty.value()),
        }


class OrdersPanel(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Заказы МКЛ", parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        # Filters
        filters = QtWidgets.QHBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Поиск по ФИО или телефону")
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["Все"] + MKL_STATUSES)
        self.search.textChanged.connect(self.refresh)
        self.status_combo.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.search)
        filters.addWidget(self.status_combo)
        self.layout().addLayout(filters)

        # Split orders/items
        split = QtWidgets.QSplitter()
        # Orders table
        self.orders_table = QtWidgets.QTableWidget(0, 5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Клиент", "Телефон", "Статус", "Позиции"])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.orders_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.orders_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self._orders_menu)
        self.orders_table.itemSelectionChanged.connect(self.refresh_items)
        split.addWidget(self.orders_table)

        # Items table
        self.items_table = QtWidgets.QTableWidget(0, 8)
        self.items_table.setHorizontalHeaderLabels(["ID", "Товар", "SPH", "CYL", "AX", "BC", "Qty", ""])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.items_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self._items_menu)
        split.addWidget(self.items_table)

        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        self.layout().addWidget(split)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        self.new_btn = QtWidgets.QPushButton("Новый заказ")
        self.status_btn = QtWidgets.QPushButton("Изменить статус")
        self.add_item_btn = QtWidgets.QPushButton("Добавить позицию")
        self.edit_item_btn = QtWidgets.QPushButton("Изменить позицию")
        self.delete_item_btn = QtWidgets.QPushButton("Удалить позицию")
        self.delete_order_btn = QtWidgets.QPushButton("Удалить заказ")
        self.export_btn = QtWidgets.QPushButton("Экспорт по статусу")
        btns.addWidget(self.new_btn)
        btns.addWidget(self.status_btn)
        btns.addWidget(self.add_item_btn)
        btns.addWidget(self.edit_item_btn)
        btns.addWidget(self.delete_item_btn)
        btns.addWidget(self.delete_order_btn)
        btns.addWidget(self.export_btn)
        self.layout().addLayout(btns)

        self.new_btn.clicked.connect(self.create_order)
        self.status_btn.clicked.connect(self.change_status)
        self.add_item_btn.clicked.connect(self.add_item_to_order)
        self.edit_item_btn.clicked.connect(self.edit_item)
        self.delete_item_btn.clicked.connect(self.delete_item)
        self.delete_order_btn.clicked.connect(self.delete_order)
        self.export_btn.clicked.connect(self.export_by_status)

        # Shortcuts
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self, activated=self.create_order)
        QtWidgets.QShortcut(QtGui.QKeySequence("F2"), self, activated=self.change_status)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+I"), self, activated=self.add_item_to_order)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+E"), self, activated=self.export_by_status)
        QtWidgets.QShortcut(QtGui.QKeySequence("Delete"), self, activated=self.delete_order)

        self.refresh()

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

    def refresh(self):
        data = list_mkl_orders(self.status_combo.currentText(), self.search.text())
        self.orders_table.setRowCount(0)
        for row in data:
            items = get_mkl_order_items(int(row["id"]))
            summary = "; ".join(
                f'{i["product_name"]} SPH:{_val(i["sph"])} CYL:{_val(i["cyl"])} AX:{_val(i["ax"])} BC:{_val(i["bc"])} x{i["qty"]}'
                for i in items
            )
            r = self.orders_table.rowCount()
            self.orders_table.insertRow(r)
            self.orders_table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.orders_table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["full_name"]))
            self.orders_table.setItem(r, 2, QtWidgets.QTableWidgetItem(row["phone"] or ""))
            status_item = QtWidgets.QTableWidgetItem(row["status"])
            color = {
                "Не заказан": QtCore.Qt.yellow,
                "Заказан": QtCore.Qt.cyan,
                "Прозвонен": QtCore.Qt.magenta,
                "Вручен": QtCore.Qt.green,
            }.get(row["status"], QtCore.Qt.white)
            status_item.setBackground(color)
            self.orders_table.setItem(r, 3, status_item)
            self.orders_table.setItem(r, 4, QtWidgets.QTableWidgetItem(summary))
        if self.orders_table.rowCount():
            self.orders_table.selectRow(0)
        self.refresh_items()

    def refresh_items(self):
        oid = self.current_order_id()
        self.items_table.setRowCount(0)
        if not oid:
            return
        items = get_mkl_order_items(oid)
        for i in items:
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            self.items_table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(i["id"])))
            self.items_table.setItem(r, 1, QtWidgets.QTableWidgetItem(i["product_name"]))
            self.items_table.setItem(r, 2, QtWidgets.QTableWidgetItem(_val(i["sph"])))
            self.items_table.setItem(r, 3, QtWidgets.QTableWidgetItem(_val(i["cyl"])))
            self.items_table.setItem(r, 4, QtWidgets.QTableWidgetItem(_val(i["ax"])))
            self.items_table.setItem(r, 5, QtWidgets.QTableWidgetItem(_val(i["bc"])))
            self.items_table.setItem(r, 6, QtWidgets.QTableWidgetItem(str(i["qty"])))
            self.items_table.setItem(r, 7, QtWidgets.QTableWidgetItem(""))

    def create_order(self):
        dlg = MKLOrderDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            d = dlg.data()
            oid = create_mkl_order(d["client_id"], "Не заказан")
            add_mkl_order_item(oid, d["product_id"], d["sph"], d["cyl"], d["ax"], d["bc"], d["qty"])
            self.refresh()

    def change_status(self):
        oid = self.current_order_id()
        if not oid:
            return
        status, ok = QtWidgets.QInputDialog.getItem(self, "Статус", "Выберите статус:", MKL_STATUSES, 0, False)
        if not ok:
            return
        set_mkl_order_status(oid, status)
        self.refresh()

    def add_item_to_order(self):
        oid = self.current_order_id()
        if not oid:
            return
        dlg = MKLAddItemDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            d = dlg.data()
            add_mkl_order_item(oid, d["product_id"], d["sph"], d["cyl"], d["ax"], d["bc"], d["qty"])
            self.refresh_items()

    def edit_item(self):
        from database import update_mkl_order_item, list_mkl_products
        iid = self.current_item_id()
        oid = self.current_order_id()
        if not iid or not oid:
            return
        r = self.items_table.currentRow()
        # prefill dialog
        dlg = MKLAddItemDialog(self)
        # select product by name match
        prod_name = self.items_table.item(r, 1).text()
        for idx in range(dlg.product_combo.count()):
            if dlg.product_combo.itemText(idx) == prod_name:
                dlg.product_combo.setCurrentIndex(idx)
                break
        # set values
        dlg.sph.setValue(self._to_float(self.items_table.item(r, 2).text(), 0.0))
        cyl_text = self.items_table.item(r, 3).text()
        if cyl_text == "":
            dlg.cyl_none.setChecked(True)
        else:
            dlg.cyl.setValue(self._to_float(cyl_text, 0.0))
        ax_text = self.items_table.item(r, 4).text()
        if ax_text == "":
            dlg.ax_none.setChecked(True)
        else:
            dlg.ax.setValue(int(self._to_float(ax_text, 0)))
        bc_text = self.items_table.item(r, 5).text()
        if bc_text == "":
            dlg.bc_none.setChecked(True)
        else:
            dlg.bc.setValue(self._to_float(bc_text, 8.6))
        dlg.qty.setValue(int(self._to_float(self.items_table.item(r, 6).text(), 1)))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            d = dlg.data()
            update_mkl_order_item(iid, d["product_id"], d["sph"], d["cyl"], d["ax"], d["bc"], d["qty"])
            self.refresh_items()

    def delete_item(self):
        from database import delete_mkl_order_item
        iid = self.current_item_id()
        if not iid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить позицию?") == QtWidgets.QMessageBox.Yes:
            delete_mkl_order_item(iid)
            self.refresh_items()

    def delete_order(self):
        oid = self.current_order_id()
        if not oid:
            return
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить заказ и позиции?") == QtWidgets.QMessageBox.Yes:
            delete_mkl_order(oid)
            self.refresh()

    def _orders_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_new = menu.addAction("Новый заказ")
        act_status = menu.addAction("Изменить статус")
        act_add_item = menu.addAction("Добавить позицию")
        act_delete = menu.addAction("Удалить заказ")
        act_export = menu.addAction("Экспорт по статусу")
        action = menu.exec_(self.orders_table.mapToGlobal(pos))
        if action == act_new:
            self.create_order()
        elif action == act_status:
            self.change_status()
        elif action == act_add_item:
            self.add_item_to_order()
        elif action == act_delete:
            self.delete_order()
        elif action == act_export:
            self.export_by_status()

    def _items_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_add = menu.addAction("Добавить позицию")
        act_edit = menu.addAction("Изменить позицию")
        act_delete = menu.addAction("Удалить позицию")
        action = menu.exec_(self.items_table.mapToGlobal(pos))
        if action == act_add:
            self.add_item_to_order()
        elif action == act_edit:
            self.edit_item()
        elif action == act_delete:
            self.delete_item()

    def export_by_status(self):
        from utils_export import export_txt, export_csv, export_xlsx
        status, ok = QtWidgets.QInputDialog.getItem(self, "Экспорт", "Статус для экспорта:", MKL_STATUSES, 0, False)
        if not ok:
            return
        data = list_mkl_orders(status, "")
        if not data:
            QtWidgets.QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return
        fmt, ok = QtWidgets.QInputDialog.getItem(self, "Формат", "Выберите формат:", ["TXT", "CSV", "XLSX"], 0, False)
        if not ok:
            return
        default_name = f"mkl_{status.lower()}.{fmt.lower()}"
        filters = ";;".join(["Text (*.txt)", "CSV (*.csv)", "Excel (*.xlsx)"])
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", default_name, filters)
        if not path:
            return
        rows = []
        # header
        rows.append(["OrderID", "Клиент", "Телефон", "Статус", "Товар", "SPH", "CYL", "AX", "BC", "Qty"])
        for row in data:
            items = get_mkl_order_items(int(row["id"]))
            for i in items:
                rows.append(
                    [
                        str(row["id"]),
                        row["full_name"],
                        row["phone"] or "",
                        row["status"],
                        i["product_name"],
                        _val(i["sph"]),
                        _val(i["cyl"]),
                        _val(i["ax"]),
                        _val(i["bc"]),
                        str(i["qty"]),
                    ]
                )
        try:
            if fmt == "TXT":
                export_txt(path, rows, sep="|")
            elif fmt == "CSV":
                export_csv(path, rows)
            else:
                export_xlsx(path, rows)
            QtWidgets.QMessageBox.information(self, "Экспорт", f"Экспортировано в файл:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def _to_float(self, s: str, default: float) -> float:
        try:
            return float(s)
        except Exception:
            return default


def _val(v) -> str:
    return "" if v is None else str(v)


class MKLInterface(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        splitter = QtWidgets.QSplitter()
        left = QtWidgets.QWidget()
        left.setLayout(QtWidgets.QVBoxLayout())
        self.clients = ClientsPanel()
        self.products = ProductsPanel()
        left.layout().addWidget(self.clients)
        left.layout().addWidget(self.products)

        right = QtWidgets.QWidget()
        right.setLayout(QtWidgets.QVBoxLayout())
        self.orders = OrdersPanel()
        right.layout().addWidget(self.orders)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)