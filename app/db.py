import sqlite3
from datetime import datetime


class AppDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable foreign keys
        try:
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        # Clients
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                phone TEXT NOT NULL
            );
            """
        )
        # Products (generic, kept for backward compatibility)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # Separate product catalogs for MKL and Meridian
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # MKL orders (flat structure for now)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mkl_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                phone TEXT NOT NULL,
                product TEXT NOT NULL,
                sph TEXT,
                cyl TEXT,
                ax TEXT,
                bc TEXT,
                qty TEXT,
                status TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        # Add 'comment' column if it doesn't exist
        try:
            cur.execute("ALTER TABLE mkl_orders ADD COLUMN comment TEXT;")
        except Exception:
            pass
        # Meridian orders (header) + items
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meridian_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meridian_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                sph TEXT,
                cyl TEXT,
                ax TEXT,
                d TEXT,
                qty TEXT,
                FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
            );
            """
        )

        # Prices table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL
            );
            """
        )

        self.conn.commit()

    # --- Clients ---
    def list_clients(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, fio, phone FROM clients ORDER BY fio COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "fio": r["fio"], "phone": r["phone"]} for r in rows]

    def add_client(self, fio: str, phone: str) -> int:
        cur = self.conn.execute("INSERT INTO clients (fio, phone) VALUES (?, ?);", (fio, phone))
        self.conn.commit()
        return cur.lastrowid

    def update_client(self, client_id: int, fio: str, phone: str):
        self.conn.execute("UPDATE clients SET fio=?, phone=? WHERE id=?;", (fio, phone, client_id))
        self.conn.commit()

    def delete_client(self, client_id: int):
        self.conn.execute("DELETE FROM clients WHERE id=?;", (client_id,))
        self.conn.commit()

    # --- Products (generic) ---
    def list_products(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name FROM products ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def add_product(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO products (name) VALUES (?);", (name,))
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id: int, name: str):
        self.conn.execute("UPDATE products SET name=? WHERE id=?;", (name, product_id))
        self.conn.commit()

    def delete_product(self, product_id: int):
        self.conn.execute("DELETE FROM products WHERE id=?;", (product_id,))
        self.conn.commit()

    # --- Products MKL ---
    def list_products_mkl(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name FROM products_mkl ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def add_product_mkl(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO products_mkl (name) VALUES (?);", (name,))
        self.conn.commit()
        return cur.lastrowid

    def update_product_mkl(self, product_id: int, name: str):
        self.conn.execute("UPDATE products_mkl SET name=? WHERE id=?;", (name, product_id))
        self.conn.commit()

    def delete_product_mkl(self, product_id: int):
        self.conn.execute("DELETE FROM products_mkl WHERE id=?;", (product_id,))
        self.conn.commit()

    # --- Products Meridian ---
    def list_products_meridian(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name FROM products_meridian ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def add_product_meridian(self, name: str) -> int:
        cur = self.conn.execute("INSERT INTO products_meridian (name) VALUES (?);", (name,))
        self.conn.commit()
        return cur.lastrowid

    def update_product_meridian(self, product_id: int, name: str):
        self.conn.execute("UPDATE products_meridian SET name=? WHERE id=?;", (name, product_id))
        self.conn.commit()

    def delete_product_meridian(self, product_id: int):
        self.conn.execute("DELETE FROM products_meridian WHERE id=?;", (product_id,))
        self.conn.commit()

    # --- MKL Orders ---
    def list_mkl_orders(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, fio, phone, product, sph, cyl, ax, bc, qty, status, date, COALESCE(comment,'') AS comment FROM mkl_orders ORDER BY id DESC;"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "fio": r["fio"],
                "phone": r["phone"],
                "product": r["product"],
                "sph": r["sph"] or "",
                "cyl": r["cyl"] or "",
                "ax": r["ax"] or "",
                "bc": r["bc"] or "",
                "qty": r["qty"] or "",
                "status": r["status"],
                "date": r["date"],
                "comment": r["comment"] or "",
            }
            for r in rows
        ]

    def add_mkl_order(self, order: dict) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO mkl_orders (fio, phone, product, sph, cyl, ax, bc, qty, status, date, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                order.get("fio", ""),
                order.get("phone", ""),
                order.get("product", ""),
                order.get("sph", ""),
                order.get("cyl", ""),
                order.get("ax", ""),
                order.get("bc", ""),
                order.get("qty", ""),
                order.get("status", "Не заказан"),
                order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
                (order.get("comment", "") or "").strip(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_mkl_order(self, order_id: int, fields: dict):
        # Only update provided fields
        cols = []
        vals = []
        for k in ("fio", "phone", "product", "sph", "cyl", "ax", "bc", "qty", "status", "date", "comment"):
            if k in fields:
                cols.append(f"{k}=?")
                vals.append(fields[k])
        if cols:
            vals.append(order_id)
            self.conn.execute(f"UPDATE mkl_orders SET {', '.join(cols)} WHERE id=?;", tuple(vals))
            self.conn.commit()

    def delete_mkl_order(self, order_id: int):
        self.conn.execute("DELETE FROM mkl_orders WHERE id=?;", (order_id,))
        self.conn.commit()

    # --- Meridian Orders + Items ---
    def list_meridian_orders(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, status, date FROM meridian_orders ORDER BY id DESC;"
        ).fetchall()
        return [{"id": r["id"], "title": r["title"], "status": r["status"], "date": r["date"]} for r in rows]

    def get_meridian_items(self, order_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, order_id, product, sph, cyl, ax, d, qty FROM meridian_items WHERE order_id=? ORDER BY id ASC;",
            (order_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "order_id": r["order_id"],
                "product": r["product"],
                "sph": r["sph"] or "",
                "cyl": r["cyl"] or "",
                "ax": r["ax"] or "",
                "d": r["d"] or "",
                "qty": r["qty"] or "",
            }
            for r in rows
        ]

    def add_meridian_order(self, order: dict, items: list[dict]) -> int:
        cur = self.conn.execute(
            "INSERT INTO meridian_orders (title, status, date) VALUES (?, ?, ?);",
            (order.get("title", ""), order.get("status", "Не заказан"), order.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))),
        )
        order_id = cur.lastrowid
        for it in items:
            self.conn.execute(
                """
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("d", ""),
                    it.get("qty", ""),
                ),
            )
        self.conn.commit()
        return order_id

    def update_meridian_order(self, order_id: int, fields: dict):
        cols = []
        vals = []
        for k in ("title", "status", "date"):
            if k in fields:
                cols.append(f"{k}=?")
                vals.append(fields[k])
        if cols:
            vals.append(order_id)
            self.conn.execute(f"UPDATE meridian_orders SET {', '.join(cols)} WHERE id=?;", tuple(vals))
            self.conn.commit()

    def replace_meridian_items(self, order_id: int, items: list[dict]):
        # Replace items for order
        self.conn.execute("DELETE FROM meridian_items WHERE order_id=?;", (order_id,))
        for it in items:
            self.conn.execute(
                """
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("d", ""),
                    it.get("qty", ""),
                ),
            )
        self.conn.commit()

    def delete_meridian_order(self, order_id: int):
        # Items will be cascaded
        self.conn.execute("DELETE FROM meridian_orders WHERE id=?;", (order_id,))
        self.conn.commit()

    # --- Prices ---
    def list_prices(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, path FROM prices ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "path": r["path"]} for r in rows]

    def add_price(self, name: str, path: str) -> int:
        cur = self.conn.execute("INSERT INTO prices (name, path) VALUES (?, ?);", (name, path))
        self.conn.commit()
        return cur.lastrowid

    def update_price(self, price_id: int, name: str, path: str):
        self.conn.execute("UPDATE prices SET name=?, path=? WHERE id=?;", (name, path, price_id))
        self.conn.commit()

    def delete_price(self, price_id: int):
        self.conn.execute("DELETE FROM prices WHERE id=?;", (price_id,))
        self.conn.commit()