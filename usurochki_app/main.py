import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)

# Импорты пакета или локальные при запуске скрипта напрямую
try:
    from .db import Database
    from .theme import apply_dark_theme, apply_light_theme, common_stylesheet
    from .settings import SettingsManager, SettingsWindow
    from .mkl import MKLWindow
    from .meridian import MeridianWindow
except ImportError:
    from db import Database
    from theme import apply_dark_theme, apply_light_theme, common_stylesheet
    from settings import SettingsManager, SettingsWindow
    from mkl import MKLWindow
ow


class MainWindow(QWidget):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("УссурОЧки.рф — система управления заказами")
        self.setMinimumSize(900, 600)

        # База данных и настройки
        base_dir = os.path.join(os.path.dirname(__file__), "data")
        self.settings = SettingsManager(base_dir=base_dir)
        self.db = Database(base_dir=base_dir)

        # Тема
        self._apply_theme(self.settings.get_theme())
        self.app.setStyleSheet(common_stylesheet())

        # Главное окно
        layout = QVBoxLayout(self)
        title = QLabel("УссурОЧки.рф")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24pt; font-weight: bold;")
        layout.addWidget(title)

        # Кнопки
        buttons = QHBoxLayout()
        btn_mkl = QPushButton("Заказы МКЛ")
        btn_meridian = QPushButton("Заказы Меридиан")
        btn_settings = QPushButton("Настройки")
        buttons.addWidget(btn_mkl)
        buttons.addWidget(btn_meridian)
        buttons.addWidget(btn_settings)
        layout.addLayout(buttons)

        # Окна разделов
        self.mkl_win = MKLWindow(self.db, export_dir=self.settings.get_export_dir())
        self.mer_win = MeridianWindow(self.db, export_dir=self.settings.get_export_dir())
        self.set_win = SettingsWindow(self.settings, on_theme_changed=self._apply_theme)

        # Сигналы
        btn_mkl.clicked.connect(self.mkl_win.show)
        btn_meridian.clicked.connect(self.mer_win.show)
        btn_settings.clicked.connect(self.set_win.show)

    def _apply_theme(self, theme: str):
        if theme == "light":
            apply_light_theme(self.app)
        else:
            apply_dark_theme(self.app)


def main():
    app = QApplication(sys.argv)
    win = MainWindow(app)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()