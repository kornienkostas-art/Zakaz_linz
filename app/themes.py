from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(250, 250, 250))
    p.setColor(QPalette.WindowText, Qt.black)
    p.setColor(QPalette.Base, QColor(245, 245, 245))
    p.setColor(QPalette.AlternateBase, QColor(232, 232, 232))
    p.setColor(QPalette.ToolTipBase, Qt.white)
    p.setColor(QPalette.ToolTipText, Qt.black)
    p.setColor(QPalette.Text, Qt.black)
    p.setColor(QPalette.Button, QColor(245, 245, 245))
    p.setColor(QPalette.ButtonText, Qt.black)
    p.setColor(QPalette.BrightText, Qt.red)
    p.setColor(QPalette.Highlight, QColor(76, 163, 224))
    p.setColor(QPalette.HighlightedText, Qt.white)
    return p


def dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(53, 53, 53))
    p.setColor(QPalette.WindowText, Qt.white)
    p.setColor(QPalette.Base, QColor(35, 35, 35))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipText, Qt.white)
    p.setColor(QPalette.Text, Qt.white)
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, Qt.white)
    p.setColor(QPalette.BrightText, Qt.red)
    p.setColor(QPalette.Highlight, QColor(76, 163, 224))
    p.setColor(QPalette.HighlightedText, Qt.black)
    return p


def apply_theme(theme: str) -> None:
    QApplication.setStyle("Fusion")
    if theme == "dark":
        QApplication.setPalette(dark_palette())
    elif theme == "light":
        QApplication.setPalette(light_palette())
    else:
        # system: reset to default
        QApplication.setPalette(QApplication.style().standardPalette())