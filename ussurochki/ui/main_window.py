from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QAction,
    QStyle,
)

from ..utils import ThemeManager, backup_database
from ..db import Database
from .widgets import BigNavButton, FadingStackedWidget
from .mkl_orders_view import MKLOrdersPage
from .meridian_orders_view import MeridianOrdersPage
from .settings_view import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, db: Database, settings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings

        self.setWindowTitle("УссурОЧки.рф — система управления заказами")

        self.stack = FadingStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_page = self._build_start_page()
        self.page_mkl = MKLOrdersPage(self.db, self.settings, self)
        self.page_meridian = MeridianOrdersPage(self.db, self.settings, self)
        self.page_settings = SettingsPage(self.db, self.settings, self)

        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.page_mkl)
        self.stack.addWidget(self.page_meridian)
        self.stack.addWidget(self.page_settings)

        self._build_toolbar()

    def _build_toolbar(self):
        tb = QToolBar("Главная")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_home = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon), "Главная", self)
        act_home.triggered.connect(lambda: self.stack.setCurrentWidget(self.start_page))
        tb.addAction(act_home)

        tb.addSeparator()

        act_mkl = QAction("Заказы МКЛ", self)
        act_mkl.triggered.connect(lambda: self.stack.setCurrentWidget(self.page_mkl))
        tb.addAction(act_mkl)

        act_mer = QAction("Заказы Меридиан", self)
        act_mer.triggered.connect(lambda: self.stack.setCurrentWidget(self.page_meridian))
        tb.addAction(act_mer)

        act_settings = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Настройки", self)
        act_settings.triggered.connect(lambda: self.stack.setCurrentWidget(self.page_settings))
        tb.addAction(act_settings)

    def _build_start_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("УссурОЧки.рф")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28pt; font-weight: 600; margin-bottom: 20px;")
        lay.addWidget(title)

        row = QHBoxLayout()
        btn_mkl = BigNavButton("Заказы МКЛ")
        btn_mkl.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_mkl))
        btn_meridian = BigNavButton("Заказы Меридиан")
        btn_meridian.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_meridian))
        btn_settings = BigNavButton("Настройки")
        btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_settings))
        row.addWidget(btn_mkl)
        row.addWidget(btn_meridian)
        row.addWidget(btn_settings)
        lay.addLayout(row)

        return w