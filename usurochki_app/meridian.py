from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
    QMessageBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QFileDialog,
    QMenu,
)

from .db import Database
from .validators import (
    validate_sph,
    validate_cyl,
    validate_ax,
    validate_qty,
)

MER_STATUSES = ["Заказан", "Не заказан"]


class ProductDialog(QDialog):
    def __init__(self, parent=None, name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Товар (Меридиан)")
        layout = QFormLayout(self)

        from PyQt6.QtWidgets import QLineEdit
        self.name_edit = QLineEdit(name)
        layout.addRow("Название*", self.name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название обязательно.")
            return None
        return name


class OrderItemDialog(QDialog):
    def __init__(self, parent=None, product_name: str = "", sph: float = 0.0, cyl: Optional[float] = None,
                 ax: Optional[int] = None, qty: int = 1, products: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Позиция заказа (Меридиан)")
        layout = QFormLayout(self)

        self.product_combo = QComboBox()
        if products:
            self.product_combo.addItems(products)
        if product_name:
            idx = self.product_combo.findText(product_name)
            if idx >= 0:
                self.product_combo.setCurrentIndex(idx)
            else:
                self.product_combo.insertItem(0, product_name)
                self.product_combo.setCurrentIndex(0)

        self.sph_spin = QDoubleSpinBox()
        self.sph_spin.setRange(-30.0, 30.0)
        self.sph_spin.setSingleStep(0.25)
        self.sph_spin.setDecimals(2)
        self.sph_spin.setValue(sph)

        self.cyl_spin = QDoubleSpinBox()
        self.cyl_spin.setRange(-10.0, 10.0)
        self.cyl_spin.setSingleStep(0.25)
        self.cyl_spin.setDecimals(2)
        if cyl is not None:
            self.cyl_spin.setValue(cyl)
        else:
            self.cyl_spin.clear()

        self.ax_spin = QSpinBox()
        self.ax_spin.setRange(0, 180)
        if ax is not None:
            self.ax_spin.setValue(ax)
        else:
            self.ax_spin.clear()

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 20)
        self.qty_spin.setValue(qty)

        layout.addRow("Товар", self.product_combo)
        layout.addRow("SPH", self.sph_spin)
        layout.addRow("CYL (пусто если нет)", self.cyl_spin)
        layout.addRow("AX (пусто если нет)", self.ax_spin)
        layout.addRow("Количество", self.qty_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        product_name = self.product_combo.currentText().strip()
        sph = float(self.sph_spin.value())
        cyl_text = self.cyl_spin.text().strip()
        ax_text = self.ax_spin.text().strip()
        qty = int(self.qty_spin.value())

        cyl = float(cyl_text) if cyl_text else None
        ax = int(ax_text) if ax_text else None

        if not validate_sph(sph):
            QMessageBox.warning(self, "Ошибка", "SPH должен быть в диапазоне [-30; 30] с шагом 0.25.")
            return None
        if cyl is not None and not validate_cyl(cyl):
            QMessageBox.warning(self, "Ошибка", "CYL должен быть в диапазоне [-10; 10] с шагом 0.25.")
            return None
        if ax is not None and not validate_ax(ax):
            QMessageBox.warning(self, "Ошибка", "AX должен быть в диапазоне [0; 180] с шагом 1.")
            return None
        if not validate_qty(qty):
            QMessageBox.warning(self, "Ошибка", "Количество должно быть от 1 до 20.")
            return None

        return product_name, sph, cyl, ax, qty


class MeridianWindow(QWidget):
    def __init__(self, db: Database, export_dir: str):
        super().__init__()
        self.db = db
        self.export_dir = export_dir
        self.setWindowTitle("Заказы Меридиан — УссурОЧки.рф")

        # Верхнее управление товарами
        top = QHBoxLayout()
        btn_add_prod = QPushButton("Добавить товар")
        btn_edit_prod = QPushButton("Редактировать товар")
        btn_del_prod = QPushButton("Удалить товар")
        top.addWidget(btn_add_prod)
        top.addWidget(btn_edit_prod)
        top.addWidget(btn_del_prod)

        # Заказы
        controls = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItem("Все")
        self.status_combo.addItems(MER_STATUSES)
        btn_add_order = QPushButton("Создать заказ")
        btn_edit_items = QPushButton("Редактировать позиции")
        btn_status = QPushButton("Изменить статус")
        btn_del_order = QPushButton("Удалить заказ")
        btn_export = QPushButton("Экспорт незаказанных товаров")

        controls.addWidget(QLabel("Статус:"))
        controls.addWidget(self.status_combo)
        controls.addWidget(btn_add_order)
        controls.addWidget(btn_edit_items)
        controls.addWidget(btn_status)
        controls.addWidget(btn_del_order)
        controls.addWidget(btn_export)

        self.products_table = QTableWidget(0, 2)
        self.products_table.setHorizontalHeaderLabels(["ID", "Название"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self._products_context_menu)

        self.orders_table = QTableWidget(0, 4)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Номер", "Статус", "Дата"])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self._orders_context_menu)

        main = QVBoxLayout(self)
        main.addLayout(top)
        main.addWidget(self.products_table)
        main.addLayout(controls)
        main.addWidget(self.orders_table)

        btn_add_prod.clicked.connect(self._add_product)
        btn_edit_prod.clicked.connect(self._edit_product)
        btn_del_prod.clicked.connect(self._del_product)

        self.status_combo.currentIndexChanged.connect(self.refresh_orders)
        btn_add_order.clicked.connect(self._create_order)
        btn_edit_items.clicked.connect(self._edit_order_items)
        btn_status.clicked.connect(self._change_status)
        btn_del_order.clicked.connect(self._del_order)
        btn_export.clicked.connect(self._export_unordered_items)

        self.refresh_products()
        self.refresh_orders()

    # --------- Товары ----------
    def _products_context_menu(self, pos):
        menu = QMenu(self)
        act_add = QAction("Добавить", self)
        act_edit = QAction("Редактировать", self)
        act_del = QAction("Удалить", self)
        act_add.triggered.connect(self._add_product)
        act_edit.triggered.connect(self._edit_product)
        act_del.triggered.connect(self._del_product)
        menu.addAction(act_add)
        menu.addAction(act_edit)
        menu.addAction(act_del)
        menu.exec(self.products_table.mapToGlobal(pos))

    def _selected_id(self, table: QTableWidget) -> Optional[int]:
        idxs = table.selectionModel().selectedRows()
        if not idxs:
            return None
        row = idxs[0].row()
        item = table.item(row, 0)
        return int(item.text()) if item else None

    def refresh_products(self):
        rows = self.db.list_products("meridian")
        self.products_table.setRowCount(0)
        for r in rows:
            rr = self.products_table.rowCount()
            self.products_table.insertRow(rr)
            self.products_table.setItem(rr, 0, QTableWidgetItem(str(r["id"])))
            self.products_table.setItem(rr, 1, QTableWidgetItem(r["name"]))

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_data()
            if name:
                try:
                    self.db.add_product("meridian", name)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось добавить товар: {e}")
                self.refresh_products()

    def _edit_product(self):
        pid = self._selected_id(self.products_table)
        if not pid:
            return
        rows = self.db.list_products("meridian")
        row = next((r for r in rows if r["id"] == pid), None)
        if not row:
            return
        dlg = ProductDialog(self, name=row["name"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_data()
            if name:
                try:
                    self.db.update_product("meridian", pid, name)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось обновить товар: {e}")
                self.refresh_products()

    def _del_product(self):
        pid = self._selected_id(self.products_table)
        if not pid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить товар?") == QMessageBox.StandardButton.Yes:
            self.db.delete_product("meridian", pid)
            self.refresh_products()

    # --------- Заказы ----------
    def _orders_context_menu(self, pos):
        menu = QMenu(self)
        act_add = QAction("Создать заказ", self)
        act_edit_items = QAction("Редактировать позиции", self)
        act_status = QAction("Изменить статус", self)
        act_del = QAction("Удалить", self)
        act_add.triggered.connect(self._create_order)
        act_edit_items.triggered.connect(self._edit_order_items)
        act_status.triggered.connect(self._change_status)
        act_del.triggered.connect(self._del_order)
        menu.addAction(act_add)
        menu.addAction(act_edit_items)
        menu.addAction(act_status)
        menu.addAction(act_del)
        menu.exec(self.orders_table.mapToGlobal(pos))

    def refresh_orders(self):
        status = None if self.status_combo.currentText() == "Все" else self.status_combo.currentText()
        rows = self.db.list_orders_meridian(status_filter=status)
        self.orders_table.setRowCount(0)
        for r in rows:
            rr = self.orders_table.rowCount()
            self.orders_table.insertRow(rr)
            self.orders_table.setItem(rr, 0, QTableWidgetItem(str(r["id"])))
            self.orders_table.setItem(rr, 1, QTableWidgetItem(str(r["number"])))
            status_item = QTableWidgetItem(r["status"])
            color_map = {
                "Не заказан": QColor(220, 38, 38),  # красный
                "Заказан": QColor(34, 197, 94),     # зелёный
            }
            status_item.setForeground(color_map.get(r["status"], QColor(255, 255, 255)))
            self.orders_table.setItem(rr, 2, status_item)
            self.orders_table.setItem(rr, 3, QTableWidgetItem(r["created_at"]))

    def _selected_order_id(self) -> Optional[int]:
        return self._selected_id(self.orders_table)

    def _create_order(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Создать заказ (Меридиан)")
        fl = QFormLayout(dlg)
        combo_status = QComboBox()
        combo_status.addItems(MER_STATUSES)
        fl.addRow("Статус", combo_status)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        fl.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            status = combo_status.currentText()
            order_id = self.db.create_order_meridian(status)
            self.refresh_orders()
            if QMessageBox.question(self, "Позиции", "Добавить позиции сейчас?") == QMessageBox.StandardButton.Yes:
                self._edit_order_items(order_id)

    def _edit_order_items(self, order_id: Optional[int] = None):
        oid = order_id or self._selected_order_id()
        if not oid:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Позиции заказа (Меридиан)")
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["ID", "Товар", "SPH", "CYL", "AX", "Qty"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        btns = QHBoxLayout()
        btn_add = QPushButton("Добавить позицию")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")
        btns.addWidget(btn_add)
        btns.addWidget(btn_edit)
        btns.addWidget(btn_del)

        layout.addWidget(table)
        layout.addLayout(btns)

        products = [p["name"] for p in self.db.list_products("meridian")]

        def refresh_items():
            table.setRowCount(0)
            items = self.db.list_order_items_meridian(oid)
            for it in items:
                r = table.rowCount()
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(str(it["id"])))
                table.setItem(r, 1, QTableWidgetItem(it["product_name"]))
                table.setItem(r, 2, QTableWidgetItem(str(it["sph"])))
                table.setItem(r, 3, QTableWidgetItem("" if it["cyl"] is None else str(it["cyl"])))
                table.setItem(r, 4, QTableWidgetItem("" if it["ax"] is None else str(it["ax"])))
                table.setItem(r, 5, QTableWidgetItem(str(it["qty"])))

        refresh_items()

        def selected_item_id() -> Optional[int]:
            idxs = table.selectionModel().selectedRows()
            if not idxs:
                return None
            row = idxs[0].row()
            item = table.item(row, 0)
            return int(item.text()) if item else None

        def add_item():
            idlg = OrderItemDialog(self, products=products)
            if idlg.exec() == QDialog.DialogCode.Accepted:
                data = idlg.get_data()
                if data:
                    product_name, sph, cyl, ax, qty = data
                    self.db.add_order_item_meridian(oid, product_name, sph, cyl, ax, qty)
                    refresh_items()

        def edit_item():
            iid = selected_item_id()
            if not iid:
                return
            items = self.db.list_order_items_meridian(oid)
            it = next((x for x in items if x["id"] == iid), None)
            if not it:
                return
            idlg = OrderItemDialog(
                self,
                product_name=it["product_name"],
                sph=float(it["sph"]),
                cyl=None if it["cyl"] is None else float(it["cyl"]),
                ax=None if it["ax"] is None else int(it["ax"]),
                qty=int(it["qty"]),
                products=products,
            )
            if idlg.exec() == QDialog.DialogCode.Accepted:
                data = idlg.get_data()
                if data:
                    product_name, sph, cyl, ax, qty = data
                    self.db.update_order_item_meridian(iid, product_name, sph, cyl, ax, qty)
                    refresh_items()

        def del_item():
            iid = selected_item_id()
            if not iid:
                return
            if QMessageBox.question(dlg, "Удалить", "Удалить позицию?") == QMessageBox.StandardButton.Yes:
                self.db.delete_order_item_meridian(iid)
                refresh_items()

        btn_add.clicked.connect(add_item)
        btn_edit.clicked.connect(edit_item)
        btn_del.clicked.connect(del_item)

        dlg.exec()

    def _change_status(self):
        oid = self._selected_order_id()
        if not oid:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Изменить статус заказа (Меридиан)")
        fl = QFormLayout(dlg)
        combo = QComboBox()
        combo.addItems(MER_STATUSES)
        fl.addRow("Статус", combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        fl.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            status = combo.currentText()
            self.db.update_order_meridian_status(oid, status)
            self.refresh_orders()

    def _del_order(self):
        oid = self._selected_order_id()
        if not oid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить заказ?") == QMessageBox.StandardButton.Yes:
            self.db.delete_order_meridian(oid)
            self.refresh_orders()

    def _export_unordered_items(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить TXT", self.export_dir, "TXT файлы (*.txt)"
        )
        if path:
            try:
                self.db.export_unordered_meridian_items(path)
                QMessageBox.information(self, "Экспорт", "Файл успешно сохранён.")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать: {e}")