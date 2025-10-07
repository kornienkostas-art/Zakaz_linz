import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional, Any, Dict

DB_PATH = Path(__file__).with_name("orders_management.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH.as_posix())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # MKL domain
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            UNIQUE(full_name, phone)
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mkl_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sph REAL DEFAULT 0.0,
            cyl REAL,
            ax INTEGER,
            bc REAL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mkl_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Не заказан',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mkl_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            sph REAL DEFAULT 0.0,
            cyl REAL,
            ax INTEGER,
            bc REAL,
            qty INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(order_id) REFERENCES mkl_orders(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES mkl_products(id)
        )
        """
    )

    # Meridian domain
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meridian_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meridian_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meridian_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            sph REAL DEFAULT 0.0,
            cyl REAL,
            ax INTEGER,
            qty INTEGER NOT NULL DEFAULT 1,
            ordered INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


# Helper CRUD functions for MKL
def add_client(full_name: str, phone: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO clients(full_name, phone) VALUES(?, ?)", (full_name.strip(), phone.strip()))
    conn.commit()
    cur.execute("SELECT id FROM clients WHERE full_name=? AND phone=?", (full_name.strip(), phone.strip()))
    row = cur.fetchone()
    conn.close()
    return int(row["id"]) if row else 0


def update_client(client_id: int, full_name: str, phone: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE clients SET full_name=?, phone=? WHERE id=?", (full_name.strip(), phone.strip(), client_id))
    conn.commit()
    conn.close()


def delete_client(client_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()


def list_clients(search: str = "") -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    if search:
        like = f"%{search.strip()}%"
        cur.execute(
            "SELECT * FROM clients WHERE full_name LIKE ? OR phone LIKE ? ORDER BY full_name COLLATE NOCASE",
            (like, like),
        )
    else:
        cur.execute("SELECT * FROM clients ORDER BY full_name COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_mkl_product(name: str, sph: Optional[float], cyl: Optional[float], ax: Optional[int], bc: Optional[float]) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mkl_products(name, sph, cyl, ax, bc) VALUES(?, ?, ?, ?, ?)",
        (name.strip(), sph, cyl, ax, bc),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return int(pid)


def update_mkl_product(product_id: int, name: str, sph: Optional[float], cyl: Optional[float], ax: Optional[int], bc: Optional[float]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE mkl_products SET name=?, sph=?, cyl=?, ax=?, bc=? WHERE id=?",
        (name.strip(), sph, cyl, ax, bc, product_id),
    )
    conn.commit()
    conn.close()


def delete_mkl_product(product_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mkl_products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def list_mkl_products() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mkl_products ORDER BY name COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_mkl_order(client_id: int, status: str = "Не заказан") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO mkl_orders(client_id, status) VALUES(?, ?)", (client_id, status))
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return int(oid)


def add_mkl_order_item(order_id: int, product_id: int, sph: Optional[float], cyl: Optional[float], ax: Optional[int], bc: Optional[float], qty: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mkl_order_items(order_id, product_id, sph, cyl, ax, bc, qty) VALUES(?, ?, ?, ?, ?, ?, ?)",
        (order_id, product_id, sph, cyl, ax, bc, qty),
    )
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return int(iid)


def delete_mkl_order(order_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mkl_orders WHERE id=?", (order_id,))
    cur.execute("DELETE FROM mkl_order_items WHERE order_id=?", (order_id,))
    conn.commit()
    conn.close()


def list_mkl_orders(status_filter: Optional[str] = None, search: str = "") -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    base = """
    SELECT o.id, o.status, o.created_at, c.full_name, c.phone
    FROM mkl_orders o
    JOIN clients c ON c.id = o.client_id
    """
    where = []
    params: List[Any] = []
    if status_filter and status_filter != "Все":
        where.append("o.status = ?")
        params.append(status_filter)
    if search:
        where.append("(c.full_name LIKE ? OR c.phone LIKE ?)")
        like = f"%{search.strip()}%"
        params.extend([like, like])
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY o.created_at DESC"
    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_mkl_order_items(order_id: int) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT i.*, p.name as product_name
        FROM mkl_order_items i
        JOIN mkl_products p ON p.id = i.product_id
        WHERE i.order_id=?
        ORDER BY i.id
        """,
        (order_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def set_mkl_order_status(order_id: int, status: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE mkl_orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()


# Meridian helpers
def add_meridian_product(name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO meridian_products(name) VALUES(?)", (name.strip(),))
    conn.commit()
    cur.execute("SELECT id FROM meridian_products WHERE name=?", (name.strip(),))
    row = cur.fetchone()
    conn.close()
    return int(row["id"]) if row else 0


def delete_meridian_product(product_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM meridian_products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def list_meridian_products() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM meridian_products ORDER BY name COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_meridian_order(number: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO meridian_orders(number) VALUES(?)", (number.strip(),))
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return int(oid)


def delete_meridian_order(order_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM meridian_orders WHERE id=?", (order_id,))
    cur.execute("DELETE FROM meridian_order_items WHERE order_id=?", (order_id,))
    conn.commit()
    conn.close()


def list_meridian_orders() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM meridian_orders ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_meridian_item(order_id: int, product_name: str, sph: Optional[float], cyl: Optional[float], ax: Optional[int], qty: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meridian_order_items(order_id, product_name, sph, cyl, ax, qty) VALUES(?, ?, ?, ?, ?, ?)",
        (order_id, product_name.strip(), sph, cyl, ax, qty),
    )
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return int(iid)


def delete_meridian_item(item_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM meridian_order_items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def list_meridian_items(order_id: int) -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM meridian_order_items WHERE order_id=? ORDER BY id",
        (order_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def set_meridian_item_ordered(item_id: int, ordered: bool) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE meridian_order_items SET ordered=? WHERE id=?", (1 if ordered else 0, item_id))
    conn.commit()
    conn.close()