import os
import re
import shutil
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


PHONE_RE = re.compile(r"^(?:\+7|8)\d{10}$")


def is_valid_phone(phone: Optional[str]) -> bool:
    if not phone:
        return True
    return bool(PHONE_RE.match(phone.strip()))


def ensure_app_data_dir() -> str:
    base = os.path.abspath("data")
    os.makedirs(base, exist_ok=True)
    return base


def backup_database(db_path: str, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"ussurochki_backup_{ts}.db"
    dest = os.path.join(dest_dir, base_name)
    shutil.copy2(db_path, dest)
    return dest


def format_item_mkl_row(item: dict) -> str:
    parts = [f"SPH {item['sph']:+.2f}"]
    if item.get("cyl") is not None:
        parts.append(f"CYL {item['cyl']:+.2f}")
    if item.get("ax") is not None:
        parts.append(f"AX {int(item['ax'])}")
    if item.get("bc") is not None:
        parts.append(f"BC {item['bc']:.1f}")
    parts.append(f"x{item['qty']}")
    return ", ".join(parts)


def format_item_meridian_row(item: dict) -> str:
    parts = [f"SPH {item['sph']:+.2f}"]
    if item.get("cyl") is not None:
        parts.append(f"CYL {item['cyl']:+.2f}")
    if item.get("ax") is not None:
        parts.append(f"AX {int(item['ax'])}")
    parts.append(f"x{item['qty']}")
    return ", ".join(parts)


class ThemeManager:
    @staticmethod
    def apply(app: QApplication, theme: str):
        if theme == "dark":
            ThemeManager._apply_dark(app)
        else:
            ThemeManager._apply_light(app)

    @staticmethod
    def _apply_light(app: QApplication):
        pal = app.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#f4f5f7"))
        pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f0f0"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#202124"))
        pal.setColor(QPalette.ColorRole.Button, QColor("#e9eaee"))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor("#202124"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        app.setPalette(pal)
        app.setStyleSheet(_COMMON_QSS)

    @staticmethod
    def _apply_dark(app: QApplication):
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#121417"))
        pal.setColor(QPalette.ColorRole.Base, QColor("#0f1114"))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#171a1f"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#e5e7eb"))
        pal.setColor(QPalette.ColorRole.Button, QColor("#1f2430"))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor("#e5e7eb"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#e5e7eb"))
        app.setPalette(pal)
        app.setStyleSheet(_COMMON_QSS)


_COMMON_QSS = """
QWidget {
    font-family: Segoe UI, Roboto, Arial;
    font-size: 10.5pt;
}

QPushButton {
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(59,130,246,0.08);
    padding: 8px 14px;
    border-radius: 8px;
}
QPushButton:hover { background: rgba(59,130,246,0.18); }
QPushButton:pressed { background: rgba(59,130,246,0.28); }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    border: 1px solid rgba(255,255,255,0.12);
    padding: 6px 8px;
    border-radius: 6px;
    background: palette(Base);
}

QHeaderView::section {
    background: rgba(0,0,0,0.08);
    padding: 6px;
    border: none;
}

QTableWidget {
    gridline-color: rgba(255,255,255,0.08);
    selection-background-color: #3b82f6;
    selection-color: white;
}

QGroupBox {
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    margin-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
"""