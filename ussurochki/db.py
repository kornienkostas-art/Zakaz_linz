import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def initialize(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);

            CREATE TABLE IF NOT EXISTS product_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS product_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS orders_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS order_items_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                sph REAL NOT NULL,
                cyl REAL,
                ax INTEGER,
                bc REAL,
                qty INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product_mkl(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_order_items_mkl_order ON order_items_mkl(order_id);

            CREATE TABLE IF NOT EXISTS orders_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                sph REAL NOT NULL,
                cyl REAL,
                ax INTEGER,
                qty INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product_meridian(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_order_items_meridian_order ON order_items_meridian(order_id);
            """
        )

        # Ensure numbering for meridian orders
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_orders_meridian_number
            AFTER INSERT ON orders_meridian
            FOR EACH ROW
            WHEN NEW.number IS NULL
            BEGIN
                UPDATE orders_meridian
                SET number = (SELECT COALESCE(MAX(number), 0) + 1 FROM orders_meridian)
                WHERE id = NEW.id;
            END;
            """
        )

        conn.commit()

    @contextmanager
    def tx(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    # ---------- Clients ----------

    def list_clients(self, query: str = "") -> List[sqlite3.Row]:
        conn = self.connect()
        cur = conn.cursor()
        if query:
            like = f"%{query}%"
            cur.execute(
                """
                SELECT * FROM clients
                WHERE full_name LIKE ? OR phone LIKE ?
                ORDER BY full_name COLLATE NOCASE
                """,
                (like, like),
            )
        else:
            cur.execute(
                "SELECT * FROM clients ORDER BY full_name COLLATE NOCASE"
            )
        return cur.fetchall()

    def add_client(self, full_name: str, phone: Optional[str]) -> int:
        with self.tx() as conn:
            cur = conn.execute(
                "INSERT INTO clients(full_name, phone) VALUES(?, ?)",
                (full_name.strip(), phone.strip() if phone else None),
            )
            return cur.lastrowid

    def update_client(self, client_id: int, full_name: str, phone: Optional[str]) -> None:
        with self.tx() as conn:
            conn.execute(
                "UPDATE clients SET full_name = ?, phone = ? WHERE id = ?",
                (full_name.strip(), phone.strip() if phone else None, client_id),
            )

    def delete_client(self, client_id: int) -> None:
        with self.tx() as conn:
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))

    # ---------- Products (MKL) ----------

    def list_products_mkl(self) -> List[sqlite3.Row]:
        cur = self.connect().cursor()
        cur.execute("SELECT * FROM product_mkl ORDER BY name COLLATE NOCASE")
        return cur.fetchall()

    def add_product_mkl(self, name: str) -> int:
        with self.tx() as conn:
            cur = conn.execute("INSERT INTO product_mkl(name) VALUES(?)", (name.strip(),))
            return cur.lastrowid

    def update_product_mkl(self, product_id: int, name: str) -> None:
        with self.tx() as conn:
            conn.execute("UPDATE product_mkl SET name = ? WHERE id = ?", (name.strip(), product_id))

    def delete_product_mkl(self, product_id: int) -> None:
        with self.tx() as conn:
            conn.execute("DELETE FROM product_mkl WHERE id = ?", (product_id,))

    # ---------- Products (Meridian) ----------

    def list_products_meridian(self) -> List[sqlite3.Row]:
        cur = self.connect().cursor()
        cur.execute("SELECT * FROM product_meridian ORDER BY name COLLATE NOCASE")
        return cur.fetchall()

    def add_product_meridian(self, name: str) -> int:
        with self.tx() as conn:
            cur = conn.execute("INSERT INTO product_meridian(name) VALUES(?)", (name.strip(),))
            return cur.lastrowid

    def update_product_meridian(self, product_id: int, name: str) -> None:
        with self.tx() as conn:
            conn.execute("UPDATE product_meridian SET name = ? WHERE id = ?", (name.strip(), product_id))

    def delete_product_meridian(self, product_id: int) -> None:
        with self.tx() as conn:
            conn.execute("DELETE FROM product_meridian WHERE id = ?", (product_id,))

    # ---------- Orders MKL ----------

    def create_order_mkl(self, client_id: int, status: str, items: Sequence[Dict[str, Any]]) -> int:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            cur = conn.execute(
                "INSERT INTO orders_mkl(client_id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (client_id, status, now, now),
            )
            order_id = cur.lastrowid
            for it in items:
                conn.execute(
                    """
                    INSERT INTO order_items_mkl(order_id, product_id, sph, cyl, ax, bc, qty)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        it["product_id"],
                        it["sph"],
                        it.get("cyl"),
                        it.get("ax"),
                        it.get("bc"),
                        it["qty"],
                    ),
                )
            return order_id

    def update_order_mkl(self, order_id: int, client_id: int, status: str, items: Sequence[Dict[str, Any]]) -> None:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            conn.execute(
                "UPDATE orders_mkl SET client_id = ?, status = ?, updated_at = ? WHERE id = ?",
                (client_id, status, now, order_id),
            )
            conn.execute("DELETE FROM order_items_mkl WHERE order_id = ?", (order_id,))
            for it in items:
                conn.execute(
                    """
                    INSERT INTO order_items_mkl(order_id, product_id, sph, cyl, ax, bc, qty)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        it["product_id"],
                        it["sph"],
                        it.get("cyl"),
                        it.get("ax"),
                        it.get("bc"),
                        it["qty"],
                    ),
                )

    def update_order_mkl_status(self, order_id: int, status: str) -> None:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            conn.execute(
                "UPDATE orders_mkl SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )

    def delete_order_mkl(self, order_id: int) -> None:
        with self.tx() as conn:
            conn.execute("DELETE FROM orders_mkl WHERE id = ?", (order_id,))

    def list_orders_mkl(self, search: str = "", status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.connect()
        cur = conn.cursor()
        params: List[Any] = []
        where = []
        if search:
            like = f"%{search}%"
            where.append("(c.full_name LIKE ? OR c.phone LIKE ?)")
            params.extend([like, like])
        if status and status != "Все":
            where.append("o.status = ?")
            params.append(status)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        cur.execute(
            f"""
            SELECT o.*, c.full_name AS client_name, c.phone AS phone
            FROM orders_mkl o
            JOIN clients c ON c.id = o.client_id
            {where_sql}
            ORDER BY o.created_at DESC
            """,
            params,
        )
        orders = [dict(row) for row in cur.fetchall()]
        for od in orders:
            cur.execute(
                """
                SELECT i.*, p.name AS product_name
                FROM order_items_mkl i
                JOIN product_mkl p ON p.id = i.product_id
                WHERE i.order_id = ?
                ORDER BY i.id
                """,
                (od["id"],),
            )
            od["items"] = [dict(r) for r in cur.fetchall()]
        return orders

    # ---------- Orders Meridian ----------

    def create_order_meridian(self, status: str, items: Sequence[Dict[str, Any]]) -> int:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            cur = conn.execute(
                "INSERT INTO orders_meridian(number, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (None, status, now, now),
            )
            order_id = cur.lastrowid
            for it in items:
                conn.execute(
                    """
                    INSERT INTO order_items_meridian(order_id, product_id, sph, cyl, ax, qty)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        it["product_id"],
                        it["sph"],
                        it.get("cyl"),
                        it.get("ax"),
                        it["qty"],
                    ),
                )
            return order_id

    def update_order_meridian(self, order_id: int, status: str, items: Sequence[Dict[str, Any]]) -> None:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            conn.execute(
                "UPDATE orders_meridian SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )
            conn.execute("DELETE FROM order_items_meridian WHERE order_id = ?", (order_id,))
            for it in items:
                conn.execute(
                    """
                    INSERT INTO order_items_meridian(order_id, product_id, sph, cyl, ax, qty)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        it["product_id"],
                        it["sph"],
                        it.get("cyl"),
                        it.get("ax"),
                        it["qty"],
                    ),
                )

    def update_order_meridian_status(self, order_id: int, status: str) -> None:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self.tx() as conn:
            conn.execute(
                "UPDATE orders_meridian SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )

    def delete_order_meridian(self, order_id: int) -> None:
        with self.tx() as conn:
            conn.execute("DELETE FROM orders_meridian WHERE id = ?", (order_id,))

    def list_orders_meridian(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self.connect()
        cur = conn.cursor()
        params: List[Any] = []
        where = []
        if status and status != "Все":
            where.append("o.status = ?")
            params.append(status)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        cur.execute(
            f"""
            SELECT * FROM orders_meridian o
            {where_sql}
            ORDER BY o.created_at DESC
            """,
            params,
        )
        orders = [dict(row) for row in cur.fetchall()]
        for od in orders:
            cur.execute(
                """
                SELECT i.*, p.name AS product_name
                FROM order_items_meridian i
                JOIN product_meridian p ON p.id = i.product_id
                WHERE i.order_id = ?
                ORDER BY i.id
                """,
                (od["id"],),
            )
            od["items"] = [dict(r) for r in cur.fetchall()]
        return orders