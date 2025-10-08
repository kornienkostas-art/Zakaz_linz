from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
    app.setPalette(palette)


def apply_light_theme(app: QApplication):
    app.setPalette(app.style().standardPalette())


def common_stylesheet() -> str:
    # Небольшой современный Flat-UI стиль
    return """
    QWidget {
        font-size: 12pt;
    }
    QToolButton, QPushButton {
        padding: 8px 14px;
        border-radius: 6px;
        background-color: #3b82f6;
        color: white;
    }
    QPushButton:hover {
        background-color: #2563eb;
    }
    QPushButton:disabled {
        background-color: #94a3b8;
        color: #e2e8f0;
    }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
        padding: 6px;
        border: 1px solid #64748b;
        border-radius: 6px;
    }
    QHeaderView::section {
        padding: 6px;
    }
    """