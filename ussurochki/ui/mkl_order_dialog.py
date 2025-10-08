from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QMessageBox,
    QHeaderView,
)

from ..db import Database
from ..utils import is_valid_phone
from .widgets import OptionalDoubleSpin, OptionalIntSpin


class MKLOrderDialog(QDialog):
    def __init__(self, db: Database, parent=None, order_id: Optional[int] = None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle("Заказ МКЛ")

        self.cmb_client = QComboBox()
        self._load_clients()

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Не заказан", "Заказан", "Прозвонен", "Вручен"])

        self.btn_add_row = QPushButton("Добавить позицию")
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_del_row = QPushButton("Удалить позицию")
        self.btn_del_row.clicked.connect(self.delete_row)

        header = QHBoxLayout()
        header.addWidget(QLabel("Клиент:"))
        header.addWidget(self.cmb_client, 2)
        header.addWidget(QLabel("Статус:"))
        header.addWidget(self.cmb_status, 1)
        header.addStretch(1)
        header.addWidget(self.btn_add_row)
        header.addWidget(self.btn_del_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Товар", "SPH", "CYL", "AX", "BC", "Кол-во"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self.save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        lay = QVBoxLayout(self)
        lay.addLayout(header)
        lay.addWidget(self.table, 1)
        lay.addLayout(btns)
        self.resize(900, 600)

        if self.order_id:
            self._load_order()
        else:
            self.add_row()

    def _load_clients(self):
        self.cmb_client.clear()
        clients = self.db.list_clients()
        for c in clients:
            display = f"{c['full_name']} ({c['phone'] or '—'})"
            self.cmb_client.addItem(display, c["id"])

    def _load_products(self):
        return self.db.list_products_mkl()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Product combobox
        cmb_prod = QComboBox()
        for p in self._load_products():
            cmb_prod.addItem(p["name"], p["id"])
        self.table.setCellWidget(row, 0, cmb_prod)

        # SPH
        sph = OptionalDoubleSpin(decimals=2, minimum=-30.0, maximum=30.0, step=0.25, placeholder="0.00")
        sph.setValue(0.0)
        self.table.setCellWidget(row, 1, sph)

        # CYL
        cyl = OptionalDoubleSpin(decimals=2, minimum=-10.0, maximum=10.0, step=0.25, placeholder="пусто")
        cyl.setValue(None)
        self.table.setCellWidget(row, 2, cyl)

        # AX
        ax = OptionalIntSpin(minimum=0, maximum=180, step=1, placeholder="пусто")
        ax.setValue(None)
        self.table.setCellWidget(row, 3, ax)

        # BC
        bc = OptionalDoubleSpin(decimals=1, minimum=8.0, maximum=9.0, step=0.1, placeholder="пусто")
        bc.setValue(None)
        self.table.setCellWidget(row, 4, bc)

        # QTY
        qty = QComboBox()
        qty.addItems([str(i) for i in range(1, 21)])
        qty.setCurrentText("1")
        self.table.setCellWidget(row, 5, qty)

    def delete_row(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.table.removeRow(rows[0].row())

    def _load_order(self):
        orders = self.db.list_orders_mkl()
        cur = next((o for o in orders if o["id"] == self.order_id), None)
        if not cur:
            return
        idx = self.cmb_client.findData(cur["client_id"]) if "client_id" in cur else -1
        if idx >= 0:
            self.cmb_client.setCurrentIndex(idx)
        st_idx = self.cmb_status.findText(cur["status"])
        if st_idx >= 0:
            self.cmb_status.setCurrentIndex(st_idx)
        for it in cur["items"]:
            self.add_row()
            row = self.table.rowCount() - 1
            cmb_prod: QComboBox = self.table.cellWidget(row, 0)  # type: ignore
            cmb_prod.setCurrentIndex(cmb_prod.findData(it["product_id"]))
            sph: OptionalDoubleSpin = self.table.cellWidget(row, 1)  # type: ignore
            sph.setValue(float(it["sph"]))
            cyl: OptionalDoubleSpin = self.table.cellWidget(row, 2)  # type: ignore
            cyl.setValue(it.get("cyl"))
            ax: OptionalIntSpin = self.table.cellWidget(row, 3)  # type: ignore
            ax.setValue(it.get("ax"))
            bc: OptionalDoubleSpin = self.table.cellWidget(row, 4)  # type: ignore
            bc.setValue(it.get("bc"))
            qty: QComboBox = self.table.cellWidget(row, 5)  # type: ignore
            qty.setCurrentText(str(it["qty"]))

    def _collect_items(self) -> Optional[List[dict]]:
        items = []
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну позицию.")
            return None
        for row in range(self.table.rowCount()):
            cmb_prod: QComboBox = self.table.cellWidget(row, 0)  # type: ignore
            sph: OptionalDoubleSpin = self.table.cellWidget(row, 1)  # type: ignore
            cyl: OptionalDoubleSpin = self.table.cellWidget(row, 2)  # type: ignore
            ax: OptionalIntSpin = self.table.cellWidget(row, 3)  # type: ignore
            bc: OptionalDoubleSpin = self.table.cellWidget(row, 4)  # type: ignore
            qty: QComboBox = self.table.cellWidget(row, 5)  # type: ignore

            product_id = cmb_prod.currentData()
            if product_id is None:
                QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: выберите товар.")
                return None

            sph_val = sph.value()
            if sph_val is None:
                sph_val = 0.0
            if sph_val < -30.0 or sph_val > 30.0 or round((sph_val - 0.0) / 0.25, 2) % 1 != 0:
                QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: SPH должен быть от -30.0 до +30.0 с шагом 0.25.")
                return None

            cyl_val = cyl.value()
            if cyl_val is not None:
                if cyl_val < -10.0 or cyl_val > 10.0 or round((cyl_val - 0.0) / 0.25, 2) % 1 != 0:
                    QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: CYL должен быть от -10.0 до +10.0 с шагом 0.25.")
                    return None

            ax_val = ax.value()
            if ax_val is not None:
                if ax_val < 0 or ax_val > 180:
                    QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: AX должен быть от 0 до 180.")
                    return None

            bc_val = bc.value()
            if bc_val is not None:
                if bc_val < 8.0 or bc_val > 9.0 or round((bc_val - 8.0) / 0.1, 2) % 1 != 0:
                    QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: BC должен быть от 8.0 до 9.0 с шагом 0.1.")
                    return None

            qty_val = int(qty.currentText())
            if qty_val < 1 or qty_val > 20:
                QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: Количество от 1 до 20.")
                return None

            items.append({
                "product_id": int(product_id),
                "sph": float(sph_val),
                "cyl": float(cyl_val) if cyl_val is not None else None,
                "ax": int(ax_val) if ax_val is not None else None,
                "bc": float(bc_val) if bc_val is not None else None,
                "qty": qty_val,
            })
        return items

    def save(self):
        client_id = self.cmb_client.currentData()
        if client_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента.")
            return
        items = self._collect_items()
        if items is None:
            return
        status = self.cmb_status.currentText()
        if self.order_id:
            self.db.update_order_mkl(self.order_id, client_id, status, items)
        else:
            self.db.create_order_mkl(client_id, status, items)
        self.accept()