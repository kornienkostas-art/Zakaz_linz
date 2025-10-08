import sys
import os
from datetime import date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QComboBox, QMessageBox, QInputDialog,
    QLineEdit, QSpinBox, QFormLayout, QDialog, QDialogButtonBox, QFileDialog,
    QStackedWidget, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPalette, QColor

from db import init_db, Client, Product, MklOrder, MklOrderItem, MeridianOrder, MeridianOrderItem, export_mkl, export_meridian, DATA_DIR, EXPORT_DIR


def apply_dark_palette(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(18, 18, 18))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(30, 30, 30))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("УссурОЧки.рф — Управление заказами")
        self.resize(1100, 700)

        self.theme_dark = True

        # Menu
        menubar = self.menuBar()
        app_menu = menubar.addMenu("Приложение")
        self.theme_act = QAction("Тёмная тема", self, checkable=True, checked=True)
        self.theme_act.triggered.connect(self.toggle_theme)
        app_menu.addAction(self.theme_act)
        about_act = QAction("О приложении", self)
        about_act.triggered.connect(self.show_about)
        app_menu.addAction(about_act)

        data_menu = menubar.addMenu("Данные")
        open_db_act = QAction("Открыть папку БД", self)
        open_db_act.triggered.connect(lambda: self.open_folder(DATA_DIR))
        data_menu.addAction(open_db_act)
        open_export_act = QAction("Открыть папку экспорта", self)
        open_export_act.triggered.connect(lambda: self.open_folder(EXPORT_DIR))
        data_menu.addAction(open_export_act)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_view = self.build_home()
        self.mkl_view = self.build_mkl()
        self.meridian_view = self.build_meridian()
        self.settings_view = self.build_settings()

        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.mkl_view)
        self.stack.addWidget(self.meridian_view)
        self.stack.addWidget(self.settings_view)

        self.stack.setCurrentWidget(self.home_view)

    def toggle_theme(self):
        self.theme_dark = self.theme_act.isChecked()
        if self.theme_dark:
            apply_dark_palette(QApplication.instance())
            self.theme_act.setText("Тёмная тема")
        else:
            QApplication.instance().setPalette(QApplication.palette())  # reset to system/light
            self.theme_act.setText("Светлая тема")

    def show_about(self):
        QMessageBox.information(self, "О приложении", "УссурОЧки.рф — Управление заказами.\nЛокальная БД (SQLite), светлая/тёмная тема, экспорт TXT.")

    def open_folder(self, path: str):
        try:
            os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку:\n{e}")

    # ---------------- Home ----------------
    def build_home(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Главное меню"))
        btn_mkl = QPushButton("Заказы МКЛ")
        btn_mkl.clicked.connect(lambda: self.stack.setCurrentWidget(self.mkl_view))
        btn_meridian = QPushButton("Заказы Меридиан")
        btn_meridian.clicked.connect(lambda: self.stack.setCurrentWidget(self.meridian_view))
        btn_settings = QPushButton("Настройки")
        btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_view))
        v.addWidget(btn_mkl)
        v.addWidget(btn_meridian)
        v.addWidget(btn_settings)
        v.addStretch()
        return w

    # ---------------- MKL ----------------
    def build_mkl(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        header = QHBoxLayout()
        header.addWidget(QLabel("Заказы МКЛ"))
        self.mkl_filter = QComboBox()
        self.mkl_filter.addItems(["Все", "не заказан", "заказан", "прозвонен", "вручен"])
        self.mkl_filter.currentTextChanged.connect(self.refresh_mkl)
        header.addWidget(self.mkl_filter)
        btn_add_order = QPushButton("Добавить заказ")
        btn_add_order.clicked.connect(self.mkl_add_order)
        btn_export = QPushButton("Экспорт TXT")
        btn_export.clicked.connect(self.mkl_export)
        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        header.addWidget(btn_add_order)
        header.addWidget(btn_export)
        header.addWidget(btn_back)
        header.addStretch()
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        # Left: orders
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addWidget(QLabel("Список заказов"))
        self.mkl_orders_list = QListWidget()
        self.mkl_orders_list.itemSelectionChanged.connect(self.mkl_select_order)
        left_l.addWidget(self.mkl_orders_list)
        splitter.addWidget(left)

        # Right: items + clients + products
        right = QWidget()
        right_l = QVBoxLayout(right)

        right_l.addWidget(QLabel("Позиции заказа"))
        self.mkl_items_list = QListWidget()
        right_l.addWidget(self.mkl_items_list)

        add_item_row = QHBoxLayout()
        self.mkl_product_combo = QComboBox()
        self.mkl_qty_spin = QSpinBox()
        self.mkl_qty_spin.setRange(1, 999)
        self.mkl_qty_spin.setValue(1)
        btn_add_item = QPushButton("Добавить позицию")
        btn_add_item.clicked.connect(self.mkl_add_item)
        btn_save_items = QPushButton("Сохранить позиции")
        btn_save_items.clicked.connect(self.mkl_save_items)
        add_item_row.addWidget(self.mkl_product_combo)
        add_item_row.addWidget(QLabel("Кол-во"))
        add_item_row.addWidget(self.mkl_qty_spin)
        add_item_row.addWidget(btn_add_item)
        add_item_row.addWidget(btn_save_items)
        right_l.addLayout(add_item_row)

        right_l.addWidget(QLabel("Клиенты"))
        self.clients_list = QListWidget()
        right_l.addWidget(self.clients_list)

        client_btns = QHBoxLayout()
        btn_add_client = QPushButton("Добавить")
        btn_add_client.clicked.connect(self.add_client)
        btn_edit_client = QPushButton("Редактировать")
        btn_edit_client.clicked.connect(self.edit_client)
        btn_del_client = QPushButton("Удалить")
        btn_del_client.clicked.connect(self.del_client)
        client_btns.addWidget(btn_add_client)
        client_btns.addWidget(btn_edit_client)
        client_btns.addWidget(btn_del_client)
        right_l.addLayout(client_btns)

        right_l.addWidget(QLabel("Товары"))
        self.products_list = QListWidget()
        right_l.addWidget(self.products_list)

        product_btns = QHBoxLayout()
        btn_add_product = QPushButton("Добавить")
        btn_add_product.clicked.connect(self.add_product)
        btn_edit_product = QPushButton("Редактировать")
        btn_edit_product.clicked.connect(self.edit_product)
        btn_del_product = QPushButton("Удалить")
        btn_del_product.clicked.connect(self.del_product)
        product_btns.addWidget(btn_add_product)
        product_btns.addWidget(btn_edit_product)
        product_btns.addWidget(btn_del_product)
        right_l.addLayout(product_btns)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        self.refresh_mkl()
        return w

    def mkl_export(self):
        status = self.mkl_filter.currentText()
        status = None if status == "Все" else status
        path = export_mkl(status)
        QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")

    def refresh_mkl(self):
        # products
        self.mkl_product_combo.clear()
        for p in Product.select().order_by(Product.name):
            self.mkl_product_combo.addItem(p.name, p.id)

        # clients
        self.clients_list.clear()
        for c in Client.select().order_by(Client.name):
            item = QListWidgetItem(f"{c.name} • {c.phone or '—'}")
            item.setData(Qt.UserRole, c.id)
            self.clients_list.addItem(item)

        # products list view
        self.products_list.clear()
        for p in Product.select().order_by(Product.name):
            item = QListWidgetItem(f"{p.name} • {p.description or '—'} • {p.price} ₽")
            item.setData(Qt.UserRole, p.id)
            self.products_list.addItem(item)

        # orders
        self.mkl_orders_list.clear()
        status = self.mkl_filter.currentText()
        query = MklOrder.select(MklOrder, Client).join(Client)
        if status != "Все":
            query = query.where(MklOrder.status == status)
        for o in query.order_by(MklOrder.date.desc(), MklOrder.id.desc()):
            item = QListWidgetItem(f"#{o.id} • {o.date} • {o.client.name} ({o.client.phone or '—'}) • {o.status}")
            item.setData(Qt.UserRole, o.id)
            self.mkl_orders_list.addItem(item)

        self.mkl_items_list.clear()

    def mkl_select_order(self):
        self.mkl_items_list.clear()
        items = self.mkl_orders_list.selectedItems()
        if not items:
            return
        order_id = items[0].data(Qt.UserRole)
        for it in MklOrderItem.select(MklOrderItem, Product).join(Product).where(MklOrderItem.order_id == order_id):
            item = QListWidgetItem(f"{it.product.name} x{it.qty}")
            item.setData(Qt.UserRole, it.id)
            self.mkl_items_list.addItem(item)

        # actions per order: status change, edit date/notes, delete
        # Show quick actions via buttons in a dialog
        self.mkl_order_actions_dialog(order_id)

    def mkl_order_actions_dialog(self, order_id: int):
        o = MklOrder.get_by_id(order_id)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Заказ #{o.id} — действия")
        fl = QFormLayout(dlg)

        status_cb = QComboBox()
        for s in ["не заказан", "заказан", "прозвонен", "вручен"]:
            status_cb.addItem(s)
        status_cb.setCurrentText(o.status)
        fl.addRow(QLabel("Статус:"), status_cb)

        date_edit = QLineEdit(str(o.date))
        fl.addRow(QLabel("Дата (YYYY-MM-DD):"), date_edit)

        notes_edit = QLineEdit(o.notes or "")
        fl.addRow(QLabel("Примечание:"), notes_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        fl.addRow(btns)

        btn_del = QPushButton("Удалить заказ")
        fl.addRow(btn_del)

        def on_save():
            try:
                o.status = status_cb.currentText()
                o.date = date.fromisoformat(date_edit.text().strip())
                o.notes = notes_edit.text().strip()
                o.save()
                self.refresh_mkl()
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")

        def on_delete():
            if QMessageBox.question(self, "Подтвердите", "Удалить заказ и его позиции?") == QMessageBox.Yes:
                MklOrderItem.delete().where(MklOrderItem.order == o).execute()
                o.delete_instance()
                self.refresh_mkl()
                dlg.accept()

        btns.accepted.connect(on_save)
        btns.rejected.connect(dlg.reject)
        btn_del.clicked.connect(on_delete)
        dlg.exec()

    def mkl_add_order(self):
        # need selected client
        items = self.clients_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Клиент", "Выберите клиента в списке справа.")
            return
        client_id = items[0].data(Qt.UserRole)
        MklOrder.create(client=client_id, status="не заказан", date=date.today(), notes="")
        self.refresh_mkl()

    def mkl_add_item(self):
        # need selected order
        items = self.mkl_orders_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Заказ", "Выберите заказ в списке слева.")
            return
        order_id = items[0].data(Qt.UserRole)
        pid = self.mkl_product_combo.currentData()
        qty = self.mkl_qty_spin.value()
        if pid:
            MklOrderItem.create(order=order_id, product=pid, qty=qty)
            self.mkl_select_order()

    def mkl_save_items(self):
        # nothing to do (items saved on add), but could be used to persist buffered edits
        QMessageBox.information(self, "Позиции", "Позиции уже сохраняются при добавлении/редактировании.")

    # Clients CRUD
    def add_client(self):
        name, ok = QInputDialog.getText(self, "Новый клиент", "ФИО:")
        if not ok or not name.strip():
            return
        phone, ok2 = QInputDialog.getText(self, "Новый клиент", "Телефон:")
        if ok2:
            Client.create(name=name.strip(), phone=(phone.strip() or None))
            self.refresh_mkl()

    def edit_client(self):
        items = self.clients_list.selectedItems()
        if not items:
            return
        cid = items[0].data(Qt.UserRole)
        c = Client.get_by_id(cid)
        name, ok = QInputDialog.getText(self, "Редактировать клиента", "ФИО:", text=c.name)
        if not ok or not name.strip():
            return
        phone, ok2 = QInputDialog.getText(self, "Редактировать клиента", "Телефон:", text=c.phone or "")
        if ok2:
            c.name = name.strip()
            c.phone = phone.strip() or None
            c.save()
            self.refresh_mkl()

    def del_client(self):
        items = self.clients_list.selectedItems()
        if not items:
            return
        cid = items[0].data(Qt.UserRole)
        if QMessageBox.question(self, "Подтвердите", "Удалить клиента и его заказы МКЛ?") == QMessageBox.Yes:
            # Cascade via DB relationships
            Client.get_by_id(cid).delete_instance(recursive=True)
            self.refresh_mkl()

    # Products CRUD
    def add_product(self):
        name, ok = QInputDialog.getText(self, "Новый товар", "Наименование:")
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "Новый товар", "Описание:")
        price_str, ok3 = QInputDialog.getText(self, "Новый товар", "Цена (число):", text="0")
        if ok2 and ok3:
            try:
                price = float(price_str.strip() or "0")
            except:
                price = 0.0
            Product.create(name=name.strip(), description=(desc.strip() or None), price=price)
            self.refresh_mkl()

    def edit_product(self):
        items = self.products_list.selectedItems()
        if not items:
            return
        pid = items[0].data(Qt.UserRole)
        p = Product.get_by_id(pid)
        name, ok = QInputDialog.getText(self, "Редактировать товар", "Наименование:", text=p.name)
        if not ok or not name.strip():
            return
        desc, ok2 = QInputDialog.getText(self, "Редактировать товар", "Описание:", text=p.description or "")
        price_str, ok3 = QInputDialog.getText(self, "Редактировать товар", "Цена (число):", text=str(p.price))
        if ok2 and ok3:
            try:
                price = float(price_str.strip() or str(p.price))
            except:
                price = p.price
            p.name = name.strip()
            p.description = desc.strip() or None
            p.price = price
            p.save()
            self.refresh_mkl()

    def del_product(self):
        items = self.products_list.selectedItems()
        if not items:
            return
        pid = items[0].data(Qt.UserRole)
        if QMessageBox.question(self, "Подтвердите", "Удалить товар и его позиции в заказах МКЛ?") == QMessageBox.Yes:
            # delete items referencing product
            MklOrderItem.delete().where(MklOrderItem.product_id == pid).execute()
            Product.get_by_id(pid).delete_instance()
            self.refresh_mkl()

    # ---------------- Meridian ----------------
    def build_meridian(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        header = QHBoxLayout()
        header.addWidget(QLabel("Заказы Меридиан"))
        self.meridian_filter = QComboBox()
        self.meridian_filter.addItems(["Все", "не заказан", "заказан"])
        self.meridian_filter.currentTextChanged.connect(self.refresh_meridian)
        header.addWidget(self.meridian_filter)
        btn_add_order = QPushButton("Добавить заказ")
        btn_add_order.clicked.connect(self.meridian_add_order)
        btn_export = QPushButton("Экспорт TXT")
        btn_export.clicked.connect(self.meridian_export)
        btn_back = QPushButton("Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        header.addWidget(btn_add_order)
        header.addWidget(btn_export)
        header.addWidget(btn_back)
        header.addStretch()
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        # Left: orders
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.addWidget(QLabel("Список заказов"))
        self.meridian_orders_list = QListWidget()
        self.meridian_orders_list.itemSelectionChanged.connect(self.meridian_select_order)
        left_l.addWidget(self.meridian_orders_list)
        splitter.addWidget(left)

        # Right: items
        right = QWidget()
        right_l = QVBoxLayout(right)

        right_l.addWidget(QLabel("Позиции заказа"))
        self.meridian_items_list = QListWidget()
        right_l.addWidget(self.meridian_items_list)

        add_item_row = QHBoxLayout()
        self.meridian_item_name = QLineEdit()
        self.meridian_item_name.setPlaceholderText("Наименование товара")
        self.meridian_qty_spin = QSpinBox()
        self.meridian_qty_spin.setRange(1, 999)
        self.meridian_qty_spin.setValue(1)
        btn_add_item = QPushButton("Добавить позицию")
        btn_add_item.clicked.connect(self.meridian_add_item)
        btn_save_items = QPushButton("Сохранить позиции")
        btn_save_items.clicked.connect(self.meridian_save_items)
        add_item_row.addWidget(self.meridian_item_name)
        add_item_row.addWidget(QLabel("Кол-во"))
        add_item_row.addWidget(self.meridian_qty_spin)
        add_item_row.addWidget(btn_add_item)
        add_item_row.addWidget(btn_save_items)
        right_l.addLayout(add_item_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        self.refresh_meridian()
        return w

    def meridian_export(self):
        status = self.meridian_filter.currentText()
        status = None if status == "Все" else status
        path = export_meridian(status)
        QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")

    def refresh_meridian(self):
        self.meridian_orders_list.clear()
        status = self.meridian_filter.currentText()
        query = MeridianOrder.select()
        if status != "Все":
            query = query.where(MeridianOrder.status == status)
        for o in query.order_by(MeridianOrder.date.desc(), MeridianOrder.id.desc()):
            item = QListWidgetItem(f"#{o.id} • {o.date} • {o.status}")
            item.setData(Qt.UserRole, o.id)
            self.meridian_orders_list.addItem(item)
        self.meridian_items_list.clear()

    def meridian_select_order(self):
        self.meridian_items_list.clear()
        items = self.meridian_orders_list.selectedItems()
        if not items:
            return
        order_id = items[0].data(Qt.UserRole)
        for it in MeridianOrderItem.select().where(MeridianOrderItem.order_id == order_id):
            item = QListWidgetItem(f"{it.product_name} x{it.qty}")
            item.setData(Qt.UserRole, it.id)
            self.meridian_items_list.addItem(item)

        self.meridian_order_actions_dialog(order_id)

    def meridian_order_actions_dialog(self, order_id: int):
        o = MeridianOrder.get_by_id(order_id)
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Заказ Меридиан #{o.id} — действия")
        fl = QFormLayout(dlg)

        status_cb = QComboBox()
        for s in ["не заказан", "заказан"]:
            status_cb.addItem(s)
        status_cb.setCurrentText(o.status)
        fl.addRow(QLabel("Статус:"), status_cb)

        date_edit = QLineEdit(str(o.date))
        fl.addRow(QLabel("Дата (YYYY-MM-DD):"), date_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        fl.addRow(btns)

        btn_del = QPushButton("Удалить заказ")
        fl.addRow(btn_del)

        def on_save():
            try:
                o.status = status_cb.currentText()
                o.date = date.fromisoformat(date_edit.text().strip())
                o.save()
                self.refresh_meridian()
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")

        def on_delete():
            if QMessageBox.question(self, "Подтвердите", "Удалить заказ и его позиции?") == QMessageBox.Yes:
                MeridianOrderItem.delete().where(MeridianOrderItem.order == o).execute()
                o.delete_instance()
                self.refresh_meridian()
                dlg.accept()

        btns.accepted.connect(on_save)
        btns.rejected.connect(dlg.reject)
        btn_del.clicked.connect(on_delete)
        dlg.exec()

    def meridian_add_order(self):
        MeridianOrder.create(status="не заказан", date=date.today())
        self.refresh_meridian()

    def meridian_add_item(self):
        items = self.meridian_orders_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Заказ", "Выберите заказ в списке слева.")
            return
        order_id = items[0].data(Qt.UserRole)
        name = self.meridian_item_name.text().strip()
        qty = self.meridian_qty_spin.value()
        if not name:
            return
        MeridianOrderItem.create(order=order_id, product_name=name, qty=qty)
        self.meridian_item_name.clear()
        self.meridian_qty_spin.setValue(1)
        self.meridian_select_order()

    def meridian_save_items(self):
        QMessageBox.information(self, "Позиции", "Позиции уже сохраняются при добавлении/редактировании.")

    # ---------------- Settings ----------------
    def build_settings(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Настройки"))
        v.addWidget(QLabel(f"База данных: {DB_PATH}"))
        v.addWidget(QLabel(f"Экспорт TXT: {EXPORT_DIR}"))
        btn_home = QPushButton("Назад")
        btn_home.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        v.addWidget(btn_home)
        v.addStretch()
        return w


def main():
    init_db()
    app = QApplication(sys.argv)
    apply_dark_palette(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()