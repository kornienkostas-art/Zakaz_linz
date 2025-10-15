from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
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
)

from app.db import AppDB


COLUMNS = [
    ("id", "ID"),
    ("fio", "ФИО"),
    ("phone", "Телефон"),
]


class ClientsModel(QAbstractTableModel):
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


class ClientFormDialog(QDialog):
    def __init__(self, parent=None, client: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        self._client = client or {}
        layout = QFormLayout(self)

        def field(name: str, label: str, initial: str = "") -> QLineEdit:
            le = QLineEdit(initial)
            le.setObjectName(name)
            layout.addRow(label, le)
            return le

        self.fio = field("fio", "ФИО", self._client.get("fio", ""))
        self.phone = field("phone", "Телефон", self._client.get("phone", ""))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        if not self.fio.text().strip() or not self.phone.text().strip():
            QMessageBox.warning(self, "Ошибка", "Заполните поля ФИО и Телефон.")
            return
        self._client = {
            "fio": self.fio.text().strip(),
            "phone": self.phone.text().strip(),
        }
        self.accept()

    def result_client(self) -> Dict[str, Any]:
        return self._client


class ClientsPage(QWidget):
    def __init__(self, db: AppDB, parent=None):
        super().__init__(parent)
        self.db = db

        v = QVBoxLayout(self)
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
        btn_add.clicked.connect(self._add)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        top.addWidget(self.search, 1)
        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_del)
        v.addLayout(top)

        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        v.addWidget(self.table, 1)

        self._model = ClientsModel(self.db.list_clients())
        self.table.setModel(self._model)

        # Header behavior
        try:
            from PySide6.QtWidgets import QHeaderView
            h = self.table.horizontalHeader()
            h.setSectionResizeMode(QHeaderView.Interactive)
            h.setStretchLastSection(True)
            h.setMinimumSectionSize(120)
        except Exception:
            pass

        self.table.resizeColumnsToContents()

    def _on_search(self, text: str):
        self._model.set_query(text)

    def _selected(self) -> Optional[Dict[str, Any]]:
        idx = self.table.currentIndex()
        return self._model.get_row(idx.row())

    def _add(self):
        dlg = ClientFormDialog(self)
        if dlg.exec():
            c = dlg.result_client()
            self.db.add_client(c["fio"], c["phone"])
            self._refresh()

    def _edit(self):
        row = self._selected()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        dlg = ClientFormDialog(self, row)
        if dlg.exec():
            c = dlg.result_client()
            self.db.update_client(row["id"], c["fio"], c["phone"])
            self._refresh()

    def _delete(self):
        row = self._selected()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите запись.")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить запись ID={row['id']}?") == QMessageBox.Yes:
            self.db.delete_client(row["id"])
            self._refresh()

    def _refresh(self):
        self._model.set_rows(self.db.list_clients())
        self.table.resizeColumnsToContents()