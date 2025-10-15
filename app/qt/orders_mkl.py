from typing import List, Dict, Any, Optional
from datetime import datetime

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QStringListModel, QRegularExpression
from PySide6.QtGui import QAction, QRegularExpressionValidator
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
    QCompleter,
    QComboBox,
    QMenu,
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
    STATUS_OPTIONS = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]

    def __init__(self, db: AppDB, parent=None, order: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Заказ МКЛ")
        self._order = order or {}
        self._db = db
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

        # Status combo box
        self.status = QComboBox()
        self.status.addItems(self.STATUS_OPTIONS)
        self.status.setCurrentText(self._order.get("status", "Не заказан"))
        layout.addRow("Статус", self.status)

        self.date = field("date", "Дата", self._order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.comment = field("comment", "Комментарий", self._order.get("comment", ""))

        # Validators for numeric fields (soft validation)
        try:
            num_re = QRegularExpression(r"^[-+]?\\d*(?:[\\.,]\\d+)?$")
            int_re = QRegularExpression(r"^\\d+$")
            for le in (self.sph, self.cyl, self.bc):
                le.setValidator(QRegularExpressionValidator(num_re))
            for le in (self.ax, self.qty):
                le.setValidator(QRegularExpressionValidator(int_re))
        except Exception:
            pass

        # Snap helpers on editing finished
        self.sph.editingFinished.connect(lambda: self._snap_decimal(self.sph, -30.0, 30.0, 0.25))
        self.cyl.editingFinished.connect(lambda: self._snap_decimal(self.cyl, -10.0, 10.0, 0.25))
        self.ax.editingFinished.connect(lambda: self._snap_int(self.ax, 0, 180))
        self.bc.editingFinished.connect(lambda: self._snap_decimal(self.bc, 8.0, 9.0, 0.1))
        self.qty.editingFinished.connect(lambda: self._snap_int(self.qty, 1, 20))

        # Setup completers for FIO and Product from DB lists
        try:
            clients = self._db.list_clients() if self._db else []
            products_mkl = self._db.list_products_mkl() if self._db else []

            # FIO completer with contains match
            fio_list = [c.get("fio", "") for c in clients if (c.get("fio", "") or "").strip()]
            self._clients_by_fio = {c.get("fio", ""): c for c in clients}
            fio_model = QStringListModel(fio_list)
            fio_completer = QCompleter(fio_model, self)
            fio_completer.setCaseSensitivity(Qt.CaseInsensitive)
            try:
                fio_completer.setFilterMode(Qt.MatchContains)
            except Exception:
                pass
            self.fio.setCompleter(fio_completer)

            def on_fio_activated(text: str):
                c = self._clients_by_fio.get(text)
                if c:
                    self.phone.setText(c.get("phone", ""))

            fio_completer.activated[str].connect(on_fio_activated)

            # Product completer
            prod_list = [p.get("name", "") for p in products_mkl if (p.get("name", "") or "").strip()]
            prod_model = QStringListModel(prod_list)
            prod_completer = QCompleter(prod_model, self)
            prod_completer.setCaseSensitivity(Qt.CaseInsensitive)
            try:
                prod_completer.setFilterMode(Qt.MatchContains)
            except Exception:
                pass
            self.product.setCompleter(prod_completer)
        except Exception:
            pass

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @staticmethod
    def _snap_decimal(le: QLineEdit, min_v: float, max_v: float, step: float):
        try:
            text = (le.text() or "").replace(",", ".").strip()
            if text == "":
                return
            v = float(text)
        except Exception:
            # reset into range
            v = min_v
        v = max(min_v, min(max_v, v))
        # snap to step from min_v
        steps = round((v - min_v) / step)
        snapped = min_v + steps * step
        snapped = max(min_v, min(max_v, snapped))
        le.setText(f"{snapped:.2f}")

    @staticmethod
    def _snap_int(le: QLineEdit, min_v: int, max_v: int):
        try:
            text = (le.text() or "").strip()
            if text == "":
                return
            v = int(float(text.replace(",", ".")))
        except Exception:
            v = min_v
        v = max(min_v, min(max_v, v))
        le.setText(str(v))

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
            "status": self.status.currentText() or "Не заказан",
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
        btn_mark = QPushButton("Отметить «Заказан»")
        btn_add.clicked.connect(self._add)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_export.clicked.connect(self._export_txt)
        btn_mark.clicked.connect(self._mark_ordered)
        top.addWidget(self.search, 1)
        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_del)
        top.addWidget(btn_mark)
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

        # Double-click to edit
        try:
            self.table.doubleClicked.connect(lambda _: self._edit())
        except Exception:
            pass

        # Context menu
        try:
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self._show_context_menu)
        except Exception:
            pass

        scroll.setWidget(cont)
        root.addWidget(scroll)

    def _on_search(self, text: str):
        self._model.set_query(text)

    def _selected_order(self) -> Optional[Dict[str, Any]]:
        idx = self.table.currentIndex()
        return self._model.get_row(idx.row())

    def _add(self):
        dlg = OrderFormDialog(self.db, self)
        if dlg.exec():
            order = dlg.result_order()
            self.db.add_mkl_order(order)
            self._refresh()

    def _edit(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Редактирование", "Выберите запись.")
            return
        dlg = OrderFormDialog(self.db, self, row)
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

    def _mark_ordered(self):
        row = self._selected_order()
        if not row:
            QMessageBox.information(self, "Статус", "Выберите запись.")
            return
        try:
            self.db.update_mkl_order(row["id"], {"status": "Заказан", "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            self._refresh()
        except Exception:
            QMessageBox.warning(self, "Статус", "Не удалось обновить статус.")

    def _show_context_menu(self, pos):
        try:
            menu = QMenu(self)
            act_add = menu.addAction("Создать")
            act_edit = menu.addAction("Редактировать")
            act_del = menu.addAction("Удалить")
            menu.addSeparator()
            act_mark = menu.addAction("Отметить «Заказан»")
            act_export = menu.addAction("Экспорт TXT")
            action = menu.exec(self.table.viewport().mapToGlobal(pos))
            if action == act_add:
                self._add()
            elif action == act_edit:
                self._edit()
            elif action == act_del:
                self._delete()
            elif action == act_mark:
                self._mark_ordered()
            elif action == act_export:
                self._export_txt()
        except Exception:
            pass

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