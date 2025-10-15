from typing import List, Dict, Any, Optional
from datetime import datetime

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableView,
    QPushButton,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QFileDialog,
    QScrollArea,
)

from app.db import AppDB


COLUMNS = [
    ("id", "ID"),
    ("fio", "ФИО"),
    ("phone", "Телефон"),
    ("product", "Товар"),
    ("sph", "SPH"),
    ("cyl", "CYL"),
    ("ax", "AX"),
    ("bc", "BC"),
    ("qty", "Кол-во"),
    ("status", "Статус"),
    ("date", "Дата"),
    ("comment", "Комментарий"),
]


class OrdersMklModel(QAbstractTableModel):
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
            s = " ".join(str(r.get(k, "")) for k, _ in COLUMNS).lower()
            if q in s:
                idxs.append(i)
        self._filtered_idx = idxs

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_idx)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[self._filtered_idx[index.row()]]
        key = COLUMNS[index.column()][0]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return row.get(key, "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return COLUMNS[section][1]
        return super().headerData(section, orientation, role)

    def get_row(self, view_row: int) -> Optional[Dict[str, Any]]:
        if 0 <= view_row < len(self._filtered_idx):
            return self._rows[self._filtered_idx[view_row]]
        return None


class OrderFormDialog(QDialog):
    def __init__(self, parent=None, order: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Заказ МКЛ")
        self._order = order or {}
        layout = QFormLayout(self)

        def field(name: str, label: str, initial: str = "") -> QLineEdit:
            le = QLineEdit(initial)
            le.setObjectName(name)
            layout.addRow(label, le)
            return le

        self.fio = field("fio", "ФИО", self._order.get("fio", ""))
        self.phone = field("phone", "Телефон", self._order.get("phone", ""))
        self.product = field("product", "Товар", self._order.get("product", ""))
        self.sph = field("sph", "SPH", self._order.get("sph", ""))
        self.cyl = field("cyl", "CYL", self._order.get("cyl", ""))
        self.ax = field("ax", "AX", self._order.get("ax", ""))
        self.bc = field("bc", "BC", self._order.get("bc", ""))
        self.qty = field("qty", "Кол-во", self._order.get("qty", ""))
        self.status = field("status", "Статус", self._order.get("status", "Не заказан"))
        self.date = field("date", "Дата", self._order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.comment = field("comment", "Комментарий", self._order.get("comment", ""))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        # minimal validation
        if not self.fio.text().strip() or not self.product.text().strip():
            QMessageBox.warning(self, "Ошибка", "Заполните поля ФИО и Товар.")
            return
        self._order = {
            "fio": self.fio.text().strip(),
            "phone": self.phone.text().strip(),
            "product": self.product.text().strip(),
            "sph": self.sph.text().strip(),
            "cyl": self.cyl.text().strip(),
            "ax": self.ax.text().strip(),
            "bc": self.bc.text().strip(),
            "qty": self.qty.text().strip(),
            "status": self.status.text().strip() or "Не заказан",
            "date": self.date.text().strip() or datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": self.comment.text().strip(),
        }
        self.accept()

    def result_order(self) -> Dict[str, Any]:
        return self._order


class OrdersMklPage(QWidget):
    def __init__(self, db: AppDB, export_folder_getter, parent=None):
        super().__init__(parent)
        self.db = db
        self.export_folder_getter = export_folder_getter

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        v = QVBoxLayout(cont)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск…")
        self.search.setMinimumWidth(200)
        self.search.textChanged.connect(self._on_search)
        btn_add = QPushButton("Создать")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")
        btn_export = QPushButton("Экспорт TXT")
        btn_add.clicked.connect(self._add)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_export.clicked.connect(self._export_txt)
        top.addWidget(self.search, 1)
        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_del)
        top.addWidget(btn_export)
        v.addLayout(top)

        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        v.addWidget(self.table, 1)

        self._model = OrdersMklModel(self.db.list_mkl_orders())
        self.table.setModel(self._model)

        # Header behavior for small windows
        header = self.table.horizontalHeader()
        try:
            from PySide6.QtWidgets import QHeaderView
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setStretchLastSection(True)
            header.setMinimumSectionSize(100)
        except Exception:
            pass

        self.table.resizeColumnsToContents()

        scroll.setWidget(cont)
        root.addWidget(scroll)

    def _on_search(self, text: str):
        self._model.set_query(text)

    def _selected_order(self) -> Optional[Dict[str, Any]]:
        idx = self.table.currentIndex()
        return self._model.get_row(idx.row())

    def _add(self):
        dlg = OrderFormDialog(self)
        if dlg.exec():
            order = dlg.result_order()
            self.db.add_mkl_order(order)
            self._refresh()

    def _edit(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        dlg = OrderFormDialog(self, row)
        if dlg.exec():
            updated = dlg.result_order()
            self.db.update_mkl_order(row["id"], updated)
            self._refresh()

    def _delete(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите запись.")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить запись ID={row['id']}?") == QMessageBox.Yes:
            self.db.delete_mkl_order(row["id"])
            self._refresh()

    def _refresh(self):
        self._model.set_rows(self.db.list_mkl_orders())
        self.table.resizeColumnsToContents()

    def _export_txt(self):
        # Export all rows to TXT (simple format)
        orders = self.db.list_mkl_orders()
        export_dir = self.export_folder_getter()
        if not export_dir:
            export_dir = "."
        fname = QFileDialog.getSaveFileName(self, "Сохранить TXT", export_dir, "Text files (*.txt)")[0]
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf-8") as f:
                for o in orders:
                    line = (
                        f"ID={o['id']} | {o['fio']} | {o['phone']} | "
                        f"{o['product']} | SPH={o['sph']} CYL={o['cyl']} AX={o['ax']} BC={o['bc']} | "
                        f"QTY={o['qty']} | {o['status']} | {o['date']} | {o['comment']}\n"
                    )
                    f.write(line)
            QMessageBox.information(self, "Экспорт", f"Файл сохранен: {fname}")
        except Exception as e:
            QMessageBox.warning(self, "Экспорт", f"Ошибка экспорта: {e}")