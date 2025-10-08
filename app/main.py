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
    """Брутальный тигр: угловатая геометрия, много полос и текстур."""
    def sizeHint(self):
        return QtCore.QSize(76, 76)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        try:
            rect = self.rect().adjusted(8, 8, -8, -8)
            cx = rect.center().x()
            cy = rect.center().y()
            r = min(rect.width(), rect.height()) / 2

            # Кольца-рамки (чуть толще, чтобы придать веса)
            for i, w in enumerate((3.0, 1.8, 1.2)):
                rr = r - i * 4
                pen = QtGui.QPen(ACCENT, w)
                pen.setCosmetic(True)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawEllipse(QtCore.QPointF(cx, cy), rr, rr)

            # Радиальные метки
            painter.setPen(QtGui.QPen(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 140), 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
            for angle in range(0, 360, 30):
                a = math.radians(angle)
                p1 = QtCore.QPointF(cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))
                p2 = QtCore.QPointF(cx + (r - 11) * math.cos(a), cy + (r - 11) * math.sin(a))
                painter.drawLine(p1, p2)

            # Основные размеры для головы
            w = rect.width()
            h = rect.height()
            x = rect.left()
            y = rect.top()

            # Угловатая голова в виде многоугольника (челюсть, скулы)
            head_poly = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.35, y + h * 0.28),  # левый верх
                QtCore.QPointF(x + w * 0.30, y + h * 0.40),  # левый скула
                QtCore.QPointF(x + w * 0.32, y + h * 0.54),  # левая челюсть
                QtCore.QPointF(x + w * 0.50, y + h * 0.62),  # подбородок
                QtCore.QPointF(x + w * 0.68, y + h * 0.54),  # правая челюсть
                QtCore.QPointF(x + w * 0.70, y + h * 0.40),  # правая скула
                QtCore.QPointF(x + w * 0.65, y + h * 0.28),  # правый верх
                QtCore.QPointF(x + w * 0.50, y + h * 0.22),  # лоб центр
            ])
            painter.setPen(QtGui.QPen(ACCENT, 2.5))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 30)))
            painter.drawPolygon(head_poly)

            # Уши — острые треугольники
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(ACCENT, 2.2))
            ear_left = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.36, y + h * 0.24),
                QtCore.QPointF(x + w * 0.28, y + h * 0.34),
                QtCore.QPointF(x + w * 0.40, y + h * 0.34),
            ])
            ear_right = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.64, y + h * 0.24),
                QtCore.QPointF(x + w * 0.72, y + h * 0.34),
                QtCore.QPointF(x + w * 0.60, y + h * 0.34),
            ])
            painter.drawPolygon(ear_left)
            painter.drawPolygon(ear_right)

            # Глаза — узкие «щели»
            painter.setPen(QtGui.QPen(ACCENT, 2.4, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
            eye_y = y + h * 0.38
            eye_w = w * 0.08
            painter.drawLine(QtCore.QPointF(x + w * 0.42, eye_y), QtCore.QPointF(x + w * 0.42 + eye_w, eye_y - h * 0.02))
            painter.drawLine(QtCore.QPointF(x + w * 0.58 - eye_w, eye_y - h * 0.02), QtCore.QPointF(x + w * 0.58, eye_y))

            # «Брови» — V-образные накладки над глазами
            painter.setPen(QtGui.QPen(ACCENT, 2.0))
            painter.drawLine(QtCore.QPointF(x + w * 0.40, y + h * 0.34), QtCore.QPointF(x + w * 0.50, y + h * 0.32))
            painter.drawLine(QtCore.QPointF(x + w * 0.60, y + h * 0.34), QtCore.QPointF(x + w * 0.50, y + h * 0.32))

            # Нос — ромб
            nose = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.50, y + h * 0.44),
                QtCore.QPointF(x + w * 0.45, y + h * 0.48),
                QtCore.QPointF(x + w * 0.50, y + h * 0.52),
                QtCore.QPointF(x + w * 0.55, y + h * 0.48),
            ])
            painter.setBrush(QtGui.QBrush(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 60)))
            painter.setPen(QtGui.QPen(ACCENT, 2.2))
            painter.drawPolygon(nose)

            # Рот — прямая с «клыками»
            painter.setPen(QtGui.QPen(ACCENT, 2.2))
            painter.drawLine(QtCore.QPointF(x + w * 0.42, y + h * 0.54), QtCore.QPointF(x + w * 0.58, y + h * 0.54))
            fang_left = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.46, y + h * 0.54),
                QtCore.QPointF(x + w * 0.44, y + h * 0.60),
                QtCore.QPointF(x + w * 0.48, y + h * 0.54),
            ])
            fang_right = QtGui.QPolygonF([
                QtCore.QPointF(x + w * 0.52, y + h * 0.54),
                QtCore.QPointF(x + w * 0.56, y + h * 0.54),
                QtCore.QPointF(x + w * 0.56, y + h * 0.60),
            ])
            painter.drawPolygon(fang_left)
            painter.drawPolygon(fang_right)

            # Брутальные полосы — больше, резче
            painter.setPen(QtGui.QPen(ACCENT, 2.2))
            stripes = [
                # лобные V-полосы
                (QtCore.QPointF(x + w * 0.50, y + h * 0.26), QtCore.QPointF(x + w * 0.44, y + h * 0.32)),
                (QtCore.QPointF(x + w * 0.50, y + h * 0.26), QtCore.QPointF(x + w * 0.56, y + h * 0.32)),
                # верхние боковые
                (QtCore.QPointF(x + w * 0.34, y + h * 0.36), QtCore.QPointF(x + w * 0.42, y + h * 0.40)),
                (QtCore.QPointF(x + w * 0.66, y + h * 0.36), QtCore.QPointF(x + w * 0.58, y + h * 0.40)),
                # средние боковые
                (QtCore.QPointF(x + w * 0.33, y + h * 0.46), QtCore.QPointF(x + w * 0.41, y + h * 0.48)),
                (QtCore.QPointF(x + w * 0.67, y + h * 0.46), QtCore.QPointF(x + w * 0.59, y + h * 0.48)),
                # нижние боковые
                (QtCore.QPointF(x + w * 0.36, y + h * 0.54), QtCore.QPointF(x + w * 0.44, y + h * 0.56)),
                (QtCore.QPointF(x + w * 0.64, y + h * 0.54), QtCore.QPointF(x + w * 0.56, y + h * 0.56)),
            ]
            for p1, p2 in stripes:
                painter.drawLine(p1, p2)

            # Текстурная штриховка внутри (тонкие линии)
            painter.setPen(QtGui.QPen(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 120), 1))
            for i in range(4):
                painter.drawLine(QtCore.QPointF(x + w * (0.40 + i * 0.04), y + h * 0.42),
                                  QtCore.QPointF(x + w * (0.44 + i * 0.04), y + h * 0.50))

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