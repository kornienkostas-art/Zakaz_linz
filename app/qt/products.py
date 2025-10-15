from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableView,
    QPushButton,
    QTabWidget,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
)

from app.db import AppDB


class _ProductsModel(QAbstractTableModel):
    def __init__(self, rows: List[Dict[str, Any]]):
        super().__init__()
        self._rows = rows
        self._filtered_idx = list(range(len(rows)))
        self._query = ""

    def set_rows(self, rows: List[Dict[str, Any]]):
        self.beginResetModel()
        self._rows = rows
        self._apply_filter()
        self.endResetModel()

    def set_query(self, query: str):
        self.beginResetModel()
        self._query = (query or "").strip().lower()
        self._apply_filter()
        self.endResetModel()

    def _apply_filter(self):
        if not self._query:
            self._filtered_idx = list(range(len(self._rows)))
            return
        q = self._query
        idxs = []
        for i, r in enumerate(self._rows):
            s = str(r.get("name", "")).lower()
            if q in s:
                idxs.append(i)
        self._filtered_idx = idxs

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_idx)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 2  # id, name

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[self._filtered_idx[index.row()]]
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return row.get("id", "")
            else:
                return row.get("name", "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ["ID", "Название"][section]
        return super().headerData(section, orientation, role)

    def get_row(self, view_row: int) -> Optional[Dict[str, Any]]:
        if 0 <= view_row < len(self._filtered_idx):
            return self._rows[self._filtered_idx[view_row]]
        return None


class _ProductDialog(QDialog):
    def __init__(self, parent=None, name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Товар")
        self._name = name
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(name)
        layout.addRow("Название", self.name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название.")
            return
        self._name = name
        self.accept()

    def result_name(self) -> str:
        return self._name


class ProductsPage(QWidget):
    def __init__(self, db: AppDB, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # MKL tab
        self._mkltab = QWidget()
        mkll = QVBoxLayout(self._mkltab)
        mkltop = QHBoxLayout()
        self.mkls = QLineEdit()
        self.mkls.setPlaceholderText("Поиск…")
        self.mkls.textChanged.connect(lambda t: self._mkllist_query(t))
        mkl_add = QPushButton("Создать")
        mkl_edit = QPushButton("Редактировать")
        mkl_del = QPushButton("Удалить")
        mkl_add.clicked.connect(self._mkl_add)
        mkl_edit.clicked.connect(self._mkl_edit)
        mkl_del.clicked.connect(self._mkl_del)
        mkltop.addWidget(self.mkls, 1)
        mkltop.addWidget(mkl_add)
        mkltop.addWidget(mkl_edit)
        mkltop.addWidget(mkl_del)
        mkll.addLayout(mkltop)
        self.mkltable = QTableView()
        self.mkltable.setSelectionBehavior(QTableView.SelectRows)
        self.mkltable.setSelectionMode(QTableView.SingleSelection)
        self.mkltable.setSortingEnabled(True)
        mkll.addWidget(self.mkltable, 1)
        self._mklmodel = _ProductsModel(self.db.list_products_mkl())
        self.mkltable.setModel(self._mklmodel)
        self.mkltable.resizeColumnsToContents()

        # Meridian tab
        self._mertab = QWidget()
        merl = QVBoxLayout(self._mertab)
        mertop = QHBoxLayout()
        self.mers = QLineEdit()
        self.mers.setPlaceholderText("Поиск…")
        self.mers.textChanged.connect(lambda t: self._merlist_query(t))
        mer_add = QPushButton("Создать")
        mer_edit = QPushButton("Редактировать")
        mer_del = QPushButton("Удалить")
        mer_add.clicked.connect(self._mer_add)
        mer_edit.clicked.connect(self._mer_edit)
        mer_del.clicked.connect(self._mer_del)
        mertop.addWidget(self.mers, 1)
        mertop.addWidget(mer_add)
        mertop.addWidget(mer_edit)
        mertop.addWidget(mer_del)
        merl.addLayout(mertop)
        self.mertable = QTableView()
        self.mertable.setSelectionBehavior(QTableView.SelectRows)
        self.mertable.setSelectionMode(QTableView.SingleSelection)
        self.mertable.setSortingEnabled(True)
        merl.addWidget(self.mertable, 1)
        self._mermodel = _ProductsModel(self.db.list_products_meridian())
        self.mertable.setModel(self._mermodel)
        self.mertable.resizeColumnsToContents()

        self.tabs.addTab(self._mkltab, "МКЛ")
        self.tabs.addTab(self._mertab, "Меридиан")

    # MKL actions
    def _mkllist_query(self, text: str):
        self._mklmodel.set_query(text)

    def _mkl_selected(self) -> Optional[Dict[str, Any]]:
        idx = self.mkltable.currentIndex()
        return self._mklmodel.get_row(idx.row())

    def _mkl_add(self):
        dlg = _ProductDialog(self)
        if dlg.exec():
            name = dlg.result_name()
            self.db.add_product_mkl(name)
            self._mkl_refresh()

    def _mkl_edit(self):
        row = self._mkl_selected()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        dlg = _ProductDialog(self, row.get("name", ""))
        if dlg.exec():
            name = dlg.result_name()
            self.db.update_product_mkl(row["id"], name)
            self._mkl_refresh()

    def _mkl_del(self):
        row = self._mkl_selected()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите запись.")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить запись ID={row['id']}?") == QMessageBox.Yes:
            self.db.delete_product_mkl(row["id"])
            self._mkl_refresh()

    def _mkl_refresh(self):
        self._mklmodel.set_rows(self.db.list_products_mkl())
        self.mkltable.resizeColumnsToContents()

    # Meridian actions
    def _merlist_query(self, text: str):
        self._mermodel.set_query(text)

    def _mer_selected(self) -> Optional[Dict[str, Any]]:
        idx = self.mertable.currentIndex()
        return self._mermodel.get_row(idx.row())

    def _mer_add(self):
        dlg = _ProductDialog(self)
        if dlg.exec():
            name = dlg.result_name()
            self.db.add_product_meridian(name)
            self._mer_refresh()

    def _mer_edit(self):
        row = self._mer_selected()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        dlg = _ProductDialog(self, row.get("name", ""))
        if dlg.exec():
            name = dlg.result_name()
            self.db.update_product_meridian(row["id"], name)
            self._mer_refresh()

    def _mer_del(self):
        row = self._mer_selected()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите запись.")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить запись ID={row['id']}?") == QMessageBox.Yes:
            self.db.delete_product_meridian(row["id"])
            self._mer_refresh()

    def _mer_refresh(self):
        self._mermodel.set_rows(self.db.list_products_meridian())
        self.mertable.resizeColumnsToContents()