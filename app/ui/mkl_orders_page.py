import sqlite3
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTableView,
    QMenu,
    QMessageBox,
    QPushButton,
)

from ..models import OrderStatus
from ..repo import list_orders_mkl, delete_order_mkl, duplicate_order_mkl, export_mkl_by_product
from ..settings_store import SettingsStore
from .order_dialogs import MKLOrderDialog


STATUS_TEXTS = [
    "Все",
    "Не заказан",
    "Заказан",
    "Прозвонен",
    "Вручен",
]

STATUS_TO_ENUM = {
    "Не заказан": OrderStatus.NOT_ORDERED,
    "Заказан": OrderStatus.ORDERED,
    "Прозвонен": OrderStatus.CALLED,
    "Вручен": OrderStatus.DELIVERED,
}


class OrdersTableModel(QAbstractTableModel):
    headers = ["Клиент", "Телефон", "Статус", "Дата", "Позиций"]

    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        super().__init__()
        self.rows = rows

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return row["client"]
            if col == 1:
                return row["phone"] or ""
            if col == 2:
                return OrderStatus(int(row["status"])).to_text()
            if col == 3:
                return row["created_at"]
            if col == 4:
                return row["positions"]
        if role == Qt.BackgroundRole and col == 2:
            color_hex = OrderStatus(int(row["status"])).color_hex()
            return QColor(color_hex)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        key_funcs = [
            lambda r: r["client"],
            lambda r: r["phone"] or "",
            lambda r: int(r["status"]),
            lambda r: r["created_at"],
            lambda r: int(r["positions"]),
        ]
        reverse = order == Qt.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        self.rows.sort(key=key_funcs[column], reverse=reverse)
        self.layoutChanged.emit()


class OrdersProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.filter_text = ""
        self.filter_status_text = "Все"

    def setFilterText(self, text: str) -> None:
        self.filter_text = text or ""
        self.invalidateFilter()

    def setFilterStatusText(self, text: str) -> None:
        self.filter_status_text = text or "Все"
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: OrdersTableModel = self.sourceModel()  # type: ignore
        idx_client = model.index(source_row, 0)
        idx_phone = model.index(source_row, 1)
        idx_status = model.index(source_row, 2)
        s_client = (model.data(idx_client, Qt.DisplayRole) or "").lower()
        s_phone = (model.data(idx_phone, Qt.DisplayRole) or "").lower()
        s_status = model.data(idx_status, Qt.DisplayRole) or ""
        ok_status = True
        if self.filter_status_text != "Все":
            ok_status = s_status == self.filter_status_text
        if not self.filter_text:
            return ok_status
        text = self.filter_text.lower()
        ok_search = text in s_client or text in s_phone
        return ok_status and ok_search


