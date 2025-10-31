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
        # Product groups (hierarchy depth=1)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS product_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        # Products (generic)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # Migrations: add group_id and sort_order to products if missing
        try:
            cur.execute("ALTER TABLE products ADD COLUMN group_id INTEGER REFERENCES product_groups(id) ON DELETE SET NULL;")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE products ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;")
        except Exception:
            pass

        # Separate product catalogs for MKL and Meridian
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # MKL product groups and migrations for products_mkl
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS product_groups_mkl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                parent_id INTEGER REFERENCES product_groups_mkl(id) ON DELETE CASCADE
            );
            """
        )
        # Migrations for existing DBs: add missing columns
        try:
            cur.execute("ALTER TABLE product_groups_mkl ADD COLUMN parent_id INTEGER REFERENCES product_groups_mkl(id) ON DELETE CASCADE;")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE products_mkl ADD COLUMN group_id INTEGER REFERENCES product_groups_mkl(id) ON DELETE SET NULL;")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE products_mkl ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;")
        except Exception:
            pass

        # Meridian product groups (now hierarchical) and products
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS product_groups_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                parent_id INTEGER REFERENCES product_groups_meridian(id) ON DELETE CASCADE
            );
            """
        )
        # Migration: add parent_id to product_groups_meridian if missing
        try:
            cur.execute("ALTER TABLE product_groups_meridian ADD COLUMN parent_id INTEGER REFERENCES product_groups_meridian(id) ON DELETE CASCADE;")
        except Exception:
            pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products_meridian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
            """
        )
        # Migrations for meridian products: add group_id and sort_order if missing
        try:
            cur.execute("ALTER TABLE products_meridian ADD COLUMN group_id INTEGER REFERENCES product_groups_meridian(id) ON DELETE SET NULL;")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE products_meridian ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;")
        except Exception:
            pass
        # MKL orders
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
                "add" TEXT,
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
        # Add 'add' (ADD) column if it doesn't exist (placed between ax and bc in schema order)
        try:
            cur.execute("ALTER TABLE mkl_orders ADD COLUMN \"add\" TEXT;")
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
                add TEXT,
                d TEXT,
                qty TEXT,
                FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
            );
            """
        )
        # Migration: add ADD column if missing
        try:
            cur.execute("ALTER TABLE meridian_items ADD COLUMN add TEXT;")
        except Exception:
            pass

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

    # --- Product Groups ---
    def list_product_groups(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, sort_order FROM product_groups ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "sort_order": r["sort_order"]} for r in rows]

    def _next_group_sort(self) -> int:
        row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM product_groups;").fetchone()
        return (row["m"] or 0) + 1

    def add_product_group(self, name: str) -> int:
        sort_order = self._next_group_sort()
        cur = self.conn.execute("INSERT INTO product_groups (name, sort_order) VALUES (?, ?);", (name, sort_order))
        self.conn.commit()
        return cur.lastrowid

    def update_product_group(self, group_id: int, name: str):
        self.conn.execute("UPDATE product_groups SET name=? WHERE id=?;", (name, group_id))
        self.conn.commit()

    def delete_product_group(self, group_id: int):
        # Detach products from group, then delete group
        self.conn.execute("UPDATE products SET group_id=NULL WHERE group_id=?;", (group_id,))
        self.conn.execute("DELETE FROM product_groups WHERE id=?;", (group_id,))
        self.conn.commit()

    def move_group(self, group_id: int, direction: int):
        # direction: -1 up, +1 down
        rows = self.conn.execute("SELECT id, sort_order FROM product_groups ORDER BY sort_order ASC, id ASC;").fetchall()
        idx = None
        for i, r in enumerate(rows):
            if r["id"] == group_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE product_groups SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE product_groups SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    # --- Products (generic) ---
    def list_products(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name FROM products ORDER BY name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def list_products_by_group(self, group_id: int | None) -> list[dict]:
        if group_id is None:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products WHERE group_id IS NULL ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        else:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products WHERE group_id=? ORDER BY sort_order ASC, name COLLATE NOCASE;", (group_id,)).fetchall()
        return [{"id": r["id"], "name": r["name"], "group_id": r["group_id"], "sort_order": r["sort_order"]} for r in rows]

    def _next_product_sort(self, group_id: int | None) -> int:
        if group_id is None:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products WHERE group_id IS NULL;").fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products WHERE group_id=?;", (group_id,)).fetchone()
        return (row["m"] or 0) + 1

    def add_product(self, name: str, group_id: int | None = None) -> int:
        sort_order = self._next_product_sort(group_id)
        cur = self.conn.execute("INSERT INTO products (name, group_id, sort_order) VALUES (?, ?, ?);", (name, group_id, sort_order))
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id: int, name: str, group_id: int | None = None):
        if group_id is None:
            self.conn.execute("UPDATE products SET name=? WHERE id=?;", (name, product_id))
        else:
            self.conn.execute("UPDATE products SET name=?, group_id=? WHERE id=?;", (name, group_id, product_id))
        self.conn.commit()

    def delete_product(self, product_id: int):
        self.conn.execute("DELETE FROM products WHERE id=?;", (product_id,))
        self.conn.commit()

    def move_product(self, product_id: int, direction: int):
        # direction: -1 up, +1 down within the same group
        r = self.conn.execute("SELECT id, group_id, sort_order FROM products WHERE id=?;", (product_id,)).fetchone()
        if not r:
            return
        gid = r["group_id"]
        rows = self.conn.execute(
            "SELECT id, sort_order FROM products WHERE (group_id IS ? OR group_id = ?) ORDER BY sort_order ASC, id ASC;",
            (None if gid is None else gid, gid),
        ).fetchall()
        idx = None
        for i, row in enumerate(rows):
            if row["id"] == product_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE products SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE products SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    # --- Products MKL with Groups ---
    def list_product_groups_mkl(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, sort_order, parent_id FROM product_groups_mkl ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "sort_order": r["sort_order"], "parent_id": r["parent_id"]} for r in rows]

    def _next_group_sort_mkl(self, parent_id: int | None) -> int:
        if parent_id is None:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM product_groups_mkl WHERE parent_id IS NULL;").fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM product_groups_mkl WHERE parent_id=?;", (parent_id,)).fetchone()
        return (row["m"] or 0) + 1

    def add_product_group_mkl(self, name: str, parent_id: int | None = None) -> int:
        sort_order = self._next_group_sort_mkl(parent_id)
        cur = self.conn.execute("INSERT INTO product_groups_mkl (name, sort_order, parent_id) VALUES (?, ?, ?);", (name, sort_order, parent_id))
        self.conn.commit()
        return cur.lastrowid

    def update_product_group_mkl(self, group_id: int, name: str, parent_id: int | None = None):
        self.conn.execute("UPDATE product_groups_mkl SET name=?, parent_id=? WHERE id=?;", (name, parent_id, group_id))
        self.conn.commit()

    def delete_product_group_mkl(self, group_id: int):
        # Detach products from group, then delete group; child groups will be cascaded by FK
        self.conn.execute("UPDATE products_mkl SET group_id=NULL WHERE group_id=?;", (group_id,))
        self.conn.execute("DELETE FROM product_groups_mkl WHERE id=?;", (group_id,))
        self.conn.commit()

    def move_group_mkl(self, group_id: int, direction: int):
        # Move within siblings (same parent_id)
        r = self.conn.execute("SELECT id, parent_id, sort_order FROM product_groups_mkl WHERE id=?;", (group_id,)).fetchone()
        if not r:
            return
        parent_id = r["parent_id"]
        rows = self.conn.execute(
            "SELECT id, sort_order FROM product_groups_mkl WHERE (parent_id IS ? OR parent_id = ?) ORDER BY sort_order ASC, id ASC;",
            (None if parent_id is None else parent_id, parent_id),
        ).fetchall()
        idx = None
        for i, row in enumerate(rows):
            if row["id"] == group_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE product_groups_mkl SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE product_groups_mkl SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    def list_products_mkl(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_mkl ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "group_id": r["group_id"], "sort_order": r["sort_order"]} for r in rows]

    def list_products_mkl_by_group(self, group_id: int | None) -> list[dict]:
        if group_id is None:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_mkl WHERE group_id IS NULL ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        else:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_mkl WHERE group_id=? ORDER BY sort_order ASC, name COLLATE NOCASE;", (group_id,)).fetchall()
        return [{"id": r["id"], "name": r["name"], "group_id": r["group_id"], "sort_order": r["sort_order"]} for r in rows]

    def _next_product_sort_mkl(self, group_id: int | None) -> int:
        if group_id is None:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products_mkl WHERE group_id IS NULL;").fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products_mkl WHERE group_id=?;", (group_id,)).fetchone()
        return (row["m"] or 0) + 1

    def add_product_mkl(self, name: str, group_id: int | None = None) -> int:
        sort_order = self._next_product_sort_mkl(group_id)
        cur = self.conn.execute("INSERT INTO products_mkl (name, group_id, sort_order) VALUES (?, ?, ?);", (name, group_id, sort_order))
        self.conn.commit()
        return cur.lastrowid

    def update_product_mkl(self, product_id: int, name: str, group_id: int | None = None):
        if group_id is None:
            self.conn.execute("UPDATE products_mkl SET name=? WHERE id=?;", (name, product_id))
        else:
            self.conn.execute("UPDATE products_mkl SET name=?, group_id=? WHERE id=?;", (name, group_id, product_id))
        self.conn.commit()

    def delete_product_mkl(self, product_id: int):
        self.conn.execute("DELETE FROM products_mkl WHERE id=?;", (product_id,))
        self.conn.commit()

    def move_product_mkl(self, product_id: int, direction: int):
        r = self.conn.execute("SELECT id, group_id, sort_order FROM products_mkl WHERE id=?;", (product_id,)).fetchone()
        if not r:
            return
        gid = r["group_id"]
        rows = self.conn.execute(
            "SELECT id, sort_order FROM products_mkl WHERE (group_id IS ? OR group_id = ?) ORDER BY sort_order ASC, id ASC;",
            (None if gid is None else gid, gid),
        ).fetchall()
        idx = None
        for i, row in enumerate(rows):
            if row["id"] == product_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE products_mkl SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE products_mkl SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    # --- Products Meridian with Groups ---
    def list_product_groups_meridian(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, sort_order, parent_id FROM product_groups_meridian ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "sort_order": r["sort_order"], "parent_id": r["parent_id"]} for r in rows]

    def _next_group_sort_meridian(self, parent_id: int | None) -> int:
        if parent_id is None:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM product_groups_meridian WHERE parent_id IS NULL;").fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM product_groups_meridian WHERE parent_id=?;", (parent_id,)).fetchone()
        return (row["m"] or 0) + 1

    def add_product_group_meridian(self, name: str, parent_id: int | None = None) -> int:
        sort_order = self._next_group_sort_meridian(parent_id)
        cur = self.conn.execute("INSERT INTO product_groups_meridian (name, sort_order, parent_id) VALUES (?, ?, ?);", (name, sort_order, parent_id))
        self.conn.commit()
        return cur.lastrowid

    def update_product_group_meridian(self, group_id: int, name: str, parent_id: int | None = None):
        self.conn.execute("UPDATE product_groups_meridian SET name=?, parent_id=? WHERE id=?;", (name, parent_id, group_id))
        self.conn.commit()

    def delete_product_group_meridian(self, group_id: int):
        self.conn.execute("UPDATE products_meridian SET group_id=NULL WHERE group_id=?;", (group_id,))
        self.conn.execute("DELETE FROM product_groups_meridian WHERE id=?;", (group_id,))
        self.conn.commit()

    def move_group_meridian(self, group_id: int, direction: int):
        # Move within siblings for the same parent_id
        r = self.conn.execute("SELECT id, parent_id, sort_order FROM product_groups_meridian WHERE id=?;", (group_id,)).fetchone()
        if not r:
            return
        parent_id = r["parent_id"]
        rows = self.conn.execute(
            "SELECT id, sort_order FROM product_groups_meridian WHERE (parent_id IS ? OR parent_id = ?) ORDER BY sort_order ASC, id ASC;",
            (None if parent_id is None else parent_id, parent_id),
        ).fetchall()
        idx = None
        for i, row in enumerate(rows):
            if row["id"] == group_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE product_groups_meridian SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE product_groups_meridian SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    def list_products_meridian(self) -> list[dict]:
        rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_meridian ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        return [{"id": r["id"], "name": r["name"], "group_id": r["group_id"], "sort_order": r["sort_order"]} for r in rows]

    def list_products_meridian_by_group(self, group_id: int | None) -> list[dict]:
        if group_id is None:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_meridian WHERE group_id IS NULL ORDER BY sort_order ASC, name COLLATE NOCASE;").fetchall()
        else:
            rows = self.conn.execute("SELECT id, name, group_id, sort_order FROM products_meridian WHERE group_id=? ORDER BY sort_order ASC, name COLLATE NOCASE;", (group_id,)).fetchall()
        return [{"id": r["id"], "name": r["name"], "group_id": r["group_id"], "sort_order": r["sort_order"]} for r in rows]

    def _next_product_sort_meridian(self, group_id: int | None) -> int:
        if group_id is None:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products_meridian WHERE group_id IS NULL;").fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products_meridian WHERE group_id=?;", (group_id,)).fetchone()
        return (row["m"] or 0) + 1

    def add_product_meridian(self, name: str, group_id: int | None = None) -> int:
        cur = self.conn.execute("INSERT INTO products_meridian (name, group_id, sort_order) VALUES (?, ?, ?);", (name, group_id, self._next_product_sort_meridian(group_id)))
        self.conn.commit()
        return cur.lastrowid

    def update_product_meridian(self, product_id: int, name: str, group_id: int | None = None):
        if group_id is None:
            self.conn.execute("UPDATE products_meridian SET name=? WHERE id=?;", (name, product_id))
        else:
            self.conn.execute("UPDATE products_meridian SET name=?, group_id=? WHERE id=?;", (name, group_id, product_id))
        self.conn.commit()

    def delete_product_meridian(self, product_id: int):
        self.conn.execute("DELETE FROM products_meridian WHERE id=?;", (product_id,))
        self.conn.commit()

    def move_product_meridian(self, product_id: int, direction: int):
        r = self.conn.execute("SELECT id, group_id, sort_order FROM products_meridian WHERE id=?;", (product_id,)).fetchone()
        if not r:
            return
        gid = r["group_id"]
        rows = self.conn.execute(
            "SELECT id, sort_order FROM products_meridian WHERE (group_id IS ? OR group_id = ?) ORDER BY sort_order ASC, id ASC;",
            (None if gid is None else gid, gid),
        ).fetchall()
        idx = None
        for i, row in enumerate(rows):
            if row["id"] == product_id:
                idx = i
                break
        if idx is None:
            return
        j = idx + (1 if direction > 0 else -1)
        if j < 0 or j >= len(rows):
            return
        a = rows[idx]
        b = rows[j]
        self.conn.execute("UPDATE products_meridian SET sort_order=? WHERE id=?;", (b["sort_order"], a["id"]))
        self.conn.execute("UPDATE products_meridian SET sort_order=? WHERE id=?;", (a["sort_order"], b["id"]))
        self.conn.commit()

    # --- MKL Orders ---
    def list_mkl_orders(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, fio, phone, product, sph, cyl, ax, \"add\", bc, qty, status, date, COALESCE(comment,'') AS comment FROM mkl_orders ORDER BY id DESC;"
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
                "add": r["add"] or "",
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
            INSERT INTO mkl_orders (fio, phone, product, sph, cyl, ax, "add", bc, qty, status, date, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                order.get("fio", ""),
                order.get("phone", ""),
                order.get("product", ""),
                order.get("sph", ""),
                order.get("cyl", ""),
                order.get("ax", ""),
                order.get("add", ""),
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
        for k in ("fio", "phone", "product", "sph", "cyl", "ax", "add", "bc", "qty", "status", "date", "comment"):
            if k in fields:
                col_name = "\"add\"" if k == "add" else k
                cols.append(f"{col_name}=?")
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
            "SELECT id, order_id, product, sph, cyl, ax, add, d, qty FROM meridian_items WHERE order_id=? ORDER BY id ASC;",
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
                "add": r["add"] or "",
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
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, add, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("add", ""),
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
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, add, d, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    it.get("product", ""),
                    it.get("sph", ""),
                    it.get("cyl", ""),
                    it.get("ax", ""),
                    it.get("add", ""),
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