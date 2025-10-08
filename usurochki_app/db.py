import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any


DB_FILENAME = "ussurochki.sqlite"


class Database:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.base_dir, exist_ok=True)

        # Миграция имени файла БД с одинарной S на двойную S
        old_db = os.path.join(self.base_dir, "usurochki.sqlite")
        new_db = os.path.join(self.base_dir, DB_FILENAME)
        if os.path.exists(old_db) and not os.path.exists(new_db):
            try:
                os.replace(old_db, new_db)
            except Exception:
                # если не удалось переименовать — продолжим с новым именем
                pass

        self.db_path = new

    def _init_schema(self):
        cur = self.conn.cursor()

        # Клиенты для МКЛ
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT
            )
            """
        )

        # Продукты для МКЛ
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        # Заказы для МКЛ
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
            """
        )

        # Позиции заказа МКЛ
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                sph REAL NOT NULL DEFAULT 0.0,
                cyl REAL,
                ax INTEGER,
                bc REAL,
                qty INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders_mkl(id) ON DELETE CASCADE
            )
            """
        )

        # Продукты для Меридиан
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )

        # Заказы для Меридиан
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Позиции заказа Меридиан
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                sph REAL NOT NULL DEFAULT 0.0,
                cyl REAL,
                ax INTEGER,
                qty INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders_meridian(id) ON DELETE CASCADE
            )
            """
        )

        self.conn.commit()

    # ---------- Клиенты (МКЛ) ----------
    def list_clients(self, search: str = "") -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        if search:
            like = f"%{search}%"
            cur.execute(
                "SELECT * FROM clients WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
                (like, like),
            )
        else:
            cur.execute("SELECT * FROM clients ORDER BY name")
        return cur.fetchall()

    def add_client(self, name: str, phone: Optional[str]) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO clients (name, phone) VALUES (?, ?)", (name, phone))
        self.conn.commit()
        return cur.lastrowid

    def update_client(self, client_id: int, name: str, phone: Optional[str]):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE clients SET name = ?, phone = ? WHERE id = ?",
            (name, phone, client_id),
        )
        self.conn.commit()

    def delete_client(self, client_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()

    # ---------- Продукты ----------
    def list_products(self, section: str) -> List[sqlite3.Row]:
        table = "products_mkl" if section == "mkl" else "products_meridian"
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {table} ORDER BY name")
        return cur.fetchall()

    def add_product(self, section: str, name: str) -> int:
        table = "products_mkl" if section == "mkl" else "products_meridian"
        cur = self.conn.cursor()
        cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, section: str, product_id: int, name: str):
        table = "products_mkl" if section == "mkl" else "products_meridian"
        cur = self.conn.cursor()
        cur.execute(f"UPDATE {table} SET name = ? WHERE id = ?", (name, product_id))
        self.conn.commit()

    def delete_product(self, section: str, product_id: int):
        table = "products_mkl" if section == "mkl" else "products_meridian"
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {table} WHERE id = ?", (product_id,))
        self.conn.commit()

    # ---------- Заказы МКЛ ----------
    def list_orders_mkl(
        self, status_filter: Optional[str] = None, search: str = ""
    ) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        query = """
            SELECT o.id, c.name AS client_name, c.phone AS client_phone, o.status, o.created_at
            FROM orders_mkl o
            JOIN clients c ON c.id = o.client_id
        """
        params: List[Any] = []
        where: List[str] = []
        if status_filter:
            where.append("o.status = ?")
            params.append(status_filter)
        if search:
            where.append("(c.name LIKE ? OR c.phone LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like])
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY o.created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()

    def create_order_mkl(self, client_id: int, status: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO orders_mkl (client_id, status, created_at) VALUES (?, ?, ?)",
            (client_id, status, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_order_mkl_status(self, order_id: int, status: str):
        cur = self.conn.cursor()
        cur.execute("UPDATE orders_mkl SET status = ? WHERE id = ?", (status, order_id))
        self.conn.commit()

    def delete_order_mkl(self, order_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM orders_mkl WHERE id = ?", (order_id,))
        self.conn.commit()

    def list_order_items_mkl(self, order_id: int) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM order_items_mkl WHERE order_id = ? ORDER BY id", (order_id,)
        )
        return cur.fetchall()

    def add_order_item_mkl(
        self,
        order_id: int,
        product_name: str,
        sph: float,
        cyl: Optional[float],
        ax: Optional[int],
        bc: Optional[float],
        qty: int,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO order_items_mkl (order_id, product_name, sph, cyl, ax, bc, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, product_name, sph, cyl, ax, bc, qty),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_order_item_mkl(
        self,
        item_id: int,
        product_name: str,
        sph: float,
        cyl: Optional[float],
        ax: Optional[int],
        bc: Optional[float],
        qty: int,
    ):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE order_items_mkl
               SET product_name = ?, sph = ?, cyl = ?, ax = ?, bc = ?, qty = ?
             WHERE id = ?
            """,
            (product_name, sph, cyl, ax, bc, qty, item_id),
        )
        self.conn.commit()

    def delete_order_item_mkl(self, item_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM order_items_mkl WHERE id = ?", (item_id,))
        self.conn.commit()

    # ---------- Заказы Меридиан ----------
    def _next_meridian_number(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT MAX(number) AS max_num FROM orders_meridian")
        row = cur.fetchone()
        return (row["max_num"] or 0) + 1

    def list_orders_meridian(self, status_filter: Optional[str] = None) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        query = "SELECT id, number, status, created_at FROM orders_meridian"
        params: List[Any] = []
        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter)
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()

    def create_order_meridian(self, status: str) -> int:
        cur = self.conn.cursor()
        number = self._next_meridian_number()
        cur.execute(
            "INSERT INTO orders_meridian (number, status, created_at) VALUES (?, ?, ?)",
            (number, status, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_order_meridian_status(self, order_id: int, status: str):
        cur = self.conn.cursor()
        cur.execute("UPDATE orders_meridian SET status = ? WHERE id = ?", (status, order_id))
        self.conn.commit()

    def delete_order_meridian(self, order_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM orders_meridian WHERE id = ?", (order_id,))
        self.conn.commit()

    def list_order_items_meridian(self, order_id: int) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM order_items_meridian WHERE order_id = ? ORDER BY id",
            (order_id,),
        )
        return cur.fetchall()

    def add_order_item_meridian(
        self,
        order_id: int,
        product_name: str,
        sph: float,
        cyl: Optional[float],
        ax: Optional[int],
        qty: int,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO order_items_meridian (order_id, product_name, sph, cyl, ax, qty)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (order_id, product_name, sph, cyl, ax, qty),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_order_item_meridian(
        self,
        item_id: int,
        product_name: str,
        sph: float,
        cyl: Optional[float],
        ax: Optional[int],
        qty: int,
    ):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE order_items_meridian
               SET product_name = ?, sph = ?, cyl = ?, ax = ?, qty = ?
             WHERE id = ?
            """,
            (product_name, sph, cyl, ax, qty, item_id),
        )
        self.conn.commit()

    def delete_order_item_meridian(self, item_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM order_items_meridian WHERE id = ?", (item_id,))
        self.conn.commit()

    # ---------- Экспорт ----------
    def export_orders_mkl(self, status: str, filepath: str):
        rows = self.list_orders_mkl(status_filter=status)
        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows:
                order_id = row["id"]
                items = self.list_order_items_mkl(order_id)
                items_text = "; ".join(
                    [
                        f'{it["product_name"]} SPH={it["sph"]}'
                        + (f', CYL={it["cyl"]}' if it["cyl"] is not None else "")
                        + (f', AX={it["ax"]}' if it["ax"] is not None else "")
                        + (f', BC={it["bc"]}' if it["bc"] is not None else "")
                        + f', Qty={it["qty"]}'
                        for it in items
                    ]
                )
                line = "\t".join(
                    [
                        row["client_name"],
                        row["client_phone"] or "",
                        items_text,
                        row["status"],
                        row["created_at"],
                    ]
                )
                f.write(line + "\n")

    def export_unordered_meridian_items(self, filepath: str):
        orders = self.list_orders_meridian(status_filter="Не заказан")
        with open(filepath, "w", encoding="utf-8") as f:
            for row in orders:
                order_id = row["id"]
                items = self.list_order_items_meridian(order_id)
                items_text = "; ".join(
                    [
                        f'{it["product_name"]} SPH={it["sph"]}'
                        + (f', CYL={it["cyl"]}' if it["cyl"] is not None else "")
                        + (f', AX={it["ax"]}' if it["ax"] is not None else "")
                        + f', Qty={it["qty"]}'
                        for it in items
                    ]
                )
                line = "\t".join(
                    [
                        str(row["number"]),
                        items_text,
                        row["status"],
                        row["created_at"],
                    ]
                )
                f.write(line + "\n")

    def close(self):
        self.conn.close()