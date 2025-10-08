import os
import sys
import sqlite3

from PySide6.QtWidgets import QApplication

from .db import connect
from .migrator import migrate
from .settings_store import SettingsStore
from .themes import apply_theme
from .ui.main_window import MainWindow


def main() -> int:
    conn = connect()
    migrate(conn)
    settings = SettingsStore(conn)

    app = QApplication(sys.argv)
    theme = settings.get().get("theme", "system")
    apply_theme(theme)

    w = MainWindow(conn, settings)
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())