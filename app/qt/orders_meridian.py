from typing import List, Dict, Any, Optional
from datetime import datetime

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
    QFileDialog,
    QTabWidget,
    QSpinBox,
)

from app.db import AppDB

ORDER_COLUMNS = [
    ("id", "ID"),
    ("title", "Название"),
    ("status", "Статус"),
    ("date", "Дата"),
]

ITEM_COLUMNS = [
    ("id", "ID"),
    ("product", "Товар"),
    ("sph", "SPH"),
    ("cyl", "CYL"),
    ("ax", "AX"),
    ("d", "D"),
    ("qty", "Кол-во"),
]


class OrdersMeridianModel(QAbstractTableModel):
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
            s = " ".join(str(r.get(k, "")) for k, _ in ORDER_COLUMNS).lower()
            if q in s:
                idxs.append(i)
        self._filtered_idx = idxs

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered_idx)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(ORDER_COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[self._filtered_idx[index.row()]]
        key = ORDER_COLUMNS[index.column()][0]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return row.get(key, "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ORDER_COLUMNS[section][1]
        return super().headerData(section, orientation, role)

    def get_row(self, view_row: int) -> Optional[Dict[str, Any]]:
        if 0 <= view_row < len(self._filtered_idx):
            return self._rows[self._filtered_idx[view_row]]
        return None


class ItemsModel(QAbstractTableModel):
    def __init__(self, items: List[Dict[str, Any]]):
        super().__init__()
        self._items = items

    def set_items(self, items: List[Dict[str, Any]]):
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(ITEM_COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._items[index.row()]
        key = ITEM_COLUMNS[index.column()][0]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return row.get(key, "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ITEM_COLUMNS[section][1]
        return super().headerData(section, orientation, role)

    def get_row(self, view_row: int) -> Optional[Dict[str, Any]]:
        if 0 <= view_row < len(self._items):
            return self._items[view_row]
        return None


class ItemDialog(QDialog):
    def __init__(self, parent=None, item: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Позиция заказа")
        self._item = item or {}
        layout = QFormLayout(self)

        def field_str(key: str, label: str, initial: str = "") -> QLineEdit:
            le = QLineEdit(initial)
            le.setObjectName(key)
            layout.addRow(label, le)
            return le

        self.product = field_str("product", "Товар", self._item.get("product", ""))
        self.sph = field_str("sph", "SPH", self._item.get("sph", ""))
        self.cyl = field_str("cyl", "CYL", self._item.get("cyl", ""))
        self.ax = field_str("ax", "AX", self._item.get("ax", ""))
        self.d = field_str("d", "D", self._item.get("d", ""))
        self.qty = field_str("qty", "Кол-во", self._item.get("qty", ""))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        if not self.product.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите товар.")
            return
        self._item = {
            "product": self.product.text().strip(),
            "sph": self.sph.text().strip(),
            "cyl": self.cyl.text().strip(),
            "ax": self.ax.text().strip(),
            "d": self.d.text().strip(),
            "qty": self.qty.text().strip(),
        }
        self.accept()

    def result_item(self) -> Dict[str, Any]:
        return self._item


class OrderDialog(QDialog):
    def __init__(self, db: AppDB, parent=None, order: Optional[Dict[str, Any]] = None, items: Optional[List[Dict[str, Any]]] = None):
        super().__init__(parent)
        self.setWindowTitle("Заказ «Меридиан»")
        self.db = db
        self._order = order or {}
        self._items = items[:] if items else []
        layout = QVBoxLayout(self)

        # Order fields
        form = QFormLayout()
        self.title = QLineEdit(self._order.get("title", ""))
        self.status = QLineEdit(self._order.get("status", "Не заказан"))
        self.date = QLineEdit(self._order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")))
        form.addRow("Название", self.title)
        form.addRow("Статус", self.status)
        form.addRow("Дата", self.date)
        layout.addLayout(form)

        # Items section
        items_top = QHBoxLayout()
        btn_add = QPushButton("Добавить позицию")
        btn_edit = QPushButton("Редактировать позицию")
        btn_del = QPushButton("Удалить позицию")
        btn_add.clicked.connect(self._add_item)
        btn_edit.clicked.connect(self._edit_item)
        btn_del.clicked.connect(self._del_item)
        items_top.addWidget(btn_add)
        items_top.addWidget(btn_edit)
        items_top.addWidget(btn_del)
        layout.addLayout(items_top)

        self.items_table = QTableView()
        self.items_table.setSelectionBehavior(QTableView.SelectRows)
        self.items_table.setSelectionMode(QTableView.SingleSelection)
        self.items_table.setSortingEnabled(True)
        layout.addWidget(self.items_table, 1)

        self._items_model = ItemsModel(self._items)
        self.items_table.setModel(self._items_model)
        self.items_table.resizeColumnsToContents()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _selected_item(self) -> Optional[Dict[str, Any]]:
        idx = self.items_table.currentIndex()
        return self._items_model.get_row(idx.row())

    def _add_item(self):
        dlg = ItemDialog(self)
        if dlg.exec():
            self._items.append(dlg.result_item())
            self._items_model.set_items(self._items)
            self.items_table.resizeColumnsToContents()

    def _edit_item(self):
        row = self._selected_item()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите позицию.")
            return
        dlg = ItemDialog(self, row)
        if dlg.exec():
            updated = dlg.result_item()
            # Replace in list
            idx = self.items_table.currentIndex().row()
            self._items[idx] = updated
            self._items_model.set_items(self._items)
            self.items_table.resizeColumnsToContents()

    def _del_item(self):
        row = self._selected_item()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите позицию.")
            return
        if QMessageBox.question(self, "Удаление", "Удалить выбранную позицию?") == QMessageBox.Yes:
            idx = self.items_table.currentIndex().row()
            del self._items[idx]
            self._items_model.set_items(self._items)
            self.items_table.resizeColumnsToContents()

    def _on_accept(self):
        if not self.title.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название заказа.")
            return
        self._order = {
            "title": self.title.text().strip(),
            "status": self.status.text().strip() or "Не заказан",
            "date": self.date.text().strip() or datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.accept()

    def result_order(self) -> Dict[str, Any]:
        return self._order

    def result_items(self) -> List[Dict[str, Any]]:
        return self._items


class OrdersMeridianPage(QWidget):
    def __init__(self, db: AppDB, export_folder_getter, parent=None):
        super().__init__(parent)
        self.db = db
        self.export_folder_getter = export_folder_getter

        v = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск…")
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
        v.addWidget(self.table, 1)

        self._model = OrdersMeridianModel(self.db.list_meridian_orders())
        self.table.setModel(self._model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str):
        self._model.set_query(text)

    def _selected_order(self) -> Optional[Dict[str, Any]]:
        idx = self.table.currentIndex()
        return self._model.get_row(idx.row())

    def _add(self):
        dlg = OrderDialog(self.db, self)
        if dlg.exec():
            order = dlg.result_order()
            items = dlg.result_items()
            self.db.add_meridian_order(order, items)
            self._refresh()

    def _edit(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        items = self.db.get_meridian_items(row["id"])
        dlg = OrderDialog(self.db, self, row, items)
        if dlg.exec():
            order = dlg.result_order()
            new_items = dlg.result_items()
            self.db.update_meridian_order(row["id"], order)
            self.db.replace_meridian_items(row["id"], new_items)
            self._refresh()

    def _delete(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Удаление", "Выберите запись.")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить заказ ID={row['id']}?") == QMessageBox.Yes:
            self.db.delete_meridian_order(row["id"])
            self._refresh()

    def _refresh(self):
        self._model.set_rows(self.db.list_meridian_orders())
        self.table.resizeColumnsToContents()

    def _export_txt(self):
        # Export all orders with items to TXT
        orders = self.db.list_meridian_orders()
        export_dir = self.export_folder_getter()
        if not export_dir:
            export_dir = "."
        fname = QFileDialog.getSaveFileName(self, "Сохранить TXT", export_dir, "Text files (*.txt)")[0]
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf-8") as f:
                for o in orders:
                    f.write(f"Заказ ID={o['id']} | {o['title']} | {o['status']} | {o['date']}\n")
                    items = self.db.get_meridian_items(o["id"])
                    for it in items:
                        line = (
                            f"  - {it['product']} | SPH={it['sph']} CYL={it['cyl']} AX={it['ax']} D={it['d']} | QTY={it['qty']}\n"
                        )
                        f.write(line)
                    f.write("\n")
            QMessageBox.information(self, "Экспорт", f"Файл сохранен: {fname}")
        except Exception as e:
            QMessageBox.warning(self, "Экспорт", f"Ошибка экспорта: {e}")