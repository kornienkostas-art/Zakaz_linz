import os
import sqlite3
from pathlib import Path
from typing import Optional, Iterable, Any


DB_FILE = "ussurochki.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Settings
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    # MCL domain
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mcl_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mcl_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mcl_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Не заказан',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(client_id) REFERENCES mcl_clients(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mcl_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            sph REAL DEFAULT 0,
            cyl REAL,
            ax INTEGER,
            bc REAL,
            qty INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(order_id) REFERENCES mcl_orders(id) ON DELETE CASCADE
        )
        """
    )

    # Meridian domain
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mer_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mer_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'Не заказан',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mer_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            sph REAL DEFAULT 0,
            cyl REAL,
            ax INTEGER,
            qty INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(order_id) REFERENCES mer_orders(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


def fetchall(query: str, params: Iterable[Any] = ()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def fetchone(query: str, params: Iterable[Any] = ()) -> Optional[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def execute(query: str, params: Iterable[Any] = ()) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def executemany(query: str, params_seq: Iterable[Iterable[Any]]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(query, params_seq)
    conn.commit()
    conn.close()


def backup_db(to_path: str) -> str:
    src = Path(DB_FILE)
    dest_dir = Path(to_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{src.stem}_backup{src.suffix}"
    with open(src, "rb") as fsrc, open(dest, "wb") as fdst:
        fdst.write(fsrc.read())
    return str(dest)