import os
import sys
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication

from .db import Database
from .utils import ensure_app_data_dir, ThemeManager
from .ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("УссурОЧки.рф")
    app.setOrganizationName("Ussurochki")

    settings = QSettings()
    theme = settings.value("theme", "dark")
    ThemeManager.apply(app, theme)

    ensure_app_data_dir()
    db_path = os.path.join("data", "ussurochki.db")
    db = Database(db_path)
    db.initialize()

    window = MainWindow(db=db, settings=settings)
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()