import sqlite3
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
)

from ..models import OrderStatus
from ..repo import (
    get_order_mkl,
    get_order_meridian,
    save_order_mkl,
    save_order_meridian,
    list_products_mkl,
    list_products_meridian,
    normalize_phone,
)


class OptionalDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None, step=0.25) -> None:
        super().__init__(parent)
        self._is_optional = True
        self._empty_value = -1e9
        self.setDecimals(2)
        self.setSingleStep(step)
        self.setMinimum(self._empty_value)
        self.setSpecialValueText("")  # shows empty when value == minimum

    def valueOrNone(self) -> Optional[float]:
        v = super().value()
        if v == self._empty_value:
            return None
        return v

    def setNone(self) -> None:
        super().setValue(self._empty_value)


class OptionalSpinBox(QSpinBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._is_optional = True
        self._empty_value = -10_000
        self.setMinimum(self._empty_value)
        self.setSpecialValueText("")

    def valueOrNone(self) -> Optional[int]:
        v = super().value()
        if v == self._empty_value:
            return None
        return v

    def setNone(self) -> None:
        super().setValue(self._empty_value)


def _is_multiple(value: float, step: float) -> bool:
    if value is None:
        return True
    scaled = round(value / step)
    return abs(value - (scaled * step)) < 1e-6


class MKLOrderDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, order_id: Optional[int] = None, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.order_id = order_id
        self.setWindowTitle("Карточка заказа МКЛ")
        self.resize(900, 600)
        self._make_ui()
        self._load()

    def _make_ui(self) -> None:
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        phone_re = QRegularExpression(r"^(\+7|8)-?\d{3}-?\d{3}-?\d{2}-?\d{2}$")
        self.phone_edit.setValidator(QRegularExpressionValidator(phone_re))
        self.status_combo = QComboBox()
        for s in [OrderStatus.NOT_ORDERED, OrderStatus.ORDERED, OrderStatus.CALLED, OrderStatus.DELIVERED]:
            self.status_combo.addItem(s.to_text(), int(s))

        top_form = QHBoxLayout()
        top_form.addWidget(QLabel("ФИО:"))
        top_form.addWidget(self.name_edit, stretch=1)
        top_form.addWidget(QLabel("Телефон:"))
        top_form.addWidget(self.phone_edit, stretch=1)
        top_form.addWidget(QLabel("Статус:"))
        top_form.addWidget(self.status_combo)

        self.items_table = QTableWidget(0, 7)
        self.items_table.setHorizontalHeaderLabels(["Товар", "Глаз", "Sph", "Cyl", "Ax", "BC", "Количество"])
        self.items_table.horizontalHeader().setStretchLastSection(True)

        add_row_btn = QPushButton("Добавить позицию")
        add_both_btn = QPushButton("Добавить для обоих глаз")
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        add_row_btn.clicked.connect(self._add_item_row)
        add_both_btn.clicked.connect(self._add_both)
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(add_row_btn)
        buttons.addWidget(add_both_btn)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_form)
        layout.addWidget(self.items_table)
        layout.addLayout(buttons)

    def _load(self) -> None:
        self._products = list_products_mkl(self.conn)
        if not self._products:
            # Seed one product to allow usage
            from ..repo import add_product_mkl

            add_product_mkl(self.conn, "Линзы MKL A")
            add_product_mkl(self.conn, "Линзы MKL B")
            self._products = list_products_mkl(self.conn)
        if self.order_id is not None:
            data = get_order_mkl(self.conn, self.order_id)
            o = data["order"]
            self.name_edit.setText(o["client_name"])
            self.phone_edit.setText(o["client_phone"] or "")
            self.status_combo.setCurrentIndex([int(d) for d in self.status_combo.model().match(
                self.status_combo.model().index(0, 0), Qt.DisplayRole, OrderStatus(int(o["status"])).to_text(), hits=1, flags=Qt.MatchExactly
            )][0] if self.status_combo.count() else 0)
            for it in data["items"]:
                self._add_item_row(prefill=it)
        else:
            self._add_item_row()

    def _add_item_row(self, prefill: Optional[Dict[str, Any]] = None) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        product_combo = QComboBox()
        for p in self._products:
            product_combo.addItem(p["name"], p["id"])
        if prefill and "product_id" in prefill:
            idx = product_combo.findData(prefill["product_id"])
            if idx >= 0:
                product_combo.setCurrentIndex(idx)

        eye_combo = QComboBox()
        eye_combo.addItems(["OD", "OS"])
        if prefill and "eye" in prefill:
            idx = eye_combo.findText(prefill["eye"])
            if idx >= 0:
                eye_combo.setCurrentIndex(idx)

        sph_spin = QDoubleSpinBox()
        sph_spin.setRange(-30.00, 30.00)
        sph_spin.setDecimals(2)
        sph_spin.setSingleStep(0.25)
        sph_spin.setValue(0.00 if not prefill else float(prefill.get("sph", 0.00)))

        cyl_spin = OptionalDoubleSpinBox(step=0.25)
        cyl_spin.setMaximum(10.00)
        if prefill and prefill.get("cyl") is not None:
            cyl_spin.setValue(float(prefill["cyl"]))
        else:
            cyl_spin.setNone()

        ax_spin = OptionalSpinBox()
        ax_spin.setMaximum(180)
        if prefill and prefill.get("ax") is not None:
            ax_spin.setValue(int(prefill["ax"]))
        else:
            ax_spin.setNone()
        ax_spin.setEnabled(cyl_spin.valueOrNone() is not None)
        cyl_spin.valueChanged.connect(lambda _: ax_spin.setEnabled(cyl_spin.valueOrNone() is not None))

        bc_spin = OptionalDoubleSpinBox(step=0.1)
        bc_spin.setMaximum(9.0)
        bc_spin.setDecimals(1)
        if prefill and prefill.get("bc") is not None:
            bc_spin.setValue(float(prefill["bc"]))
        else:
            bc_spin.setNone()

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 20)
        qty_spin.setValue(int(prefill.get("quantity", 1)) if prefill else 1)

        self.items_table.setCellWidget(row, 0, product_combo)
        self.items_table.setCellWidget(row, 1, eye_combo)
        self.items_table.setCellWidget(row, 2, sph_spin)
        self.items_table.setCellWidget(row, 3, cyl_spin)
        self.items_table.setCellWidget(row, 4, ax_spin)
        self.items_table.setCellWidget(row, 5, bc_spin)
        self.items_table.setCellWidget(row, 6, qty_spin)

    def _add_both(self) -> None:
        # Add two identical rows with OD and OS
        row_template = {
            "sph": 0.00,
            "cyl": None,
            "ax": None,
            "bc": None,
            "quantity": 1,
            "product_id": self._products[0]["id"] if self._products else None,
            "eye": "OD",
        }
        self._add_item_row(prefill=row_template)
        row_template["eye"] = "OS"
        self._add_item_row(prefill=row_template)

    def _collect_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for row in range(self.items_table.rowCount()):
            product_combo: QComboBox = self.items_table.cellWidget(row, 0)  # type: ignore
            eye_combo: QComboBox = self.items_table.cellWidget(row, 1)  # type: ignore
            sph_spin: QDoubleSpinBox = self.items_table.cellWidget(row, 2)  # type: ignore
            cyl_spin: OptionalDoubleSpinBox = self.items_table.cellWidget(row, 3)  # type: ignore
            ax_spin: OptionalSpinBox = self.items_table.cellWidget(row, 4)  # type: ignore
            bc_spin: OptionalDoubleSpinBox = self.items_table.cellWidget(row, 5)  # type: ignore
            qty_spin: QSpinBox = self.items_table.cellWidget(row, 6)  # type: ignore

            product_id = product_combo.currentData()
            eye = eye_combo.currentText()
            sph = float(sph_spin.value())
            cyl = cyl_spin.valueOrNone()
            ax = ax_spin.valueOrNone()
            bc = bc_spin.valueOrNone()
            qty = int(qty_spin.value())

            if eye not in {"OD", "OS"}:
                raise ValueError("Глаз должен быть OD/OS")
            if not _is_multiple(sph, 0.25) or not (-30.00 <= sph <= 30.00):
                raise ValueError("Sph должен быть в диапазоне −30.00…+30.00 с шагом 0.25")
            if cyl is not None and (not _is_multiple(cyl, 0.25) or not (-10.00 <= cyl <= 10.00)):
                raise ValueError("Cyl должен быть в диапазоне −10.00…+10.00 с шагом 0.25")
            if ax is not None and cyl is None:
                raise ValueError("Ax доступен только если заполнен Cyl")
            if ax is not None and not (0 <= ax <= 180):
                raise ValueError("Ax должен быть 0…180, шаг 1")
            if bc is not None and (not _is_multiple(bc, 0.1) or not (8.0 <= bc <= 9.0)):
                raise ValueError("BC должен быть 8.0…9.0 с шагом 0.1")
            if not (1 <= qty <= 20):
                raise ValueError("Количество: 1…20")

            items.append(
                {
                    "product_id": product_id,
                    "eye": eye,
                    "sph": sph,
                    "cyl": cyl,
                    "ax": ax,
                    "bc": bc,
                    "quantity": qty,
                }
            )
        return items

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно.")
            return
        phone_raw = self.phone_edit.text().strip()
        phone_norm = normalize_phone(phone_raw) if phone_raw else None
        if phone_raw and not phone_norm:
            QMessageBox.warning(self, "Ошибка", "Телефон должен быть в формате +7-XXX-XXX-XX-XX или 8-XXX-XXX-XX-XX.")
            return
        status = OrderStatus(self.status_combo.currentData())
        try:
            items = self._collect_items()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка в позициях", str(e))
            return
        oid = save_order_mkl(self.conn, self.order_id, name, phone_norm, status, items)
        self.order_id = oid
        self.accept()


class MeridianOrderDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, order_id: Optional[int] = None, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.order_id = order_id
        self.setWindowTitle("Карточка заказа Меридиан")
        self.resize(900, 600)
        self._make_ui()
        self._load()

    def _make_ui(self) -> None:
        self.num_edit = QLineEdit()
        self.status_combo = QComboBox()
        for s in [OrderStatus.NOT_ORDERED, OrderStatus.ORDERED, OrderStatus.CALLED, OrderStatus.DELIVERED]:
            self.status_combo.addItem(s.to_text(), int(s))

        top_form = QHBoxLayout()
        top_form.addWidget(QLabel("№ заказа:"))
        top_form.addWidget(self.num_edit, stretch=1)
        top_form.addWidget(QLabel("Статус:"))
        top_form.addWidget(self.status_combo)

        self.items_table = QTableWidget(0, 7)
        self.items_table.setHorizontalHeaderLabels(["Товар", "Глаз", "Sph", "Cyl", "Ax", "D", "Количество"])
        self.items_table.horizontalHeader().setStretchLastSection(True)

        add_row_btn = QPushButton("Добавить позицию")
        add_both_btn = QPushButton("Добавить для обоих глаз")
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        add_row_btn.clicked.connect(self._add_item_row)
        add_both_btn.clicked.connect(self._add_both)
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(add_row_btn)
        buttons.addWidget(add_both_btn)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_form)
        layout.addWidget(self.items_table)
        layout.addLayout(buttons)

    def _load(self) -> None:
        self._products = list_products_meridian(self.conn)
        if not self._products:
            from ..repo import add_product_meridian

            add_product_meridian(self.conn, "Линзы Meridian A")
            add_product_meridian(self.conn, "Линзы Meridian B")
            self._products = list_products_meridian(self.conn)
        if self.order_id is not None:
            data = get_order_meridian(self.conn, self.order_id)
            o = data["order"]
            self.num_edit.setText(o["order_number"])
            self.status_combo.setCurrentIndex(
                [int(d) for d in self.status_combo.model().match(
                    self.status_combo.model().index(0, 0), Qt.DisplayRole, OrderStatus(int(o["status"])).to_text(), hits=1, flags=Qt.MatchExactly
                )][0] if self.status_combo.count() else 0
            )
            for it in data["items"]:
                self._add_item_row(prefill=it)
        else:
            self._add_item_row()

    def _add_item_row(self, prefill: Optional[Dict[str, Any]] = None) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        product_combo = QComboBox()
        for p in self._products:
            product_combo.addItem(p["name"], p["id"])
        if prefill and "product_id" in prefill:
            idx = product_combo.findData(prefill["product_id"])
            if idx >= 0:
                product_combo.setCurrentIndex(idx)

        eye_combo = QComboBox()
        eye_combo.addItems(["OD", "OS"])
        if prefill and "eye" in prefill:
            idx = eye_combo.findText(prefill["eye"])
            if idx >= 0:
                eye_combo.setCurrentIndex(idx)

        sph_spin = QDoubleSpinBox()
        sph_spin.setRange(-30.00, 30.00)
        sph_spin.setDecimals(2)
        sph_spin.setSingleStep(0.25)
        sph_spin.setValue(0.00 if not prefill else float(prefill.get("sph", 0.00)))

        cyl_spin = OptionalDoubleSpinBox(step=0.25)
        cyl_spin.setMaximum(10.00)
        if prefill and prefill.get("cyl") is not None:
            cyl_spin.setValue(float(prefill["cyl"]))
        else:
            cyl_spin.setNone()

        ax_spin = OptionalSpinBox()
        ax_spin.setMaximum(180)
        if prefill and prefill.get("ax") is not None:
            ax_spin.setValue(int(prefill["ax"]))
        else:
            ax_spin.setNone()
        ax_spin.setEnabled(cyl_spin.valueOrNone() is not None)
        cyl_spin.valueChanged.connect(lambda _: ax_spin.setEnabled(cyl_spin.valueOrNone() is not None))

        d_spin = OptionalSpinBox()
        d_spin.setMaximum(90)
        d_spin.setSingleStep(5)
        if prefill and prefill.get("d") is not None:
            d_spin.setValue(int(prefill["d"]))
        else:
            d_spin.setNone()

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 20)
        qty_spin.setValue(int(prefill.get("quantity", 1)) if prefill else 1)

        self.items_table.setCellWidget(row, 0, product_combo)
        self.items_table.setCellWidget(row, 1, eye_combo)
        self.items_table.setCellWidget(row, 2, sph_spin)
        self.items_table.setCellWidget(row, 3, cyl_spin)
        self.items_table.setCellWidget(row, 4, ax_spin)
        self.items_table.setCellWidget(row, 5, d_spin)
        self.items_table.setCellWidget(row, 6, qty_spin)

    def _add_both(self) -> None:
        row_template = {
            "sph": 0.00,
            "cyl": None,
            "ax": None,
            "d": None,
            "quantity": 1,
            "product_id": self._products[0]["id"] if self._products else None,
            "eye": "OD",
        }
        self._add_item_row(prefill=row_template)
        row_template["eye"] = "OS"
        self._add_item_row(prefill=row_template)

    def _collect_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for row in range(self.items_table.rowCount()):
            product_combo: QComboBox = self.items_table.cellWidget(row, 0)  # type: ignore
            eye_combo: QComboBox = self.items_table.cellWidget(row, 1)  # type: ignore
            sph_spin: QDoubleSpinBox = self.items_table.cellWidget(row, 2)  # type: ignore
            cyl_spin: OptionalDoubleSpinBox = self.items_table.cellWidget(row, 3)  # type: ignore
            ax_spin: OptionalSpinBox = self.items_table.cellWidget(row, 4)  # type: ignore
            d_spin: OptionalSpinBox = self.items_table.cellWidget(row, 5)  # type: ignore
            qty_spin: QSpinBox = self.items_table.cellWidget(row, 6)  # type: ignore

            product_id = product_combo.currentData()
            eye = eye_combo.currentText()
            sph = float(sph_spin.value())
            cyl = cyl_spin.valueOrNone()
            ax = ax_spin.valueOrNone()
            d = d_spin.valueOrNone()
            qty = int(qty_spin.value())

            if eye not in {"OD", "OS"}:
                raise ValueError("Глаз должен быть OD/OS")
            if not _is_multiple(sph, 0.25) or not (-30.00 <= sph <= 30.00):
                raise ValueError("Sph должен быть в диапазоне −30.00…+30.00 с шагом 0.25")
            if cyl is not None and (not _is_multiple(cyl, 0.25) or not (-10.00 <= cyl <= 10.00)):
                raise ValueError("Cyl должен быть в диапазоне −10.00…+10.00 с шагом 0.25")
            if ax is not None and cyl is None:
                raise ValueError("Ax доступен только если заполнен Cyl")
            if ax is not None and not (0 <= ax <= 180):
                raise ValueError("Ax должен быть 0…180, шаг 1")
            if d is not None and (d % 5 != 0 or not (45 <= d <= 90)):
                raise ValueError("D должен быть 45…90 с шагом 5")
            if not (1 <= qty <= 20):
                raise ValueError("Количество: 1…20")

            items.append(
                {
                    "product_id": product_id,
                    "eye": eye,
                    "sph": sph,
                    "cyl": cyl,
                    "ax": ax,
                    "d": d,
                    "quantity": qty,
                }
            )
        return items

    def _save(self) -> None:
        number = self.num_edit.text().strip()
        if not number:
            QMessageBox.warning(self, "Ошибка", "№ заказа обязателен.")
            return
        status = OrderStatus(self.status_combo.currentData())
        try:
            items = self._collect_items()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка в позициях", str(e))
            return
        oid = save_order_meridian(self.conn, self.order_id, number, status, items)
        self.order_id = oid
        self.accept()