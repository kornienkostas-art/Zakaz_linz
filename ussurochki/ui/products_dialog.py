from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QInputDialog,
)

from ..db import Database


class ProductsDialog(QDialog):
    def __init__(self, db: Database, kind: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.kind = kind  # "mkl" or "meridian"
        self.setWindowTitle("Товары (МКЛ)" if kind == "mkl" else "Товары (Меридиан)")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск товара...")
        self.search.textChanged.connect(self.reload)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self.add_product)
        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.clicked.connect(self.edit_product)
        self.btn_del = QPushButton("Удалить")
        self.btn_del.clicked.connect(self.delete_product)

        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_del)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["ID", "Название"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table, 1)
        self.resize(600, 480)

        self.reload()

    def reload(self):
        if self.kind == "mkl":
            products = self.db.list_products_mkl()
        else:
            products = self.db.list_products_meridian()
        query = self.search.text().strip().lower()
        self.table.setRowCount(0)
        for row_data in products:
            name = row_data["name"]
            if query and query not in name.lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [str(row_data["id"]), name]
            for col, val in enumerate(vals):
                self.table.setItem(row, col, QTableWidgetItem(val))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self.table.item(rows[0].row(), 0).text())

    def add_product(self):
        name, ok = QInputDialog.getText(self, "Новый товар", "Название:")
        if not ok or not name.strip():
            return
        try:
            if self.kind == "mkl":
                self.db.add_product_mkl(name.strip())
            else:
                self.db.add_product_meridian(name.strip())
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self.reload()

    def edit_product(self):
        pid = self._selected_id()
        if not pid:
            return
        cur_name = self.table.item(self.table.currentRow(), 1).text()
        name, ok = QInputDialog.getText(self, "Изменить товар", "Название:", text=cur_name)
        if not ok or not name.strip():
            return
        try:
            if self.kind == "mkl":
                self.db.update_product_mkl(pid, name.strip())
            else:
                self.db.update_product_meridian(pid, name.strip())
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self.reload()

    def delete_product(self):
        pid = self._selected_id()
        if not pid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить товар? Товар не будет удалён, если есть связанные позиции в заказах.") == QMessageBox.StandardButton.Yes:
            try:
                if self.kind == "mkl":
                    self.db.delete_product_mkl(pid)
                else:
                    self.db.delete_product_meridian(pid)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))
            self.reload()