class MklOrdersPage(QWidget):
    def __init__(self, conn: sqlite3.Connection, settings: SettingsStore) -> None:
        super().__init__()
        self.conn = conn
        self.settings_store = settings
        self._make_ui()
        self.reload()

    def _make_ui(self) -> None:
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО/телефону...")

        self.status_filter = QComboBox()
        self.status_filter.addItems(STATUS_TEXTS)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По статусу", "По дате", "По ФИО"])

        top = QHBoxLayout()
        self.new_btn = QPushButton("Новый заказ")
        top.addWidget(self.new_btn)
        top.addWidget(self.search_edit, stretch=1)
        top.addWidget(self.status_filter)
        top.addWidget(self.sort_combo)

        self.table = QTableView()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.doubleClicked.connect(self._open_selected)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)

        self.search_edit.textChanged.connect(self._apply_filter)
        self.status_filter.currentIndexChanged.connect(self._apply_filter)
        self.sort_combo.currentIndexChanged.connect(self._apply_sort)
        self.new_btn.clicked.connect(self._new_order)

    def reload(self) -> None:
        rows = list_orders_mkl(self.conn)
        self.model = OrdersTableModel(rows)
        self.proxy = OrdersProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(3, Qt.DescendingOrder)
        self._apply_filter()
        self._apply_sort()

    def _apply_filter(self) -> None:
        text = self.search_edit.text().strip()
        self.proxy.setFilterText(text)
        status_text = self.status_filter.currentText()
        self.proxy.setFilterStatusText(status_text)

    def _apply_sort(self) -> None:
        choice = self.sort_combo.currentText()
        column_map = {
            "По статусу": 2,
            "По дате": 3,
            "По ФИО": 0,
        }
        col = column_map.get(choice, 3)
        self.table.sortByColumn(col, Qt.AscendingOrder if col == 0 else Qt.DescendingOrder)

    def _selected_order_id(self) -> int:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return -1
        src_idx = self.proxy.mapToSource(idx)
        row = self.model.rows[src_idx.row()]
        return int(row["id"])

    def _open_selected(self) -> None:
        oid = self._selected_order_id()
        if oid < 0:
            return
        dlg = MKLOrderDialog(self.conn, oid, self)
        if dlg.exec():
            self.reload()

    def _new_order(self) -> None:
        dlg = MKLOrderDialog(self.conn, None, self)
        if dlg.exec():
            self.reload()

    def _open_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        open_act = menu.addAction("Открыть")
        status_menu = menu.addMenu("Изменить статус")
        for s in [OrderStatus.NOT_ORDERED, OrderStatus.ORDERED, OrderStatus.CALLED, OrderStatus.DELIVERED]:
            a = status_menu.addAction(s.to_text())
            a.setData(int(s))
        menu.addSeparator()
        dup_act = menu.addAction("Дублировать")
        del_act = menu.addAction("Удалить…")
        menu.addSeparator()
        export_menu = menu.addMenu("Экспорт →")
        export_menu.addAction("Свод по товарам…")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if not action:
            return
        oid = self._selected_order_id()
        if action == open_act:
            self._open_selected()
        elif action == dup_act and oid > 0:
            duplicate_order_mkl(self.conn, oid)
            self.reload()
        elif action == del_act and oid > 0:
            ret = QMessageBox.question(self, "Удалить", "Удалить выбранный заказ?")
            if ret == QMessageBox.Yes:
                delete_order_mkl(self.conn, oid)
                self.reload()
        elif action.parentWidget() == status_menu and oid > 0:
            val = action.data()
            if val is not None:
                from ..repo import update_status_mkl

                update_status_mkl(self.conn, oid, OrderStatus(int(val)))
                self.reload()
        elif action.parentWidget() == export_menu:
            status_text = self.status_filter.currentText()
            if status_text == "Все":
                QMessageBox.warning(self, "Экспорт", "Выберите статус для экспорта (не «Все»).")
                return
            status_enum = STATUS_TO_ENUM[status_text]
            path = export_mkl_by_product(self.conn, status_enum, self.settings_store.get())
            QMessageBox.information(self, "Экспорт завершён", f"Файл сохранён:\n{path}")
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTableView,
    QMenu,
    QMessageBox,
)

from ..models import OrderStatus
from ..repo import list_orders_mkl, delete_order_mkl, duplicate_order_mkl, export_mkl_by_product
from ..settings_store import SettingsStore
from .order_dialogs import MKLOrderDialog


STATUS_TEXTS = [
    "Все",
    "Не заказан",
    "Заказан",
    "Прозвонен",
    "Вручен",
]

STATUS_TO_ENUM = {
    "Не заказан": OrderStatus.NOT_ORDERED,
    "Заказан": OrderStatus.ORDERED,
    "Прозвонен": OrderStatus.CALLED,
    "Вручен": OrderStatus.DELIVERED,
}


class OrdersTableModel(QAbstractTableModel):
    headers = ["Клиент", "Телефон", "Статус", "Дата", "Позиций"]

    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        super().__init__()
        self.rows = rows

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return row["client"]
            if col == 1:
                return row["phone"] or ""
            if col == 2:
                return OrderStatus(int(row["status"])).to_text()
            if col == 3:
                return row["created_at"]
            if col == 4:
                return row["positions"]
        if role == Qt.BackgroundRole and col == 2:
            color_hex = OrderStatus(int(row["status"])).color_hex()
            return QColor(color_hex)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        key_funcs = [
            lambda r: r["client"],
            lambda r: r["phone"] or "",
            lambda r: int(r["status"]),
            lambda r: r["created_at"],
            lambda r: int(r["positions"]),
        ]
        reverse = order == Qt.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        self.rows.sort(key=key_funcs[column], reverse=reverse)
        self.layoutChanged.emit()


