import os
import sqlite3
from typing import Dict, Any


class SettingsStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self) -> Dict[str, Any]:
        rows = self.conn.execute("SELECT key, value FROM settings;").fetchall()
        d = {row["key"]: row["value"] for row in rows}
        # defaults
        theme = d.get("theme", "system")
        export_folder = d.get("export_folder", "exports")
        show_eye = d.get("show_eye", "true") == "true"
        show_bc_mkl = d.get("show_bc_mkl", "true") == "true"
        aggregate_specs = d.get("aggregate_specs", "true") == "true"
        if export_folder and not os.path.isabs(export_folder):
            export_folder = os.path.join(os.getcwd(), export_folder)
        os.makedirs(export_folder, exist_ok=True)
        return {
            "theme": theme,
            "export_folder": export_folder,
            "show_eye": show_eye,
            "show_bc_mkl": show_bc_mkl,
            "aggregate_specs": aggregate_specs,
        }

    def set(self, key: str, value: Any) -> None:
        if isinstance(value, bool):
            value = "true" if value else "false"
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
            (key, str(value)),
        )
        self.conn.commit()