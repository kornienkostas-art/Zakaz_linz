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
    QLabel,
    QInputDialog,
)

from ..db import Database
from ..utils import is_valid_phone


class ClientsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Клиенты")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск клиента...")
        self.search.textChanged.connect(self.reload)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self.add_client)
        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.clicked.connect(self.edit_client)
        self.btn_del = QPushButton("Удалить")
        self.btn_del.clicked.connect(self.delete_client)

        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_edit)
        top.addWidget(self.btn_del)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table, 1)

        self.resize(700, 500)
        self.reload()

    def reload(self):
        query = self.search.text().strip()
        clients = self.db.list_clients(query)
        self.table.setRowCount(0)
        for row_data in clients:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [str(row_data["id"]), row_data["full_name"], row_data["phone"] or ""]
            for col, val in enumerate(vals):
                self.table.setItem(row, col, QTableWidgetItem(val))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(self.table.item(rows[0].row(), 0).text())

    def add_client(self):
        name, ok = QInputDialog.getText(self, "Новый клиент", "ФИО:")
        if not ok or not name.strip():
            return
        phone, ok2 = QInputDialog.getText(self, "Новый клиент", "Телефон (+7XXXXXXXXXX или 8XXXXXXXXXX):")
        if not ok2:
            return
        if not name.strip():
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно.")
            return
        if phone and not is_valid_phone(phone):
            QMessageBox.warning(self, "Ошибка", "Неверный формат телефона.")
            return
        try:
            self.db.add_client(name.strip(), phone.strip() if phone else None)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self.reload()

    def edit_client(self):
        cid = self._selected_id()
        if not cid:
            return
        cur_name = self.table.item(self.table.currentRow(), 1).text()
        cur_phone = self.table.item(self.table.currentRow(), 2).text()
        name, ok = QInputDialog.getText(self, "Изменить клиента", "ФИО:", text=cur_name)
        if not ok or not name.strip():
            return
        phone, ok2 = QInputDialog.getText(self, "Изменить клиента", "Телефон:", text=cur_phone)
        if not ok2:
            return
        if not name.strip():
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно.")
            return
        if phone and not is_valid_phone(phone):
            QMessageBox.warning(self, "Ошибка", "Неверный формат телефона.")
            return
        try:
            self.db.update_client(cid, name.strip(), phone.strip() if phone else None)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self.reload()

    def delete_client(self):
        cid = self._selected_id()
        if not cid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить клиента? Клиент не будет удалён, если есть связанные заказы.") == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_client(cid)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))
            self.reload()