class MklOrdersPage(QWidget):
    def __init__(self, conn: sqlite3.Connection, settings: SettingsStore) -> None:
        super().__init__()
        self.conn = conn
        self.settings_store = settings
        self._make_ui()
        self.reload()

    def _make_ui(self) -> None:
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО/телефону...")

        self.status_filter = QComboBox()
        self.status_filter.addItems(STATUS_TEXTS)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По статусу", "По дате", "По ФИО"])

        top = QHBoxLayout()
        top.addWidget(self.search_edit, stretch=1)
        top.addWidget(self.status_filter)
        top.addWidget(self.sort_combo)

        self.table = QTableView()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.doubleClicked.connect(self._open_selected)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)

        self.search_edit.textChanged.connect(self._apply_filter)
        self.status_filter.currentIndexChanged.connect(self._apply_filter)
        self.sort_combo.currentIndexChanged.connect(self._apply_sort)

    def reload(self) -> None:
        rows = list_orders_mkl(self.conn)
        self.model = OrdersTableModel(rows)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # all columns
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(3, Qt.DescendingOrder)
        self._apply_filter()
        self._apply_sort()

    def _apply_filter(self) -> None:
        text = self.search_edit.text().strip()
        self.proxy.setFilterFixedString(text)
        status_text = self.status_filter.currentText()
        if status_text == "Все":
            self.proxy.setFilterRegularExpression(text)
        else:
            status_enum = STATUS_TO_ENUM[status_text]
            # Filter by both search and status
            def filter_accepts(source_row: int, source_parent: QModelIndex) -> bool:
                idx_client = self.model.index(source_row, 0)
                idx_phone = self.model.index(source_row, 1)
                idx_status = self.model.index(source_row, 2)
                s_client = self.model.data(idx_client, Qt.DisplayRole) or ""
                s_phone = self.model.data(idx_phone, Qt.DisplayRole) or ""
                s_status = self.model.data(idx_status, Qt.DisplayRole) or ""
                ok_status = s_status == status_text
                ok_search = (text.lower() in s_client.lower()) or (text.lower() in str(s_phone).lower())
                return ok_status and (not text or ok_search)

            self.proxy.setFilterAcceptsRow(filter_accepts)

    def _apply_sort(self) -> None:
        choice = self.sort_combo.currentText()
        column_map = {
            "По статусу": 2,
            "По дате": 3,
            "По ФИО": 0,
        }
        col = column_map.get(choice, 3)
        self.table.sortByColumn(col, Qt.AscendingOrder if col == 0 else Qt.DescendingOrder)

    def _selected_order_id(self) -> int:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return -1
        src_idx = self.proxy.mapToSource(idx)
        row = self.model.rows[src_idx.row()]
        return int(row["id"])

    def _open_selected(self) -> None:
        oid = self._selected_order_id()
        if oid < 0:
            return
        dlg = MKLOrderDialog(self.conn, oid, self)
        if dlg.exec():
            self.reload()

    def _open_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        open_act = menu.addAction("Открыть")
        status_menu = menu.addMenu("Изменить статус")
        for s in [OrderStatus.NOT_ORDERED, OrderStatus.ORDERED, OrderStatus.CALLED, OrderStatus.DELIVERED]:
            status_menu.addAction(s.to_text()).setData(s)
        menu.addSeparator()
        dup_act = menu.addAction("Дублировать")
        del_act = menu.addAction("Удалить…")
        menu.addSeparator()
        export_menu = menu.addMenu("Экспорт →")
        export_menu.addAction("Свод по товарам…")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if not action:
            return
        oid = self._selected_order_id()
        if action == open_act:
            self._open_selected()
        elif action == dup_act and oid > 0:
            duplicate_order_mkl(self.conn, oid)
            self.reload()
        elif action == del_act and oid > 0:
            ret = QMessageBox.question(self, "Удалить", "Удалить выбранный заказ?")
            if ret == QMessageBox.Yes:
                delete_order_mkl(self.conn, oid)
                self.reload()
        elif action.parentWidget() == export_menu:
            status_text = self.status_filter.currentText()
            if status_text == "Все":
                QMessageBox.warning(self, "Экспорт", "Выберите статус для экспорта (не «Все»).")
                return
            status_enum = STATUS_TO_ENUM[status_text]
            path = export_mkl_by_product(self.conn, status_enum, self.settings_store.get())
            QMessageBox.information(self, "Экспорт завершён", f"Файл сохранён:\n{path}")