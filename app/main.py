import sys
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
    """Geometric, strict logo with concentric rings, grid and monogram."""
    def sizeHint(self):
        return QtCore.QSize(76, 76)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = self.rect().adjusted(8, 8, -8, -8)
        cx = rect.center().x()
        cy = rect.center().y()
        r = min(rect.width(), rect.height()) / 2

        # Concentric rings
        for i, w in enumerate((2.5, 1.5, 1.0)):
            rr = r - i * 4
            pen = QtGui.QPen(ACCENT, w)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawEllipse(QtCore.QPointF(cx, cy), rr, rr)

        # Subtle radial ticks
        painter.setPen(QtGui.QPen(QtGui.QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 120), 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        for angle in range(0, 360, 30):
            a = QtCore.qDegreesToRadians(angle)
            p1 = QtCore.QPointF(cx + (r - 6) * QtCore.qCos(a), cy + (r - 6) * QtCore.qSin(a))
            p2 = QtCore.QPointF(cx + (r - 10) * QtCore.qCos(a), cy + (r - 10) * QtCore.qSin(a))
            painter.drawLine(p1, p2)

        # Inner grid
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 40), 1))
        grid = rect.adjusted(10, 10, -10, -10)
        step = grid.width() / 4
        for i in range(1, 4):
            # vertical
            x = grid.left() + i * step
            painter.drawLine(QtCore.QPointF(x, grid.top()), QtCore.QPointF(x, grid.bottom()))
            # horizontal
            y = grid.top() + i * step
            painter.drawLine(QtCore.QPointF(grid.left(), y), QtCore.QPointF(grid.right(), y))

        # Monogram for "У" with strict geometry and inner cut
        path = QtGui.QPainterPath()
        w = rect.width()
        h = rect.height()
        x = rect.left()
        y = rect.top()

        # Outer U
        path.moveTo(x + w * 0.28, y + h * 0.22)
        path.lineTo(x + w * 0.28, y + h * 0.68)
        path.quadTo(x + w * 0.50, y + h * 0.88, x + w * 0.72, y + h * 0.68)
        path.lineTo(x + w * 0.72, y + h * 0.22)

        # Inner cut
        cut = QtGui.QPainterPath()
        cut.moveTo(x + w * 0.40, y + h * 0.32)
        cut.lineTo(x + w * 0.40, y + h * 0.60)
        cut.quadTo(x + w * 0.50, y + h * 0.70, x + w * 0.60, y + h * 0.60)
        cut.lineTo(x + w * 0.60, y + h * 0.32)

        painter.setPen(QtGui.QPen(ACCENT, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)

        painter.setPen(QtGui.QPen(QtGui.QColor(DARK_BG), 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawPath(cut)

        # Diagonal detail stroke
        painter.setPen(QtGui.QPen(ACCENT, 2, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        painter.drawLine(
            QtCore.QPointF(x + w * 0.30, y + h * 0.24),
            QtCore.QPointF(x + w * 0.70, y + h * 0.24)
        )


class Header(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 12)
        layout.setSpacing(16)

        self.logo = LogoWidget()
        self.title = QtWidgets.QLabel("УссурОЧки.рф")
        self.title.setObjectName("Title")
        self.subtitle = QtWidgets.QLabel("Панель управления заказами")
        self.subtitle.setObjectName("Subtitle")

        # Try to apply brand font if available
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

        # Signal placeholder
        self.settings_btn.clicked.connect(self.on_settings)

    def apply_brand_font(self):
        family = BrandFontLoader.load()
        if family:
            f = QtGui.QFont(family)
            f.setPointSize(24)
            f.setWeight(QtGui.QFont.DemiBold)
            self.title.setFont(f)

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

        # Central container with card-like look
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(0)

        # Center the card
        card_holder = QtWidgets.QHBoxLayout()
        card_holder.addStretch()
        self.card = Card()
        self.card.setFixedWidth(640)
        card_holder.addWidget(self.card)
        card_holder.addStretch()

        root.addLayout(card_holder)

        # Status bar subtle message
        status = QtWidgets.QStatusBar()
        status.showMessage("Готово")
        self.setStatusBar(status)

        # Apply stylesheet
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
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


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