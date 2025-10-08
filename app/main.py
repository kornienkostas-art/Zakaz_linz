import sys
import math
from PySide6 import QtCore, QtGui, QtWidgets


ACCENT = QtGui.QColor(230, 180, 60)  # warm gold accent
DARK_BG = QtGui.QColor(18, 18, 22)   # deep dark background
CARD_BG = QtGui.QColor(28, 28, 34)   # card background


class BrandFontLoader:
    """Loads a custom brand font if present in assets. Falls back gracefully."""
    FONT_PATH = "app/assets/fonts/UssurBrand.ttf"
    FAMILY_NAME = None

    @classmethod
    def load(cls):
        file = QtCore.QFileInfo(cls.FONT_PATH).absoluteFilePath()
        if QtCore.QFile.exists(file):
            font_id = QtGui.QFontDatabase.addApplicationFont(file)
            if font_id != -1:
                families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    cls.FAMILY_NAME = families[0]
        return cls.FAMILY_NAME


class LogoWidget(QtWidgets.QWidget):
    """Простой строгий логотип: круг с мягкой заливкой и стилизованная «У»."""
    def sizeHint(self):
        return QtCore.QSize(64, 64)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        try:
            rect = self.rect().adjusted(6, 6, -6, -6)

            # Базовый круг
            painter.setPen(QtGui.QPen(ACCENT, 2))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 30)))
            painter.drawEllipse(rect)

            # Стилизованная «У»
            path = QtGui.QPainterPath()
            w = rect.width()
            h = rect.height()
            x = rect.left()
            y = rect.top()

            path.moveTo(x + w * 0.25, y + h * 0.25)
            path.lineTo(x + w * 0.25, y + h * 0.75)
            path.quadTo(x + w * 0.5, y + h * 0.95, x + w * 0.75, y + h * 0.75)
            path.lineTo(x + w * 0.75, y + h * 0.25)

            painter.setPen(QtGui.QPen(ACCENT, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPath(path)
        finally:
            painter.end()


class Header(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 12)
        layout.setSpacing(16)

        self.logo = LogoWidget()
        # Базовый размер логотипа
        self.logo.setMinimumSize(84, 84)
        self.logo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.title = QtWidgets.QLabel("УссурОЧки.рф")
        self.title.setObjectName("Title")
        self.subtitle = QtWidgets.QLabel("Панель управления заказами")
        self.subtitle.setObjectName("Subtitle")

        # Применить брендовый шрифт при наличии
        self.apply_brand_font()

        text_box = QtWidgets.QVBoxLayout()
        text_box.setSpacing(2)
        text_box.addWidget(self.title)
        text_box.addWidget(self.subtitle)

        layout.addWidget(self.logo, 0, QtCore.Qt.AlignVCenter)
        layout.addLayout(text_box)
        layout.addStretch()

        self.settings_btn = QtWidgets.QPushButton("Настройки")
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        layout.addWidget(self.settings_btn, 0, QtCore.Qt.AlignTop)

        # Сигнал-заглушка
        self.settings_btn.clicked.connect(self.on_settings)

    def apply_brand_font(self):
        family = BrandFontLoader.load()
        if family:
            f = QtGui.QFont(family)
            f.setPointSize(24)
            f.setWeight(QtGui.QFont.DemiBold)
            self.title.setFont(f)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # Адаптация размера логотипа в зависимости от ширины заголовка
        # При фуллскрине логотип увеличится, но не будет чрезмерным
        width = max( self.width(), 1 )
        size = int(max(84, min(160, width * 0.10)))
        self.logo.setFixedSize(size, size)

    @QtCore.Slot()
    def on_settings(self):
        QtWidgets.QMessageBox.information(self, "Настройки", "Функционал настроек будет добавлен позже.")


class MainActions(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(24, 12, 24, 24)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        self.btn_mkl = QtWidgets.QPushButton("Заказы МКЛ")
        self.btn_meridian = QtWidgets.QPushButton("Заказы Меридиан")

        for btn in (self.btn_mkl, self.btn_meridian):
            btn.setObjectName("PrimaryBtn")
            btn.setMinimumSize(220, 72)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        layout.addWidget(self.btn_mkl, 0, 0)
        layout.addWidget(self.btn_meridian, 0, 1)

        # Placeholder actions
        self.btn_mkl.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "МКЛ", "Раздел 'Заказы МКЛ' будет реализован позже."))
        self.btn_meridian.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Меридиан", "Раздел 'Заказы Меридиан' будет реализован позже."))


class Card(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = Header()
        self.actions = MainActions()

        layout.addWidget(self.header)
        layout.addWidget(self.actions)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("УссурОЧки.рф — Управление заказами")
        self.setMinimumSize(720, 480)

        # Центральный контейнер
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(0)

        # Дать карточке возможность растягиваться во фуллскрине
        card_holder = QtWidgets.QHBoxLayout()
        self.card = Card()
        self.card.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        card_holder.addWidget(self.card)

        root.addLayout(card_holder)

        # Статус-бар
        status = QtWidgets.QStatusBar()
        status.showMessage("Готово")
        self.setStatusBar(status)

        # Применить стили
        self.apply_styles()

    def apply_styles(self):
        try:
            with open(QtCore.QFileInfo("app/styles.qss").absoluteFilePath(), "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception:
            # Fallback minimal styles if stylesheet not found
            self.setStyleSheet("""
                QMainWindow { background: #121216; }
                #Card { background: #1c1c22; border-radius: 16px; }
                #Title { color: #e6b43c; font-size: 22px; font-weight: 600; }
                #Subtitle { color: #9aa0a6; font-size: 12px; }
                #PrimaryBtn {
                    color: #ffffff; background: #2a2a33; border: 1px solid #3a3a44; border-radius: 12px;
                    font-size: 16px; padding: 12px 20px;
                }
                #PrimaryBtn:hover { background: #34343e; border-color: #474753; }
                #PrimaryBtn:pressed { background: #2a2a33; border-color: #59596a; }
                #SettingsBtn {
                    color: #e6b43c; background: transparent; border: 1px solid #3a3a44; border-radius: 10px;
                    padding: 8px 14px; font-weight: 500;
                }
                #SettingsBtn:hover { border-color: #59596a; color: #ffd680; }
                #SettingsBtn:pressed { border-color: #7a7a8a; }
            """)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super().closeEvent(event)


def enable_high_dpi():
    # Qt6 включает high-DPI по умолчанию; явные атрибуты устарели.
    # Оставляем функцию для потенциальной дальнейшей настройки.
    pass


def main():
    enable_high_dpi()
    app = QtWidgets.QApplication(sys.argv)

    # Dark palette to ensure a strict, elegant look even without stylesheet
    palette = app.palette()
    palette.setColor(QtGui.QPalette.Window, DARK_BG)
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Base, CARD_BG)
    palette.setColor(QtGui.QPalette.AlternateBase, CARD_BG)
    palette.setColor(QtGui.QPalette.ToolTipBase, CARD_BG)
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Button, CARD_BG)
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.Highlight, ACCENT)
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#000000"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()