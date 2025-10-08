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
from .widgets import OptionalDoubleSpin, OptionalIntSpin


class MeridianOrderDialog(QDialog):
    def __init__(self, db: Database, parent=None, order_id: Optional[int] = None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle("Заказ Меридиан")

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Не заказан", "Заказан"])

        self.btn_add_row = QPushButton("Добавить позицию")
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_del_row = QPushButton("Удалить позицию")
        self.btn_del_row.clicked.connect(self.delete_row)

        header = QHBoxLayout()
        header.addWidget(QLabel("Статус:"))
        header.addWidget(self.cmb_status, 1)
        header.addStretch(1)
        header.addWidget(self.btn_add_row)
        header.addWidget(self.btn_del_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Товар", "SPH", "CYL", "AX", "Кол-во"])
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

    def _load_products(self):
        return self.db.list_products_meridian()

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

        # QTY
        qty = QComboBox()
        qty.addItems([str(i) for i in range(1, 21)])
        qty.setCurrentText("1")
        self.table.setCellWidget(row, 4, qty)

    def delete_row(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.table.removeRow(rows[0].row())

    def _load_order(self):
        orders = self.db.list_orders_meridian()
        cur = next((o for o in orders if o["id"] == self.order_id), None)
        if not cur:
            return
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
            qty: QComboBox = self.table.cellWidget(row, 4)  # type: ignore
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
            qty: QComboBox = self.table.cellWidget(row, 4)  # type: ignore

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

            qty_val = int(qty.currentText())
            if qty_val < 1 or qty_val > 20:
                QMessageBox.warning(self, "Ошибка", f"Строка {row+1}: Количество от 1 до 20.")
                return None

            items.append({
                "product_id": int(product_id),
                "sph": float(sph_val),
                "cyl": float(cyl_val) if cyl_val is not None else None,
                "ax": int(ax_val) if ax_val is not None else None,
                "qty": qty_val,
            })
        return items

    def save(self):
        items = self._collect_items()
        if items is None:
            return
        status = self.cmb_status.currentText()
        if self.order_id:
            self.db.update_order_meridian(self.order_id, status, items)
        else:
            self.db.create_order_meridian(status, items)
        self.accept()