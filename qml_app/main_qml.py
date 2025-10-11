from __future__ import annotations

import os
import sys
from datetime import datetime

from PySide6.QtCore import (QAbstractListModel, QModelIndex, Qt, QByteArray, Slot)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# Reuse existing DB
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import AppDB  # noqa: E402


class MklOrdersModel(QAbstractListModel):
    ROLES = {
        "fio": Qt.UserRole + 1,
        "phone": Qt.UserRole + 2,
        "product": Qt.UserRole + 3,
        "sph": Qt.UserRole + 4,
        "cyl": Qt.UserRole + 5,
        "ax": Qt.UserRole + 6,
        "bc": Qt.UserRole + 7,
        "qty": Qt.UserRole + 8,
        "status": Qt.UserRole + 9,
        "date": Qt.UserRole + 10,
        "comment": Qt.UserRole + 11,
        "commentFlag": Qt.UserRole + 12,
    }

    def __init__(self, db: AppDB):
        super().__init__()
        self._db = db
        self._items: list[dict] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ROLES["fio"]:
            return item.get("fio", "")
        if role == self.ROLES["phone"]:
            return item.get("phone", "")
        if role == self.ROLES["product"]:
            return item.get("product", "")
        if role == self.ROLES["sph"]:
            return item.get("sph", "")
        if role == self.ROLES["cyl"]:
            return item.get("cyl", "")
        if role == self.ROLES["ax"]:
            return item.get("ax", "")
        if role == self.ROLES["bc"]:
            return item.get("bc", "")
        if role == self.ROLES["qty"]:
            return item.get("qty", "")
        if role == self.ROLES["status"]:
            return item.get("status", "")
        if role == self.ROLES["date"]:
            return item.get("date", "")
        if role == self.ROLES["comment"]:
            return item.get("comment", "")
        if role == self.ROLES["commentFlag"]:
            txt = (item.get("comment", "") or "").strip()
            return "ЕСТЬ" if txt else "НЕТ"
        return None

    def roleNames(self):
        return {v: QByteArray(k.encode("utf-8")) for k, v in self.ROLES.items()}

    @Slot()
    def refresh(self):
        try:
            items = self._db.list_mkl_orders()
        except Exception:
            items = []
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    @Slot(str, str, str, str, str, str, str, str)
    def addOrder(self, fio: str, phone: str, product: str, qty: str, sph: str, cyl: str, ax: str, bc: str):
        order = {
            "fio": fio.strip(),
            "phone": phone.strip(),
            "product": product.strip(),
            "qty": qty.strip(),
            "sph": sph.strip(),
            "cyl": cyl.strip(),
            "ax": ax.strip(),
            "bc": bc.strip(),
            "status": "Не заказан",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": "",
        }
        try:
            self._db.add_mkl_order(order)
        except Exception:
            pass
        self.refresh()

    @Slot(str, str, str, str, str, str, str, str, str)
    def addOrderWithComment(self, fio: str, phone: str, product: str, qty: str, sph: str, cyl: str, ax: str, bc: str, comment: str):
        order = {
            "fio": fio.strip(),
            "phone": phone.strip(),
            "product": product.strip(),
            "qty": qty.strip(),
            "sph": sph.strip(),
            "cyl": cyl.strip(),
            "ax": ax.strip(),
            "bc": bc.strip(),
            "status": "Не заказан",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "comment": (comment or "").strip(),
        }
        try:
            self._db.add_mkl_order(order)
        except Exception:
            pass
        self.refresh()


def run():
    app = QGuiApplication(sys.argv)
    # Init DB
    db_file = os.path.join(ROOT, "data.db")
    db = AppDB(db_file)
    model = MklOrdersModel(db)
    engine = QQmlApplicationEngine()
    # Expose model as context property
    engine.rootContext().setContextProperty("mklModel", model)
    # Load QML
    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml", "Main.qml")
    engine.load(qml_path)
    if not engine.rootObjects():
        sys.exit(-1)
    # Initial refresh
    model.refresh()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()