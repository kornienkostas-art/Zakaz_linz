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
        "orderId": Qt.UserRole + 1,
        "fio": Qt.UserRole + 2,
        "phone": Qt.UserRole + 3,
        "product": Qt.UserRole + 4,
        "sph": Qt.UserRole + 5,
        "cyl": Qt.UserRole + 6,
        "ax": Qt.UserRole + 7,
        "bc": Qt.UserRole + 8,
        "qty": Qt.UserRole + 9,
        "status": Qt.UserRole + 10,
        "date": Qt.UserRole + 11,
        "comment": Qt.UserRole + 12,
        "commentFlag": Qt.UserRole + 13,
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
        if role == self.ROLES["orderId"]:
            return item.get("id", 0)
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

    @Slot(int)
    def deleteOrder(self, order_id: int):
        try:
            self._db.delete_mkl_order(order_id)
        except Exception:
            pass
        self.refresh()

    @Slot(int, str, str, str, str, str, str, str, str, str)
    def updateOrder(self, order_id: int, fio: str, phone: str, product: str, qty: str, sph: str, cyl: str, ax: str, bc: str, comment: str):
        fields = {
            "fio": fio.strip(),
            "phone": phone.strip(),
            "product": product.strip(),
            "qty": qty.strip(),
            "sph": sph.strip(),
            "cyl": cyl.strip(),
            "ax": ax.strip(),
            "bc": bc.strip(),
            "comment": (comment or "").strip(),
        }
        try:
            self._db.update_mkl_order(order_id, fields)
        except Exception:
            pass
        self.refresh()

    @Slot(int, result=object)
    def getOrder(self, order_id: int):
        for it in self._items:
            if int(it.get("id") or 0) == int(order_id):
                return it
        return {}


class MeridianOrdersModel(QAbstractListModel):
    ROLES = {
        "orderId": Qt.UserRole + 1,
        "title": Qt.UserRole + 2,
   "status": Qt.UserRole + 3,
        "date": Qt.UserRole + 4,
        "itemsCount": Qt.UserRole + 5,
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
        it = self._items[row]
        if role == self.ROLES["orderId"]:
            return it.get("id", 0)
        if role == self.ROLES["title"]:
            return it.get("title", "")
        if role == self.ROLES["status"]:
            return it.get("status", "")
        if role == self.ROLES["date"]:
            return it.get("date", "")
        if role == self.ROLES["itemsCount"]:
            return it.get("itemsCount", 0)
        return None

    def roleNames(self):
        return {v: QByteArray(k.encode("utf-8")) for k, v in self.ROLES.items()}

    @Slot()
    def refresh(self):
        try:
            orders = self._db.list_meridian_orders()
        except Exception:
            orders = []
        # compute items count
        for o in orders:
            cnt = 0
            try:
                cnt = len(self._db.get_meridian_items(o.get("id")))
            except Exception:
                cnt = 0
            o["itemsCount"] = cnt
        self.beginResetModel()
        self._items = orders
        self.endResetModel()

    @Slot(str)
    def addOrder(self, title: str):
        order = {
            "title": (title or "").strip(),
            "status": "Не заказан",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        if not order["title"]:
            order["title"] = f"Заказ Меридиан"
        try:
            self._db.add_meridian_order(order, [])
        except Exception:
            pass
        self.refresh()

    @Slot(int)
    def deleteOrder(self, order_id: int):
        try:
            self._db.delete_meridian_order(order_id)
        except Exception:
            pass
        self.refresh()

    @Slot(int, str)
    def updateStatus(self, order_id: int, status: str):
        try:
            self._db.update_meridian_order(order_id, {"status": status, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
        except Exception:
            pass
        self.refresh()


def run():
    app = QGuiApplication(sys.argv)
    # Init DB
    db_file = os.path.join(ROOT, "data.db")
    db = AppDB(db_file)
    mkl = MklOrdersModel(db)
    mer = MeridianOrdersModel(db)
    engine = QQmlApplicationEngine()
    # Expose models
    engine.rootContext().setContextProperty("mklModel", mkl)
    engine.rootContext().setContextProperty("merModel", mer)
    # Load QML
    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml", "Main.qml")
    engine.load(qml_path)
    if not engine.rootObjects():
        sys.exit(-1)
    # Initial refresh
    mkl.refresh()
    mer.refresh()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()