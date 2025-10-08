from typing import List, Optional
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMenu,
    QMessageBox,
    QFileDialog,
    QStyle,
)

from ..db import Database
from ..exporters import export_meridian_not_ordered
from ..utils import format_item_meridian_row
from .meridian_order_dialog import MeridianOrderDialog


MERIDIAN_STATUSES = ["Не заказан", "Заказан"]


class MeridianOrdersPage(QWidget):
    def __init__(self, db: Database, settings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings
        self._orders_cache: List[dict] = []

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Все"] + MERIDIAN_STATUSES)
        self.cmb_status.currentIndexChanged.connect(self.reload)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.btn_add.clicked.connect(self.add_order)

        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.clicked.connect(self.edit_selected)

        self.btn_del = QPushButton("Удалить")
        self.btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.btn_del.clicked.connect(self.delete_selected)

        self.btn_products = QPushButton("Товары")
        self.btn_products.clicked.connect(self.manage_products)

        self.btn_export = QPushButton("Экспорт незаказанных")
        self.btn_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_export.clicked.connect(self.export_txt)

        top = QHBoxLayout()
        top.addWidget(self.cmb_status, 1)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_del)
        top.addStretch(1)
        top.addWidget(self.btn_products)
        top.addWidget(self.btn_export)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Товары", "Статус", "Дата"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_ctx_menu)
        self.table.doubleClicked.connect(self.edit_selected)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table, 1)

        self.reload()

    def reload(self):
        status = self.cmb_status.currentText()
        self._orders_cache = self.db.list_orders_meridian(status=status if status != "Все" else None)
        self.table.setRowCount(0)
        for od in self._orders_cache:
            row = self.table.rowCount()
            self.table.insertRow(row)
            items_str = "; ".join([f"{it['product_name']} [{format_item_meridian_row(it)}]" for it in od["items"]])
            vals = [
                str(od["id"]),
                str(od["number"]),
                items_str,
                od["status"],
                od["created_at"],
            ]
            for col, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if col in (0, 1, 4):
                    it.setData(Qt.ItemDataRole.UserRole, val)
                self.table.setItem(row, col, it)
            st_item = self.table.item(row, 3)
            color_map = {
                "Не заказан": "#ef4444",
                "Заказан": "#22c55e",
            }
            c = color_map.get(st_item.text())
            if c:
                st_item.setBackground(QColor(c))
                st_item.setForeground(QColor("#ffffff"))
        self.table.resizeColumnsToContents()

    def _selected_order_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return int(self.table.item(row, 0).text())

    def add_order(self):
        dlg = MeridianOrderDialog(self.db, self)
        if dlg.exec():
            self.reload()

    def edit_selected(self):
        order_id = self._selected_order_id()
        if not order_id:
            return
        dlg = MeridianOrderDialog(self.db, self, order_id=order_id)
        if dlg.exec():
            self.reload()

    def delete_selected(self):
        order_id = self._selected_order_id()
        if not order_id:
            return
        if QMessageBox.question(self, "Удалить", "Удалить выбранный заказ?") == QMessageBox.StandardButton.Yes:
            self.db.delete_order_meridian(order_id)
            self.reload()

    def open_ctx_menu(self, pos):
        order_id = self._selected_order_id()
        if not order_id:
            return
        menu = QMenu(self)
        act_edit = menu.addAction("Изменить")
        act_del = menu.addAction("Удалить")
        menu.addSeparator()
        submenu = menu.addMenu("Изменить статус")
        for st in MERIDIAN_STATUSES:
            submenu.addAction(st)
        act = menu.exec(self.table.mapToGlobal(pos))
        if not act:
            return
        if act == act_edit:
            self.edit_selected()
        elif act == act_del:
            self.delete_selected()
        elif act.text() in MERIDIAN_STATUSES:
            self.db.update_order_meridian_status(order_id, act.text())
            self.reload()

    def manage_products(self):
        from .products_dialog import ProductsDialog
        dlg = ProductsDialog(self.db, kind="meridian", parent=self)
        if dlg.exec():
            self.reload()

    def export_txt(self):
        default_dir = self.settings.value("export_dir", "exports")
        os_dir = QFileDialog.getExistingDirectory(self, "Папка для экспорта", default_dir)
        if not os_dir:
            return
        self.settings.setValue("export_dir", os_dir)
        path = os.path.join(os_dir, "meridian_not_ordered.txt")
        export_meridian_not_ordered(self._orders_cache, path)
        QMessageBox.information(self, "Экспорт", f"Файл сохранён:\\n{path}")