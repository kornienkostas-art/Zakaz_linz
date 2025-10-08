from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QLabel,
    QComboBox,
    QMessageBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QTabWidget,
    QFileDialog,
    QMenu,
)

# Импорты пакета или локальные при запуске скриптов напрямую
try:
    from .db import Database
    from .validators import (
        validate_phone,
        validate_sph,
        validate_cyl,
        validate_ax,
        validate_bc,
        validate_qty,
        normalize_empty_str,
    )
except ImportError:
    from db import Database
    from validators import (
        validate_phone,
        validate_sph,
        validate_cyl,
        validate_ax,
        validate_bc,
        validate_qty,
        normalize_empty_str,
    )


MKL_STATUSES = ["Не заказан", "Заказан", "Прозвонен", "Вручен"]


class ClientDialog(QDialog):
    def __init__(self, parent=None, name: str = "", phone: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Клиент")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.phone_edit = QLineEdit(phone)
        # Автоформатирование номера телефона: +7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX
        self.phone_edit.setPlaceholderText("+7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX")
        def _apply_mask(t: str):
            if t.startswith("+7"):
                self.phone_edit.setInputMask("+7-000-000-00-00;_")
            elif t.startswith("8"):
                self.phone_edit.setInputMask("8-000-000-00-00;_")
            else:
                self.phone_edit.setInputMask("")
        self.phone_edit.textEdited.connect(_apply_mask)

        layout.addRow("ФИО*", self.name_edit)
        layout.addRow("Телефон", self.phone_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        name = self.name_edit.text().strip()
        phone = normalize_empty_str(self.phone_edit.text())
        if not name:
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно.")
            return None
        if phone and not validate_phone(phone):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Телефон должен быть в формате +7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX.",
            )
            return None
        return name, phone


class ProductDialog(QDialog):
    def __init__(self, parent=None, name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Товар")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        layout.addRow("Название*", self.name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название обязательно.")
            return None
        return name


class OrderItemDialog(QDialog):
    def __init__(self, parent=None, product_name: str = "", sph: float = 0.0, cyl: Optional[float] = None,
                 ax: Optional[int] = None, bc: Optional[float] = None, qty: int = 1, products: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Позиция заказа (МКЛ)")
        layout = QFormLayout(self)

        self.product_combo = QComboBox()
        if products:
            self.product_combo.addItems(products)
        if product_name:
            idx = self.product_combo.findText(product_name)
            if idx >= 0:
                self.product_combo.setCurrentIndex(idx)
            else:
                self.product_combo.insertItem(0, product_name)
                self.product_combo.setCurrentIndex(0)

        self.sph_spin = QDoubleSpinBox()
        self.sph_spin.setRange(-30.0, 30.0)
        self.sph_spin.setSingleStep(0.25)
        self.sph_spin.setDecimals(2)
        self.sph_spin.setValue(sph)

        self.cyl_spin = QDoubleSpinBox()
        self.cyl_spin.setRange(-10.0, 10.0)
        self.cyl_spin.setSingleStep(0.25)
        self.cyl_spin.setDecimals(2)
        if cyl is not None:
            self.cyl_spin.setValue(cyl)
        else:
            self.cyl_spin.clear()

        self.ax_spin = QSpinBox()
        self.ax_spin.setRange(0, 180)
        if ax is not None:
            self.ax_spin.setValue(ax)
        else:
            self.ax_spin.clear()

        self.bc_spin = QDoubleSpinBox()
        self.bc_spin.setRange(8.0, 9.0)
        self.bc_spin.setSingleStep(0.1)
        self.bc_spin.setDecimals(2)
        if bc is not None:
            self.bc_spin.setValue(bc)
        else:
            self.bc_spin.clear()

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 20)
        self.qty_spin.setValue(qty)

        layout.addRow("Товар", self.product_combo)
        layout.addRow("SPH", self.sph_spin)
        layout.addRow("CYL (пусто если нет)", self.cyl_spin)
        layout.addRow("AX (пусто если нет)", self.ax_spin)
        layout.addRow("BC (пусто если нет)", self.bc_spin)
        layout.addRow("Количество", self.qty_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        product_name = self.product_combo.currentText().strip()
        sph = float(self.sph_spin.value())
        cyl_text = self.cyl_spin.text().strip()
        ax_text = self.ax_spin.text().strip()
        bc_text = self.bc_spin.text().strip()
        qty = int(self.qty_spin.value())

        cyl = float(cyl_text) if cyl_text else None
        ax = int(ax_text) if ax_text else None
        bc = float(bc_text) if bc_text else None

        if not validate_sph(sph):
            QMessageBox.warning(self, "Ошибка", "SPH должен быть в диапазоне [-30; 30] с шагом 0.25.")
            return None
        if cyl is not None and not validate_cyl(cyl):
            QMessageBox.warning(self, "Ошибка", "CYL должен быть в диапазоне [-10; 10] с шагом 0.25.")
            return None
        if ax is not None and not validate_ax(ax):
            QMessageBox.warning(self, "Ошибка", "AX должен быть в диапазоне [0; 180] с шагом 1.")
            return None
        if bc is not None and not validate_bc(bc):
            QMessageBox.warning(self, "Ошибка", "BC должен быть в диапазоне [8.0; 9.0] с шагом 0.1.")
            return None
        if not validate_qty(qty):
            QMessageBox.warning(self, "Ошибка", "Количество должно быть от 1 до 20.")
            return None

        return product_name, sph, cyl, ax, bc, qty


class MKLWindow(QWidget):
    def __init__(self, db: Database, export_dir: str):
        super().__init__()
        self.db = db
        self.export_dir = export_dir
        self.setWindowTitle("Заказы МКЛ — УссурОЧки.рф")

        self.tabs = QTabWidget()
        self.clients_tab = QWidget()
        self.products_tab = QWidget()
        self.orders_tab = QWidget()

        self.tabs.addTab(self.clients_tab, "Клиенты")
        self.tabs.addTab(self.products_tab, "Товары")
        self.tabs.addTab(self.orders_tab, "Заказы")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tabs)

        self._setup_clients_tab()
        self._setup_products_tab()
        self._setup_orders_tab()

    # --------- Клиенты ----------
    def _setup_clients_tab(self):
        layout = QVBoxLayout(self.clients_tab)
        controls = QHBoxLayout()
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Поиск по ФИО или телефону")
        btn_add = QPushButton("Добавить")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")

        controls.addWidget(QLabel("Поиск:"))
        controls.addWidget(self.client_search)
        controls.addWidget(btn_add)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_del)

        self.clients_table = QTableWidget(0, 3)
        self.clients_table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.clients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.clients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.clients_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.clients_table.customContextMenuRequested.connect(self._clients_context_menu)

        layout.addLayout(controls)
        layout.addWidget(self.clients_table)

        self.client_search.textChanged.connect(self.refresh_clients)
        btn_add.clicked.connect(self._add_client)
        btn_edit.clicked.connect(self._edit_client)
        btn_del.clicked.connect(self._del_client)

        self.refresh_clients()

    def refresh_clients(self):
        rows = self.db.list_clients(search=self.client_search.text().strip())
        self.clients_table.setRowCount(0)
        for r in rows:
            row = self.clients_table.rowCount()
            self.clients_table.insertRow(row)
            self.clients_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.clients_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.clients_table.setItem(row, 2, QTableWidgetItem(r["phone"] or ""))

    def _selected_id(self, table: QTableWidget) -> Optional[int]:
        indexes = table.selectionModel().selectedRows()
        if not indexes:
            return None
        row = indexes[0].row()
        id_item = table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def _clients_context_menu(self, pos):
        menu = QMenu(self)
        act_add = QAction("Добавить", self)
        act_edit = QAction("Редактировать", self)
        act_del = QAction("Удалить", self)
        act_add.triggered.connect(self._add_client)
        act_edit.triggered.connect(self._edit_client)
        act_del.triggered.connect(self._del_client)
        menu.addAction(act_add)
        menu.addAction(act_edit)
        menu.addAction(act_del)
        menu.exec(self.clients_table.mapToGlobal(pos))

    def _add_client(self):
        dlg = ClientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data:
                name, phone = data
                self.db.add_client(name, phone)
                self.refresh_clients()

    def _edit_client(self):
        client_id = self._selected_id(self.clients_table)
        if not client_id:
            return
        # Получить текущие значения
        rows = self.db.list_clients()
        row = next((r for r in rows if r["id"] == client_id), None)
        if not row:
            return
        dlg = ClientDialog(self, name=row["name"], phone=row["phone"] or "")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data:
                name, phone = data
                self.db.update_client(client_id, name, phone)
                self.refresh_clients()

    def _del_client(self):
        client_id = self._selected_id(self.clients_table)
        if not client_id:
            return
        if QMessageBox.question(self, "Удалить", "Удалить клиента?") == QMessageBox.StandardButton.Yes:
            self.db.delete_client(client_id)
            self.refresh_clients()

    # --------- Товары ----------
    def _setup_products_tab(self):
        layout = QVBoxLayout(self.products_tab)
        controls = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")

        controls.addWidget(btn_add)
        controls.addWidget(btn_edit)
        controls.addWidget(btn_del)

        self.products_table = QTableWidget(0, 2)
        self.products_table.setHorizontalHeaderLabels(["ID", "Название"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self._products_context_menu)

        layout.addLayout(controls)
        layout.addWidget(self.products_table)

        btn_add.clicked.connect(self._add_product)
        btn_edit.clicked.connect(self._edit_product)
        btn_del.clicked.connect(self._del_product)

        self.refresh_products()

    def refresh_products(self):
        rows = self.db.list_products("mkl")
        self.products_table.setRowCount(0)
        for r in rows:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.products_table.setItem(row, 1, QTableWidgetItem(r["name"]))

    def _products_context_menu(self, pos):
        menu = QMenu(self)
        act_add = QAction("Добавить", self)
        act_edit = QAction("Редактировать", self)
        act_del = QAction("Удалить", self)
        act_add.triggered.connect(self._add_product)
        act_edit.triggered.connect(self._edit_product)
        act_del.triggered.connect(self._del_product)
        menu.addAction(act_add)
        menu.addAction(act_edit)
        menu.addAction(act_del)
        menu.exec(self.products_table.mapToGlobal(pos))

    def _selected_product_id(self) -> Optional[int]:
        return self._selected_id(self.products_table)

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_data()
            if name:
                try:
                    self.db.add_product("mkl", name)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось добавить товар: {e}")
                self.refresh_products()

    def _edit_product(self):
        pid = self._selected_product_id()
        if not pid:
            return
        rows = self.db.list_products("mkl")
        row = next((r for r in rows if r["id"] == pid), None)
        if not row:
            return
        dlg = ProductDialog(self, name=row["name"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_data()
            if name:
                try:
                    self.db.update_product("mkl", pid, name)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось обновить товар: {e}")
                self.refresh_products()

    def _del_product(self):
        pid = self._selected_product_id()
        if not pid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить товар?") == QMessageBox.StandardButton.Yes:
            self.db.delete_product("mkl", pid)
            self.refresh_products()

    # --------- Заказы ----------
    def _setup_orders_tab(self):
        layout = QVBoxLayout(self.orders_tab)
        controls = QHBoxLayout()

        self.order_search = QLineEdit()
        self.order_search.setPlaceholderText("Поиск по ФИО или телефону клиента")
        self.status_combo = QComboBox()
        self.status_combo.addItem("Все")
        self.status_combo.addItems(MKL_STATUSES)
        btn_add = QPushButton("Создать заказ")
        btn_edit_items = QPushButton("Редактировать позиции")
        btn_status = QPushButton("Изменить статус")
        btn_del = QPushButton("Удалить")
        btn_export = QPushButton("Экспорт по статусу")

        controls.addWidget(QLabel("Статус:"))
        controls.addWidget(self.status_combo)
        controls.addWidget(QLabel("Поиск:"))
        controls.addWidget(self.order_search)
        controls.addWidget(btn_add)
        controls.addWidget(btn_edit_items)
        controls.addWidget(btn_status)
        controls.addWidget(btn_del)
        controls.addWidget(btn_export)

        self.orders_table = QTableWidget(0, 5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Клиент", "Телефон", "Статус", "Дата"])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self._orders_context_menu)

        layout.addLayout(controls)
        layout.addWidget(self.orders_table)

        self.order_search.textChanged.connect(self.refresh_orders)
        self.status_combo.currentIndexChanged.connect(self.refresh_orders)
        btn_add.clicked.connect(self._create_order)
        btn_edit_items.clicked.connect(self._edit_order_items)
        btn_status.clicked.connect(self._change_status)
        btn_del.clicked.connect(self._del_order)
        btn_export.clicked.connect(self._export_orders)

        self.refresh_orders()

    def refresh_orders(self):
        status = None if self.status_combo.currentText() == "Все" else self.status_combo.currentText()
        search = self.order_search.text().strip()
        rows = self.db.list_orders_mkl(status_filter=status, search=search)
        self.orders_table.setRowCount(0)
        for r in rows:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(r["client_name"]))
            self.orders_table.setItem(row, 2, QTableWidgetItem(r["client_phone"] or ""))
            status_item = QTableWidgetItem(r["status"])
            status_item.setForeground(self._status_color_brush(r["status"]))
            self.orders_table.setItem(row, 3, status_item)
            self.orders_table.setItem(row, 4, QTableWidgetItem(r["created_at"]))

    def _status_color_brush(self, status: str):
        color_map = {
            "Не заказан": QColor(220, 38, 38),  # красный
            "Заказан": QColor(34, 197, 94),     # зелёный
            "Прозвонен": QColor(234, 179, 8),   # жёлтый
            "Вручен": QColor(59, 130, 246),     # синий
        }
        return color_map.get(status, QColor(255, 255, 255))

    def _orders_context_menu(self, pos):
        menu = QMenu(self)
        act_add = QAction("Создать заказ", self)
        act_edit_items = QAction("Редактировать позиции", self)
        act_status = QAction("Изменить статус", self)
        act_del = QAction("Удалить", self)
        act_add.triggered.connect(self._create_order)
        act_edit_items.triggered.connect(self._edit_order_items)
        act_status.triggered.connect(self._change_status)
        act_del.triggered.connect(self._del_order)
        menu.addAction(act_add)
        menu.addAction(act_edit_items)
        menu.addAction(act_status)
        menu.addAction(act_del)
        menu.exec(self.orders_table.mapToGlobal(pos))

    def _selected_order_id(self) -> Optional[int]:
        return self._selected_id(self.orders_table)

    def _create_order(self):
        # выбрать клиента
        clients = self.db.list_clients()
        if not clients:
            QMessageBox.information(self, "Клиенты", "Добавьте клиентов в разделе 'Клиенты'.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Создать заказ: выбор клиента и статуса")
        fl = QFormLayout(dlg)
        combo_client = QComboBox()
        for c in clients:
            combo_client.addItem(f'{c["name"]} ({c["phone"] or "-"})', c["id"])
        combo_status = QComboBox()
        combo_status.addItems(MKL_STATUSES)
        fl.addRow("Клиент", combo_client)
        fl.addRow("Статус", combo_status)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        fl.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            client_id = combo_client.currentData()
            status = combo_status.currentText()
            order_id = self.db.create_order_mkl(client_id, status)
            self.refresh_orders()
            # сразу предложить добавить позиции
            if QMessageBox.question(self, "Позиции", "Добавить позиции сейчас?") == QMessageBox.StandardButton.Yes:
                self._edit_order_items(order_id)

    def _edit_order_items(self, order_id: Optional[int] = None):
        oid = order_id or self._selected_order_id()
        if not oid:
            return
        # диалог редактирования позиций
        dlg = QDialog(self)
        dlg.setWindowTitle("Позиции заказа (МКЛ)")
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(["ID", "Товар", "SPH", "CYL", "AX", "BC", "Qty"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        btns = QHBoxLayout()
        btn_add = QPushButton("Добавить позицию")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")
        btns.addWidget(btn_add)
        btns.addWidget(btn_edit)
        btns.addWidget(btn_del)

        layout.addWidget(table)
        layout.addLayout(btns)

        products = [p["name"] for p in self.db.list_products("mkl")]

        def refresh_items():
            table.setRowCount(0)
            items = self.db.list_order_items_mkl(oid)
            for it in items:
                r = table.rowCount()
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem(str(it["id"])))
                table.setItem(r, 1, QTableWidgetItem(it["product_name"]))
                table.setItem(r, 2, QTableWidgetItem(str(it["sph"])))
                table.setItem(r, 3, QTableWidgetItem("" if it["cyl"] is None else str(it["cyl"])))
                table.setItem(r, 4, QTableWidgetItem("" if it["ax"] is None else str(it["ax"])))
                table.setItem(r, 5, QTableWidgetItem("" if it["bc"] is None else str(it["bc"])))
                table.setItem(r, 6, QTableWidgetItem(str(it["qty"])))

        refresh_items()

        def selected_item_id() -> Optional[int]:
            idxs = table.selectionModel().selectedRows()
            if not idxs:
                return None
            row = idxs[0].row()
            item = table.item(row, 0)
            return int(item.text()) if item else None

        def add_item():
            idlg = OrderItemDialog(self, products=products)
            if idlg.exec() == QDialog.DialogCode.Accepted:
                data = idlg.get_data()
                if data:
                    product_name, sph, cyl, ax, bc, qty = data
                    self.db.add_order_item_mkl(oid, product_name, sph, cyl, ax, bc, qty)
                    refresh_items()

        def edit_item():
            iid = selected_item_id()
            if not iid:
                return
            # получить текущие значения
            items = self.db.list_order_items_mkl(oid)
            it = next((x for x in items if x["id"] == iid), None)
            if not it:
                return
            idlg = OrderItemDialog(
                self,
                product_name=it["product_name"],
                sph=float(it["sph"]),
                cyl=None if it["cyl"] is None else float(it["cyl"]),
                ax=None if it["ax"] is None else int(it["ax"]),
                bc=None if it["bc"] is None else float(it["bc"]),
                qty=int(it["qty"]),
                products=products,
            )
            if idlg.exec() == QDialog.DialogCode.Accepted:
                data = idlg.get_data()
                if data:
                    product_name, sph, cyl, ax, bc, qty = data
                    self.db.update_order_item_mkl(iid, product_name, sph, cyl, ax, bc, qty)
                    refresh_items()

        def del_item():
            iid = selected_item_id()
            if not iid:
                return
            if QMessageBox.question(dlg, "Удалить", "Удалить позицию?") == QMessageBox.StandardButton.Yes:
                self.db.delete_order_item_mkl(iid)
                refresh_items()

        btn_add.clicked.connect(add_item)
        btn_edit.clicked.connect(edit_item)
        btn_del.clicked.connect(del_item)

        dlg.exec()

    def _change_status(self):
        oid = self._selected_order_id()
        if not oid:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Изменить статус заказа")
        fl = QFormLayout(dlg)
        combo = QComboBox()
        combo.addItems(MKL_STATUSES)
        fl.addRow("Статус", combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        fl.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            status = combo.currentText()
            self.db.update_order_mkl_status(oid, status)
            self.refresh_orders()

    def _del_order(self):
        oid = self._selected_order_id()
        if not oid:
            return
        if QMessageBox.question(self, "Удалить", "Удалить заказ?") == QMessageBox.StandardButton.Yes:
            self.db.delete_order_mkl(oid)
            self.refresh_orders()

    def _export_orders(self):
        # выбрать статус
        dlg = QDialog(self)
        dlg.setWindowTitle("Экспорт заказов по статусу")
        fl = QFormLayout(dlg)
        combo = QComboBox()
        combo.addItems(MKL_STATUSES)
        fl.addRow("Статус", combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        fl.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            status = combo.currentText()
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить TXT",
                self.export_dir,
                "TXT файлы (*.txt)",
            )
            if path:
                try:
                    self.db.export_orders_mkl(status, path)
                    QMessageBox.information(self, "Экспорт", "Файл успешно сохранён.")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось экспортировать: {e}")