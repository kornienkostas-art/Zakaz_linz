import os
import sys
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

# Support running both:
# - python -m ussurochki.main
# - python ussurochki/main.py
try:
    from .db import Database
    from .utils import ensure_app_data_dir, ThemeManager
    from .ui.main_window import MainWindow
except ImportError:
    # If launched as a script, add project root to sys.path and import absolutely
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from ussurochki.db import Database  # type: ignore
    from ussurochki.utils import ensure_app_data_dir, ThemeManager  # type: ignore
    from ussurochki.ui.main_window import MainWindow  # type: ignore


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