from typing import List, Optional
import os

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
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
from ..exporters import export_mkl_by_status
from ..utils import format_item_mkl_row
from .mkl_order_dialog import MKLOrderDialog
from .clients_dialog import ClientsDialog
from .products_dialog import ProductsDialog


MKL_STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]


class MKLOrdersPage(QWidget):
    def __init__(self, db: Database, settings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings
        self._orders_cache: List[dict] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по ФИО или телефону...")
        self.search.textChanged.connect(self.reload)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Все"] + MKL_STATUSES)
        self.cmb_status.currentIndexChanged.connect(self.reload)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.btn_add.clicked.connect(self.add_order)

        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.clicked.connect(self.edit_selected)

        self.btn_del = QPushButton("Удалить")
        self.btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.btn_del.clicked.connect(self.delete_selected)

        self.btn_clients = QPushButton("Клиенты")
        self.btn_clients.clicked.connect(self.manage_clients)

        self.btn_products = QPushButton("Товары")
        self.btn_products.clicked.connect(self.manage_products)

        self.btn_export = QPushButton("Экспорт TXT")
        self.btn_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_export.clicked.connect(self.export_txt)

        top = QHBoxLayout()
        top.addWidget(self.search, 2)
        top.addWidget(self.cmb_status, 1)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_del)
        top.addStretch(1)
        top.addWidget(self.btn_clients)
        top.addWidget(self.btn_products)
        top.addWidget(self.btn_export)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Клиент", "Телефон", "Товары", "Статус", "Дата"])
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
        query = self.search.text().strip()
        self._orders_cache = self.db.list_orders_mkl(search=query, status=status if status != "Все" else None)
        self.table.setRowCount(0)
        for od in self._orders_cache:
            row = self.table.rowCount()
            self.table.insertRow(row)
            items_str = "; ".join([f"{it['product_name']} [{format_item_mkl_row(it)}]" for it in od["items"]])
            vals = [
                str(od["id"]),
                od["client_name"],
                od.get("phone") or "",
                items_str,
                od["status"],
                od["created_at"],
            ]
            for col, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if col in (0, 5):
                    it.setData(Qt.ItemDataRole.UserRole, val)
                self.table.setItem(row, col, it)
            # status color
            st_item = self.table.item(row, 4)
            color_map = {
                "Не заказан": "#ef4444",
                "Заказан": "#22c55e",
                "Прозвонен": "#f59e0b",
                "Вручен": "#3b82f6",
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
        dlg = MKLOrderDialog(self.db, self)
        if dlg.exec():
            self.reload()

    def edit_selected(self):
        order_id = self._selected_order_id()
        if not order_id:
            return
        dlg = MKLOrderDialog(self.db, self, order_id=order_id)
        if dlg.exec():
            self.reload()

    def delete_selected(self):
        order_id = self._selected_order_id()
        if not order_id:
            return
        if QMessageBox.question(self, "Удалить", "Удалить выбранный заказ?") == QMessageBox.StandardButton.Yes:
            self.db.delete_order_mkl(order_id)
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
        for st in MKL_STATUSES:
            submenu.addAction(st)
        act = menu.exec(self.table.mapToGlobal(pos))
        if not act:
            return
        if act == act_edit:
            self.edit_selected()
        elif act == act_del:
            self.delete_selected()
        elif act.text() in MKL_STATUSES:
            self.db.update_order_mkl_status(order_id, act.text())
            self.reload()

    def manage_clients(self):
        dlg = ClientsDialog(self.db, self)
        if dlg.exec():
            self.reload()

    def manage_products(self):
        dlg = ProductsDialog(self.db, kind="mkl", parent=self)
        if dlg.exec():
            self.reload()

    def export_txt(self):
        status = self.cmb_status.currentText()
        if status == "Все":
            QMessageBox.information(self, "Экспорт", "Выберите конкретный статус для экспорта.")
            return
        default_dir = self.settings.value("export_dir", "exports")
        os_dir = QFileDialog.getExistingDirectory(self, "Папка для экспорта", default_dir)
        if not os_dir:
            return
        self.settings.setValue("export_dir", os_dir)
        path = os.path.join(os_dir, f"mkl_{status.replace(' ', '_')}.txt")
        export_mkl_by_status(self._orders_cache, status, path)
        QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")