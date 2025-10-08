import os
import sqlite3
from typing import Optional

DB_FILENAME = "app.db"


def get_db_path() -> str:
    return os.path.join(os.getcwd(), DB_FILENAME)


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn