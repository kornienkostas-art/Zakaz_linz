import sqlite3
from typing import Optional


SCHEMA_VERSION = 1


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,)
    )
    return cur.fetchone() is not None


def _get_version(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, "schema_version"):
        conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL);")
        conn.execute("INSERT INTO schema_version (version) VALUES (0);")
        return 0
    cur = conn.execute("SELECT version FROM schema_version;")
    row = cur.fetchone()
    return int(row["version"]) if row else 0


def _set_version(conn: sqlite3.Connection, v: int) -> None:
    conn.execute("UPDATE schema_version SET version=?;", (v,))


def migrate(conn: sqlite3.Connection) -> None:
    cur_version = _get_version(conn)
    if cur_version < 1:
        _apply_v1(conn)
        _set_version(conn, 1)
    conn.commit()


def _apply_v1(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        -- Core entities
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT
        );

        CREATE TABLE IF NOT EXISTS products_mkl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products_meridian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );

        -- Orders MKL
        CREATE TABLE IF NOT EXISTS orders_mkl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            status INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS items_mkl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            eye TEXT NOT NULL CHECK (eye IN ('OD', 'OS')),
            sph REAL NOT NULL,
            cyl REAL,
            ax INTEGER,
            bc REAL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products_mkl(id) ON DELETE RESTRICT
        );

        -- Orders Meridian
        CREATE TABLE IF NOT EXISTS orders_meridian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL,
            status INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS items_meridian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            eye TEXT NOT NULL CHECK (eye IN ('OD', 'OS')),
            sph REAL NOT NULL,
            cyl REAL,
            ax INTEGER,
            d INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products_meridian(id) ON DELETE RESTRICT
        );

        -- Settings
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )

    # Seed default settings if absent
    existing = {row["key"] for row in conn.execute("SELECT key FROM settings;").fetchall()}
    defaults = {
        "theme": "system",
        "export_folder": "exports",
        "show_eye": "true",
        "show_bc_mkl": "true",
        "aggregate_specs": "true",
    }
    for k, v in defaults.items():
        if k not in existing:
            conn.execute("INSERT INTO settings(key, value) VALUES(?, ?);", (k, v))