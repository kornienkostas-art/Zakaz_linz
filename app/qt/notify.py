from typing import List, Dict, Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QDialogButtonBox,
    QPushButton,
    QWidget,
)


def _show_dialog(
    parent: QWidget,
    title: str,
    header: str,
    rows: List[List[str]],
    columns: List[str],
    actions: List[tuple[str, Callable[[], None]]],
) -> None:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    layout = QVBoxLayout(dlg)

    lbl = QLabel(header)
    lbl.setStyleSheet("font-weight:600; font-size:14pt; color:#0F172A;")
    layout.addWidget(lbl)

    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            item = QTableWidgetItem(val)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()
    layout.addWidget(table)

    buttons = QDialogButtonBox()
    for text, cb in actions:
        btn = QPushButton(text)
        btn.clicked.connect(lambda _, fn=cb: (fn(), dlg.accept()))
        buttons.addButton(btn, QDialogButtonBox.ActionRole)
    close_btn = QPushButton("Закрыть")
    close_btn.clicked.connect(dlg.reject)
    buttons.addButton(close_btn, QDialogButtonBox.RejectRole)
    layout.addWidget(buttons)

    dlg.setModal(True)
    dlg.setWindowModality(Qt.WindowModal)
    dlg.exec()


def show_meridian_notification(
    parent: QWidget,
    pending_orders: List[Dict],
    on_snooze: Callable[[int], None],
    on_mark_ordered: Callable[[], None],
) -> None:
    rows = [[str(o.get("title", "")), str(o.get("status", "")), str(o.get("date", ""))] for o in pending_orders[:10]]
    actions = [
        ("Отложить 15 мин", lambda: on_snooze(15)),
        ("Отложить 30 мин", lambda: on_snooze(30)),
        ("Отметить «Заказан»", on_mark_ordered),
    ]
    _show_dialog(
        parent,
        "Уведомление • Заказы «Меридиан»",
        f"Есть заказы со статусом «Не заказан». Всего: {len(pending_orders)}.",
        rows,
        ["Название", "Статус", "Дата"],
        actions,
    )


def show_mkl_notification(
    parent: QWidget,
    pending_orders: List[Dict],
    on_snooze_days: Callable[[int], None],
    on_mark_ordered: Callable[[], None],
) -> None:
    rows = [
        [str(o.get("fio", "")), str(o.get("product", "")), str(o.get("status", "")), str(o.get("date", ""))]
        for o in pending_orders[:10]
    ]
    actions = [
        ("Отложить 1 день", lambda: on_snooze_days(1)),
        ("Отложить 3 дня", lambda: on_snooze_days(3)),
        ("Отметить «Заказан»", on_mark_ordered),
    ]
    _show_dialog(
        parent,
        "Уведомление • Заказы МКЛ",
        f"Есть просроченные заказы со статусом «Не заказан». Всего: {len(pending_orders)}.",
        rows,
        ["Клиент", "Товар", "Статус", "Дата"],
        actions,
    )