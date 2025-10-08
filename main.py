import os
import sys
import ctypes
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ussurochki.paths import ensure_app_dirs, APP_NAME
from ussurochki.logging_conf import setup_logging
from ussurochki.db import Database
from ussurochki.settings import SettingsService
from ussurochki.backup import BackupService
from ussurochki.ui.main_window import MainWindow
from ussurochki.themes import apply_theme, Theme


def set_dpi_awareness_windows():
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
        except Exception:
            pass


def main():
    set_dpi_awareness_windows()
    ensure_app_dirs()
    setup_logging()

    # Initialize DB and services
    db = Database()
    db.connect()
    db.migrate()

    settings = SettingsService(db)
    backup = BackupService(db, settings)

    # Auto-backup once a day on first launch
    backup.auto_backup_if_needed()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Theme from settings
    theme_name = settings.get("theme", "System")
    theme = Theme.from_name(theme_name)
    apply_theme(app, theme)

    window = MainWindow(db=db, settings=settings, backup=backup)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()