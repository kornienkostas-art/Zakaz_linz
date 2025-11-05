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
        # Optional seed for MKL catalog (Adria hierarchy)
        try:
            self._ensure_mkl_seed_adria()
        except Exception:
            pass
        # Additional seed for other brands and solutions (idempotent)
        try:
            self._ensure_mkl_seed_brands()
        except Exception:
            pass
        # Mirror MKL catalog into Meridian under a bottom group "Контактные Линзы"
        try:
            self._ensure_meridian_contacts_from_mkl()
        except Exception:
            pass

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
                "add" TEXT,
                d TEXT,
                qty TEXT,
                FOREIGN KEY(order_id) REFERENCES meridian_orders(id) ON DELETE CASCADE
            );
            """
        )
        # Migration: add ADD column if missing
        try:
            cur.execute("ALTER TABLE meridian_items ADD COLUMN \"add\" TEXT;")
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

    # --- Seed MKL catalog (Adria hierarchy and products) ---
    def _ensure_mkl_seed_adria(self):
        """
        Create Adria group tree with products if it doesn't exist yet.
        Idempotent: checks 'Adria' top-level group presence; if found, does nothing.
        """
        row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Adria",),
        ).fetchone()
        if row:
            return  # already seeded (or manually created)

        def ensure_group(name: str, parent_id: int | None) -> int:
            r = self.conn.execute(
                "SELECT id FROM product_groups_mkl WHERE name=? AND (parent_id IS ? OR parent_id = ?);",
                (name, None if parent_id is None else parent_id, parent_id),
            ).fetchone()
            if r:
                return r["id"]
            return self.add_product_group_mkl(name, parent_id)

        def ensure_product(name: str, gid: int):
            r = self.conn.execute(
                "SELECT id FROM products_mkl WHERE name=? AND group_id=?;",
                (name, gid),
            ).fetchone()
            if r:
                return r["id"]
            return self.add_product_mkl(name, gid)

        # Build hierarchy
        adria = ensure_group("Adria", None)
        g_daily = ensure_group("Однодневные линзы", adria)
        g_monthly = ensure_group("Ежемесячные линзы", adria)
        g_quarterly = ensure_group("Квартальные линзы", adria)
        g_multifocal = ensure_group("Мультифакальные линзы", adria)
        g_color = ensure_group("Цветные линзы", adria)

        # Однодневные линзы
        for nm in [
            "Adria GO 180pk 8.6 BC",
            "Adria GO 90pk 8.6 BC",
            "Adria GO 30pk 8.6 BC",
            "Adria GO 10pk 8.6 BC",
            "Adria GO 5pk 8.6 BC",
            "ADRIA X 30pk 8.6 BC",
            "ADRIA EGO 30pk 8.6 BC",
            "Adria Zero 90pk 8.6 BC",
            "Adria Zero 30pk 8.6 BC",
            "Adria Zero 5pk 8.6 BC",
        ]:
            ensure_product(nm, g_daily)

        # Ежемесячные линзы
        for nm in [
            "Adria sport 6pk 8.6 BC",
            "Adria O2O2 2pk 8.6 BC",
            "Adria O2O2 6pk 8.6 BC",
            "Adria O2O2 12pk 8.6 BC",
        ]:
            ensure_product(nm, g_monthly)

        # Квартальные линзы
        for nm in [
            "ADRIA Season 2pk 8.6 BC",
            "ADRIA Season 4pk 8.6 BC",
            "ADRIA Season 4pk 8.9 BC",
        ]:
            ensure_product(nm, g_quarterly)

        # Мультифакальные линзы
        for nm in [
            "Adria O2O2 Toric 2pk 8.6 BC",
            "Adria O2O2 Toric 6pk 8.6 BC",
            "Adria O2O2 Multifocal 2pk 8.6 BC",
            "Adria O2O2 Multifocal 6pk 8.6 BC",
        ]:
            ensure_product(nm, g_multifocal)

        # Цветные линзы → Квартальные линзы
        g_color_quarterly = ensure_group("Квартальные линзы", g_color)

        # ADRIA Effect
        g_effect = ensure_group("ADRIA Effect", g_color_quarterly)
        for nm in [
            "ADRIA Effect Topaz (топаз)",
            "ADRIA Effect Grafit (графит)",
            "ADRIA Effect Cristal (кристалл)",
            "ADRIA Effect Quartz (кварц)",
            "ADRIA Effect Ivory (айвори)",
            "ADRIA Effect Caramel (карамель)",
        ]:
            ensure_product(nm, g_effect)

        # ADRIA Glamorous
        g_glam = ensure_group("ADRIA Glamorous", g_color_quarterly)
        for nm in [
            "ADRIA Glamorous Blue (голубой)",
            "ADRIA Glamorous Black (черный)",
            "ADRIA Glamorous Violet (фиолетовый)",
            "ADRIA Glamorous Turquoise (бирюзовый)",
            "ADRIA Glamorous Brown (карий)",
            "ADRIA Glamorous Green (зеленый)",
            "ADRIA Glamorous Gray (серый)",
            "ADRIA Glamorous Gold (золото)",
            "ADRIA Glamorous Pure Gold (чистое золото)",
        ]:
            ensure_product(nm, g_glam)

        # ADRIA Color 1 Tone
        g_c1 = ensure_group("ADRIA Color 1 Tone", g_color_quarterly)
        for nm in [
            "ADRIA Color 1 Tone Blue (голубой)",
            "ADRIA Color 1 Tone Green (зеленый)",
            "ADRIA Color 1 Tone Lavender (лаванда)",
            "ADRIA Color 1 Tone Gray (серый)",
            "ADRIA Color 1 Tone Brown (карий)",
        ]:
            ensure_product(nm, g_c1)

        # ADRIA Color 2 Tone
        g_c2 = ensure_group("ADRIA Color 2 tone", g_color_quarterly)
        for nm in [
            "ADRIA Color 2 Tone True Sapphire (сапфир)",
            "ADRIA Color 2 Tone Turquoise (бирюзовый)",
            "ADRIA Color 2 Tone Brown (карий)",
            "ADRIA Color 2 Tone Green (зеленый)",
            "ADRIA Color 2 Tone Gray (серый)",
            "ADRIA Color 2 Tone Amethyst (аметист)",
            "ADRIA Color 2 Tone Hazel (орех)",
        ]:
            ensure_product(nm, g_c2)

        # ADRIA Color 3 Tone
        g_c3 = ensure_group("ADRIA Color 3 tone", g_color_quarterly)
        for nm in [
            "ADRIA Color 3 Tone Green (зеленый)",
            "ADRIA Color 3 Tone Turquoise (бирюзовый)",
            "ADRIA Color 3 Tone True Sapphire (сапфир)",
            "ADRIA Color 3 Tone Gray (серый)",
            "ADRIA Color 3 Tone Brown (карий)",
            "ADRIA Color 3 Tone Honey (медовый)",
            "ADRIA Color 3 Tone Hazel (орех)",
            "ADRIA Color 3 Tone Pure Hazel (насыщенный орех)",
            "ADRIA Color 3 Tone Amethyst (аметист)",
        ]:
            ensure_product(nm, g_c3)

        # ADRIA Crazy
        g_crazy = ensure_group("ADRIA Crazy", g_color_quarterly)
        for nm in [
            "ADRIA Crazy Black Out (черное пятно)",
            "ADRIA Crazy MSN (сеть)",
            "ADRIA Crazy Hot Red (яркий красный)",
            "ADRIA Crazy Zombo (зомбо)",
            "ADRIA Crazy White Vampire (белый вампир)",
            "ADRIA Crazy White Out (белое пятно)",
            "ADRIA Crazy Maniac (маньяк)",
            "ADRIA Crazy Blue Angelic (голубой ангел)",
            "ADRIA Crazy Blue Wheel (голубое колесо)",
            "ADRIA Crazy Demon (демон)",
            "ADRIA Crazy Robot (робот)",
            "ADRIA Crazy Psyho (психо)",
            "ADRIA Crazy Solid Yellow (сплошной желтый)",
            "ADRIA Crazy White Cat (белая кошка)",
            "ADRIA Crazy Black Star (черная звезда)",
            "ADRIA Crazy Blood (кровь)",
            "ADRIA Crazy Cross (крест)",
            "ADRIA Crazy Devil (дьявол)",
            "ADRIA Crazy Eagle (орел)",
            "ADRIA Crazy Green Banshee (зеленая опасность)",
            "ADRIA Crazy Green Cat (зеленая кошка)",
            "ADRIA Crazy Lunatic (лунатик)",
            "ADRIA Crazy Pink (розовый)",
            "ADRIA Crazy Red Cat (красная кошка)",
            "ADRIA Crazy Sharingan (шаринган)",
            "ADRIA Crazy Target (мишень)",
            "ADRIA Crazy Wild Fire (дикий огонь)",
            "ADRIA Crazy Yellow Cat (желтая кошка)",
            "ADRIA Crazy Yellow Wolf (желтый волк)",
            "ADRIA Crazy Red Vampire (красный вампир)",
        ]:
            ensure_product(nm, g_crazy)

        # ADRIA Sclera Pro
        g_sclera = ensure_group("ADRIA Sclera Pro", g_color_quarterly)
        ensure_product("ADRIA Sclera Pro Demon look", g_sclera)

        # ADRIA Neon
        g_neon = ensure_group("ADRIA Neon", g_color_quarterly)
        for nm in [
            "ADRIA Neon Green (зеленый)",
            "ADRIA Neon Blue (голубой)",
            "ADRIA Neon White (белый)",
            "ADRIA Neon Pink (розовый)",
            "ADRIA Neon Lemon (лимонный)",
            "ADRIA Neon Violet (фиолетовый)",
            "ADRIA Neon Orange (оранжевый)",
        ]:
            ensure_product(nm, g_neon)

        # Однодневные цветные линзы (подгруппа в Цветные линзы)
        g_color_daily = ensure_group("Однодневные цветные линзы", g_color)
        for nm in [
            "ADRIA WOW (30 линз) Latin (светло-карий)",
            "ADRIA WOW (30 линз) Jazz Black (черный)",
            "ADRIA WOW (30 линз) Rhapsody (темно-карий)",
            "ADRIA WOW (30 линз) Soul Brown (карий)",
            "ADRIA MIX (10 линз) Light Green (зеленый)",
            "ADRIA MIX (10 линз) Blue (голубой)",
            "ADRIA MIX (10 линз) Pearl Gray (серый)",
            "ADRIA MIX (30 линз) (3 цвета в упаковке)",
        ]:
            ensure_product(nm, g_color_daily)

    # --- Seed MKL catalog for other brands and solutions ---
    def _ensure_mkl_seed_brands(self):
        """
        Seed additional MKL brands: Acuvue (Johnson & Johnson), Alcon, Bausch+Lomb,
        and utility groups: Растворы, Капли.
        Idempotent: checks for top-level group presence before seeding.
        """
        def ensure_group(name: str, parent_id: int | None) -> int:
            r = self.conn.execute(
                "SELECT id FROM product_groups_mkl WHERE name=? AND (parent_id IS ? OR parent_id = ?);",
                (name, None if parent_id is None else parent_id, parent_id),
            ).fetchone()
            if r:
                return r["id"]
            return self.add_product_group_mkl(name, parent_id)

        def ensure_product(name: str, gid: int):
            r = self.conn.execute(
                "SELECT id FROM products_mkl WHERE name=? AND group_id=?;",
                (name, gid),
            ).fetchone()
            if r:
                return r["id"]
            return self.add_product_mkl(name, gid)

        # Acuvue (Johnson & Johnson)
        acuvue_row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Acuvue (Johnson & Johnson)",),
        ).fetchone()
        if not acuvue_row:
            acuvue = ensure_group("Acuvue (Johnson & Johnson)", None)
            g_daily = ensure_group("Однодневные линзы", acuvue)
            for nm in [
                "1-DAY Acuvue MOIST 30pk 8.5 BC",
                "1-DAY Acuvue MOIST 30pk 9.0 BC",
                "1-DAY Acuvue MOIST 90pk 8.5 BC",
                "1-DAY Acuvue MOIST 90pk 9.0 BC",
                "1-DAY Acuvue MOIST 180pk 8.5 BC",
                "1-DAY Acuvue MOIST 180pk 9.0 BC",
                "1-Day Acuvue Oasys With Hydraluxe 30pk 8.5 BC",
                "1-Day Acuvue Oasys With Hydraluxe 30pk 9.0 BC",
                "1-Day Acuvue Oasys With Hydraluxe 90pk 8.5 BC",
                "1-Day Acuvue Oasys With Hydraluxe 90pk 9.0 BC",
                "1-Day Acuvue Oasys With Hydraluxe 180pk 8.5 BC",
                "1-Day Acuvue Oasys With Hydraluxe 180pk 9.0 BC",
                "ACUVUE OASYS MAX 1-Day 30pk 8.5 BC",
                "ACUVUE OASYS MAX 1-Day 30pk 9.0 BC",
            ]:
                ensure_product(nm, g_daily)
            g_biweek = ensure_group("Двухнедельные линзы", acuvue)
            for nm in [
                "Acuvue 2 6pk 8.3 BC",
                "Acuvue 2 6pk 8.7 BC",
                "Acuvue Oasys 6pk 8.4 BC",
                "Acuvue Oasys 6pk 8.8 BC",
                "Acuvue Oasys 12pk 8.4 BC",
                "Acuvue Oasys 12pk 8.8 BC",
                "Acuvue Oasys 24pk 8.4 BC",
                "Acuvue Oasys 24pk 8.8 BC",
            ]:
                ensure_product(nm, g_biweek)
            g_biweek_mf = ensure_group("Двухнедельные линзы мультифокальные", acuvue)
            for nm in [
                "Acuvue Oasys for ASTIGMATISM 6pk 8.6 BC",
                "1-DAY Acuvue MOIST for ASTIGMATISM 30pk 8.5 BC",
                "1-DAY Acuvue MOIST for ASTIGMATISM 90pk 8.5 BC",
                "1-DAY Acuvue Oasys With Hydraluxe for ASTIGMATISM 30pk 8.5 BC",
                "1-DAY Acuvue MOIST Multifocal 30pk 8.4 BC",
            ]:
                ensure_product(nm, g_biweek_mf)

        # Alcon
        alcon_row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Alcon",),
        ).fetchone()
        if not alcon_row:
            alcon = ensure_group("Alcon", None)
            g_daily = ensure_group("Однодневные линзы", alcon)
            for nm in [
                "Dailies Total 1 30pk 8.6 BC",
                "Dailies Total 1 90pk 8.6 BC",
                "Precision 1 30pk 8.3 BC",
                "Precision 1 90pk 8.3 BC",
                "Dailies Aqua Comfort Plus 30pk 8.7 BC",
                "Dailies Aqua Comfort Plus 30pk 8.9 BC",
            ]:
                ensure_product(nm, g_daily)
            g_monthly = ensure_group("Ежемесячные линзы", alcon)
            for nm in [
                "AIR Optix Aqua 3pk 8.6 BC",
                "AIR Optix Aqua 6pk 8.6 BC",
                "AIR Optix Night&Day AQUA 3pk 8.4 BC",
                "AIR Optix Night&Day AQUA 3pk 8.6 BC",
                "Air Optix Plus HydraGlyde 3pk 8.6 BC",
                "Air Optix Plus HydraGlyde 6pk 8.6 BC",
                "Total 30 3pk 8.6 BC",
            ]:
                ensure_product(nm, g_monthly)
            g_mf = ensure_group("Линзы мультифакальные", alcon)
            for nm in [
                "Air Optix Plus Hydraglyde For Astigmatism 3pk 8.7 BC",
                "Air Optix Plus Hydraglyde For Astigmatism 6pk 8.7 BC",
                "Air Optix Plus Hydraglyde For Astigmatism 9pk 8.7 BC",
                "AIR OPTIX plus HydraGlyde Multifocal 3pk 8.6 BC",
                "Dailies Total 1 Multifocal 30pk 8.5 BC",
                "Total 30 for Astigmatism 3pk 8.4 BC",
            ]:
                ensure_product(nm, g_mf)

        # Bausch+Lomb
        bl_row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Bausch+Lomb",),
        ).fetchone()
        if not bl_row:
            bl = ensure_group("Bausch+Lomb", None)
            g_monthly = ensure_group("Ежемесячные линзы", bl)
            for nm in [
                "SofLens 59 6pk 8.6 BC",
                "PureVision 2 6pk 8.6 BC",
            ]:
                ensure_product(nm, g_monthly)
            g_quarterly = ensure_group("Квартальные линзы", bl)
            for nm in [
                "Optima FW 4pk 8.4 BC",
                "Optima FW 4pk 8.7 BC",
            ]:
                ensure_product(nm, g_quarterly)

        # Растворы
        sol_row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Растворы",),
        ).fetchone()
        if not sol_row:
            solutions = ensure_group("Растворы", None)
            # Adria subgroup under solutions
            s_adria = ensure_group("Adria", solutions)
            for nm in [
                "ADRIA CITY Moist 360ml",
                "ADRIA (DENIQ HIGH FRESH YAL) 360ml",
                "ADRIA Plus 60ml",
                "ADRIA Plus 250ml",
            ]:
                ensure_product(nm, s_adria)
            # Renu MPS
            s_renu_mps = ensure_group("Renu MPS", solutions)
            for nm in [
                "Renu MPS 120ml",
                "Renu MPS 240ml",
                "Renu MPS 360ml",
            ]:
                ensure_product(nm, s_renu_mps)
            # Renu MultiPlus
            s_renu_multi = ensure_group("Renu MultiPlus", solutions)
            for nm in [
                "Renu MultiPlus 60ml",
                "Renu MultiPlus 120ml",
                "Renu MultiPlus 240ml",
                "Renu MultiPlus 360ml",
            ]:
                ensure_product(nm, s_renu_multi)
            # Renu Advanced
            s_renu_adv = ensure_group("Renu Advanced", solutions)
            for nm in [
                "Renu Advanced 100ml",
                "Renu Advanced 360ml",
            ]:
                ensure_product(nm, s_renu_adv)
            # Acuvue
            s_acuvue = ensure_group("Acuvue", solutions)
            for nm in [
                "Acuvue 100ml",
                "Acuvue 300ml",
                "Acuvue 360ml",
            ]:
                ensure_product(nm, s_acuvue)
            # Ликонтин
            s_likon = ensure_group("Ликонтин", solutions)
            for nm in [
                "Ликонтин-Универсал 120ml",
                "Ликонтин-Универсал 240ml",
            ]:
                ensure_product(nm, s_likon)
            # OPTIMED
            s_optimed = ensure_group("OPTIMED", solutions)
            for nm in [
                "OPTIMED Про Актив 125ml",
                "OPTIMED Про Актив 125ml",
            ]:
                ensure_product(nm, s_optimed)
            # Products directly under solutions
            for nm in [
                "AOSEPT Plus HydraGlyde 360ml",
                "OptiFree Express 355ml",
                "Энзимный очиститель \"OPTIMED\" 3ml",
                "Ликонтин 5ml  (раствор для энзимной очистки)",
                "Avizor Таблетки 10 шт.",
            ]:
                ensure_product(nm, solutions)

        # Капли (top-level group with products)
        drops_row = self.conn.execute(
            "SELECT id FROM product_groups_mkl WHERE name=? AND parent_id IS NULL;",
            ("Капли",),
        ).fetchone()
        if not drops_row:
            drops = ensure_group("Капли", None)
            for nm in [
                "ADRIA Relax 10ml",
                "OPTIMED Про Актив 10ml",
                "Avizor Comfort Drops 15ml",
                "Avizor Moisture Drops 15ml",
                "Опти-Фри 15ml",
                "Ликонтин - Комфорт 18ml",
            ]:
                ensure_product(nm, drops)

    # --- Mirror MKL catalog into Meridian under "Контактные Линзы" (bottom group) ---
    def _ensure_meridian_contacts_from_mkl(self):
        """
        Create top-level group 'Контактные Линзы' in Meridian catalog and
        mirror the entire MKL groups/products structure under it.
        Idempotent: if the group already exists, do nothing.
        """
        # Check existing top-level group
        row = self.conn.execute(
            "SELECT id FROM product_groups_meridian WHERE name=? AND parent_id IS NULL;",
            ("Контактные Линзы",),
        ).fetchone()
        if row:
            return

        # Create bottom group by using next sort value on top-level
        contacts_gid = self.add_product_group_meridian("Контактные Линзы", None)

        # Build MKL group tree
        mkl_groups = self.list_product_groups_mkl()
        children_map: dict[int | None, list[dict]] = {}
        by_id: dict[int, dict] = {}
        for g in mkl_groups:
            by_id[g["id"]] = g
            children_map.setdefault(g["parent_id"], []).append(g)
        # Sort children by sort_order then name
        for k in list(children_map.keys()):
            children_map[k].sort(key=lambda x: (x.get("sort_order", 0), (x.get("name", "") or "").lower()))

        def copy_group_tree(mkl_group: dict, meridian_parent_id: int):
            # Create meridian group
            new_gid = self.add_product_group_meridian(mkl_group["name"], meridian_parent_id)
            # Copy products from this group
            try:
                prods = self.list_products_mkl_by_group(mkl_group["id"])
            except Exception:
                prods = []
            for p in prods:
                self.add_product_meridian(p["name"], new_gid)
            # Recurse children
            for child in children_map.get(mkl_group["id"], []):
                copy_group_tree(child, new_gid)

        # Copy all top-level MKL groups under contacts_gid
        for top in children_map.get(None, []):
            copy_group_tree(top, contacts_gid)

        # Handle MKL products without a group (group_id IS NULL) by creating "Без группы"
        try:
            ungroupped = [p for p in self.list_products_mkl() if p.get("group_id") is None]
        except Exception:
            ungroupped = []
        if ungroupped:
            gid_misc = self.add_product_group_meridian("Без группы", contacts_gid)
            for p in ungroupped:
                self.add_product_meridian(p["name"], gid_misc)

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
            "SELECT id, order_id, product, sph, cyl, ax, \"add\", d, qty FROM meridian_items WHERE order_id=? ORDER BY id ASC;",
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
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, "add", d, qty)
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
                INSERT INTO meridian_items (order_id, product, sph, cyl, ax, "add", d, qty)
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