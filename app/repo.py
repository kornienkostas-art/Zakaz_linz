import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .models import OrderStatus


def normalize_phone(phone: str) -> Optional[str]:
    s = (phone or "").strip()
    if not s:
        return None
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+7" + digits[1:]
    if s.startswith("+7") and len(digits) == 11:
        return "+7" + digits[1:]
    return None


def ensure_client(conn: sqlite3.Connection, name: str, phone_raw: Optional[str]) -> int:
    phone = normalize_phone(phone_raw) if phone_raw else None
    cur = conn.execute("SELECT id FROM clients WHERE name=? AND phone IS ?", (name, phone))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    conn.execute("INSERT INTO clients(name, phone) VALUES(?, ?);", (name, phone))
    return conn.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]


def list_orders_mkl(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT o.id, c.name AS client, c.phone AS phone, o.status, o.created_at,
               (SELECT COUNT(*) FROM items_mkl im WHERE im.order_id=o.id) AS positions
        FROM orders_mkl o
        JOIN clients c ON c.id=o.client_id
        ORDER BY o.id DESC;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_orders_meridian(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT o.id, o.order_number AS number, o.status, o.created_at,
               (SELECT COUNT(*) FROM items_meridian im WHERE im.order_id=o.id) AS positions
        FROM orders_meridian o
        ORDER BY o.id DESC;
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_order_mkl(conn: sqlite3.Connection, order_id: int) -> Dict[str, Any]:
    o = conn.execute(
        "SELECT o.id, o.client_id, c.name AS client_name, c.phone AS client_phone, o.status, o.created_at "
        "FROM orders_mkl o JOIN clients c ON c.id=o.client_id WHERE o.id=?;",
        (order_id,),
    ).fetchone()
    if not o:
        raise KeyError(order_id)
    items = conn.execute(
        "SELECT i.id, i.product_id, p.name AS product_name, i.eye, i.sph, i.cyl, i.ax, i.bc, i.quantity "
        "FROM items_mkl i JOIN products_mkl p ON p.id=i.product_id WHERE i.order_id=? ORDER BY i.id;",
        (order_id,),
    ).fetchall()
    return {
        "order": dict(o),
        "items": [dict(row) for row in items],
    }


def get_order_meridian(conn: sqlite3.Connection, order_id: int) -> Dict[str, Any]:
    o = conn.execute(
        "SELECT id, order_number, status, created_at FROM orders_meridian WHERE id=?;",
        (order_id,),
    ).fetchone()
    if not o:
        raise KeyError(order_id)
    items = conn.execute(
        "SELECT i.id, i.product_id, p.name AS product_name, i.eye, i.sph, i.cyl, i.ax, i.d, i.quantity "
        "FROM items_meridian i JOIN products_meridian p ON p.id=i.product_id WHERE i.order_id=? ORDER BY i.id;",
        (order_id,),
    ).fetchall()
    return {
        "order": dict(o),
        "items": [dict(row) for row in items],
    }


def save_order_mkl(
    conn: sqlite3.Connection,
    order_id: Optional[int],
    client_name: str,
    client_phone_raw: Optional[str],
    status: OrderStatus,
    items: List[Dict[str, Any]],
) -> int:
    client_id = ensure_client(conn, client_name, client_phone_raw)
    now = datetime.now().strftime("%Y-%m-%d")
    if order_id is None:
        conn.execute(
            "INSERT INTO orders_mkl(client_id, status, created_at) VALUES(?, ?, ?);",
            (client_id, int(status), now),
        )
        order_id = conn.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
    else:
        conn.execute(
            "UPDATE orders_mkl SET client_id=?, status=? WHERE id=?;",
            (client_id, int(status), order_id),
        )
        conn.execute("DELETE FROM items_mkl WHERE order_id=?;", (order_id,))
    for it in items:
        conn.execute(
            "INSERT INTO items_mkl(order_id, product_id, eye, sph, cyl, ax, bc, quantity) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?);",
            (
                order_id,
                int(it["product_id"]),
                it["eye"],
                float(it["sph"]),
                it.get("cyl"),
                it.get("ax"),
                it.get("bc"),
                int(it["quantity"]),
            ),
        )
    conn.commit()
    return int(order_id)


def save_order_meridian(
    conn: sqlite3.Connection,
    order_id: Optional[int],
    order_number: str,
    status: OrderStatus,
    items: List[Dict[str, Any]],
) -> int:
    now = datetime.now().strftime("%Y-%m-%d")
    if order_id is None:
        conn.execute(
            "INSERT INTO orders_meridian(order_number, status, created_at) VALUES(?, ?, ?);",
            (order_number, int(status), now),
        )
        order_id = conn.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]
    else:
        conn.execute(
            "UPDATE orders_meridian SET order_number=?, status=? WHERE id=?;",
            (order_number, int(status), order_id),
        )
        conn.execute("DELETE FROM items_meridian WHERE order_id=?;", (order_id,))
    for it in items:
        conn.execute(
            "INSERT INTO items_meridian(order_id, product_id, eye, sph, cyl, ax, d, quantity) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?);",
            (
                order_id,
                int(it["product_id"]),
                it["eye"],
                float(it["sph"]),
                it.get("cyl"),
                it.get("ax"),
                it.get("d"),
                int(it["quantity"]),
            ),
        )
    conn.commit()
    return int(order_id)


def duplicate_order_mkl(conn: sqlite3.Connection, order_id: int) -> int:
    data = get_order_mkl(conn, order_id)
    o = data["order"]
    items = data["items"]
    new_id = save_order_mkl(
        conn,
        None,
        o["client_name"],
        o["client_phone"],
        OrderStatus(int(o["status"])),
        [
            {
                "product_id": it["product_id"],
                "eye": it["eye"],
                "sph": it["sph"],
                "cyl": it["cyl"],
                "ax": it["ax"],
                "bc": it["bc"],
                "quantity": it["quantity"],
            }
            for it in items
        ],
    )
    return new_id


def duplicate_order_meridian(conn: sqlite3.Connection, order_id: int) -> int:
    data = get_order_meridian(conn, order_id)
    o = data["order"]
    items = data["items"]
    new_id = save_order_meridian(
        conn,
        None,
        o["order_number"],
        OrderStatus(int(o["status"])),
        [
            {
                "product_id": it["product_id"],
                "eye": it["eye"],
                "sph": it["sph"],
                "cyl": it["cyl"],
                "ax": it["ax"],
                "d": it["d"],
                "quantity": it["quantity"],
            }
            for it in items
        ],
    )
    return new_id


def delete_order_mkl(conn: sqlite3.Connection, order_id: int) -> None:
    conn.execute("DELETE FROM orders_mkl WHERE id=?;", (order_id,))
    conn.commit()


def delete_order_meridian(conn: sqlite3.Connection, order_id: int) -> None:
    conn.execute("DELETE FROM orders_meridian WHERE id=?;", (order_id,))
    conn.commit()


def update_status_mkl(conn: sqlite3.Connection, order_id: int, status: OrderStatus) -> None:
    conn.execute("UPDATE orders_mkl SET status=? WHERE id=?;", (int(status), order_id))
    conn.commit()


def update_status_meridian(conn: sqlite3.Connection, order_id: int, status: OrderStatus) -> None:
    conn.execute("UPDATE orders_meridian SET status=? WHERE id=?;", (int(status), order_id))
    conn.commit()


def list_products_mkl(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT id, name FROM products_mkl ORDER BY name;").fetchall()]


def list_products_meridian(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT id, name FROM products_meridian ORDER BY name;").fetchall()]


def add_product_mkl(conn: sqlite3.Connection, name: str) -> int:
    conn.execute("INSERT INTO products_mkl(name) VALUES(?);", (name,))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]


def add_product_meridian(conn: sqlite3.Connection, name: str) -> int:
    conn.execute("INSERT INTO products_meridian(name) VALUES(?);", (name,))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid() AS id;").fetchone()["id"]


def remove_product_mkl(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM products_mkl WHERE id=?;", (product_id,))
    conn.commit()


def remove_product_meridian(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM products_meridian WHERE id=?;", (product_id,))
    conn.commit()


def _format_value(val: Optional[float], decimals: int) -> Optional[str]:
    if val is None:
        return None
    return f"{val:.{decimals}f}"


def _sort_key_mkl(spec: Dict[str, Any], include_eye: bool) -> Tuple:
    return (
        spec.get("sph_sort", 0.0),
        spec.get("cyl_sort", float("inf")),
        spec.get("ax_sort", float("inf")),
        spec.get("bc_sort", float("inf")),
        spec.get("eye", "") if include_eye else "",
    )


def _sort_key_meridian(spec: Dict[str, Any], include_eye: bool) -> Tuple:
    return (
        spec.get("d_sort", float("inf")),
        spec.get("sph_sort", 0.0),
        spec.get("cyl_sort", float("inf")),
        spec.get("ax_sort", float("inf")),
        spec.get("eye", "") if include_eye else "",
    )


def _round_step(value: Optional[float], step: float) -> Optional[float]:
    if value is None:
        return None
    return round(round(value / step) * step, 2)


def export_mkl_by_product(conn: sqlite3.Connection, status: OrderStatus, settings: Dict[str, Any]) -> str:
    rows = conn.execute(
        """
        SELECT p.name AS product_name, i.eye, i.sph, i.cyl, i.ax, i.bc, i.quantity
        FROM orders_mkl o
        JOIN items_mkl i ON i.order_id=o.id
        JOIN products_mkl p ON p.id=i.product_id
        WHERE o.status=?
        ORDER BY p.name;
        """,
        (int(status),),
    ).fetchall()

    by_product: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        prod = row["product_name"]
        sph = float(row["sph"])
        cyl = row["cyl"]
        ax = row["ax"]
        bc = row["bc"]
        qty = int(row["quantity"])
        eye = row["eye"]

        # normalize values to steps
        sph = _round_step(sph, 0.25)
        cyl = _round_step(cyl, 0.25) if cyl is not None else None
        bc = _round_step(bc, 0.1) if bc is not None else None

        spec = {
            "eye": eye,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "bc": bc,
            "quantity": qty,
            # sort helpers
            "sph_sort": sph,
            "cyl_sort": cyl if cyl is not None else float("inf"),
            "ax_sort": ax if ax is not None else float("inf"),
            "bc_sort": bc if bc is not None else float("inf"),
        }
        by_product.setdefault(prod, []).append(spec)

    include_eye = bool(settings.get("show_eye", True))
    show_bc_mkl = bool(settings.get("show_bc_mkl", True))
    aggregate = bool(settings.get("aggregate_specs", True))

    lines: List[str] = []
    for product_name in sorted(by_product.keys(), key=lambda s: s.lower()):
        lines.append(product_name)
        specs = by_product[product_name]

        if aggregate:
            aggregated: Dict[Tuple, Dict[str, Any]] = {}
            for s in specs:
                key = (
                    s["sph"],
                    s["cyl"],
                    s["ax"],
                    s["bc"] if show_bc_mkl else None,
                    s["eye"] if include_eye else None,
                )
                if key not in aggregated:
                    aggregated[key] = dict(s)
                else:
                    aggregated[key]["quantity"] += s["quantity"]
            specs = list(aggregated.values())

        specs.sort(key=lambda x: _sort_key_mkl(x, include_eye))

        for s in specs:
            parts = [
                f"Sph: {_format_value(s['sph'], 2)}",
            ]
            if s["cyl"] is not None:
                parts.append(f"Cyl: {_format_value(s['cyl'], 2)}")
            if s["ax"] is not None and s["cyl"] is not None:
                parts.append(f"Ax: {int(s['ax'])}")
            if show_bc_mkl and s["bc"] is not None:
                parts.append(f"BC: {_format_value(s['bc'], 1)}")
            if include_eye and s["eye"]:
                parts.append(f"Глаз: {s['eye']}")
            parts.append(f"Количество: {int(s['quantity'])}")
            lines.append(" ".join(parts))
        lines.append("")  # blank line between products

    date_str = datetime.now().strftime("%Y%m%d")
    folder = settings.get("export_folder") or os.path.join(os.getcwd(), "exports")
    os.makedirs(folder, exist_ok=True)
    filename = f"mkl_{OrderStatus(status).file_token()}_{date_str}by-product.txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines).strip() + "\n")
    return path


def export_meridian_notordered(conn: sqlite3.Connection, settings: Dict[str, Any]) -> str:
    rows = conn.execute(
        """
        SELECT p.name AS product_name, i.eye, i.sph, i.cyl, i.ax, i.d, i.quantity
        FROM orders_meridian o
        JOIN items_meridian i ON i.order_id=o.id
        JOIN products_meridian p ON p.id=i.product_id
        WHERE o.status=?
        ORDER BY p.name;
        """,
        (int(OrderStatus.NOT_ORDERED),),
    ).fetchall()

    by_product: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        prod = row["product_name"]
        sph = float(row["sph"])
        cyl = row["cyl"]
        ax = row["ax"]
        d = row["d"]
        qty = int(row["quantity"])
        eye = row["eye"]

        sph = _round_step(sph, 0.25)
        cyl = _round_step(cyl, 0.25) if cyl is not None else None

        spec = {
            "eye": eye,
            "sph": sph,
            "cyl": cyl,
            "ax": ax,
            "d": d,
            "quantity": qty,
            # sort helpers
            "d_sort": d if d is not None else float("inf"),
            "sph_sort": sph,
            "cyl_sort": cyl if cyl is not None else float("inf"),
            "ax_sort": ax if ax is not None else float("inf"),
        }
        by_product.setdefault(prod, []).append(spec)

    include_eye = bool(settings.get("show_eye", True))
    aggregate = bool(settings.get("aggregate_specs", True))

    lines: List[str] = []
    for product_name in sorted(by_product.keys(), key=lambda s: s.lower()):
        lines.append(product_name)
        specs = by_product[product_name]

        if aggregate:
            aggregated: Dict[Tuple, Dict[str, Any]] = {}
            for s in specs:
                key = (
                    s["d"],
                    s["sph"],
                    s["cyl"],
                    s["ax"],
                    s["eye"] if include_eye else None,
                )
                if key not in aggregated:
                    aggregated[key] = dict(s)
                else:
                    aggregated[key]["quantity"] += s["quantity"]
            specs = list(aggregated.values())

        specs.sort(key=lambda x: _sort_key_meridian(x, include_eye))

        for s in specs:
            parts = []
            if s["d"] is not None:
                parts.append(f"D: {int(s['d'])}")
            parts.append(f"Sph: {_format_value(s['sph'], 2)}")
            if s["cyl"] is not None:
                parts.append(f"Cyl: {_format_value(s['cyl'], 2)}")
            if s["ax"] is not None and s["cyl"] is not None:
                parts.append(f"Ax: {int(s['ax'])}")
            if include_eye and s["eye"]:
                parts.append(f"Глаз: {s['eye']}")
            parts.append(f"Количество: {int(s['quantity'])}")
            lines.append(" ".join(parts))
        lines.append("")

    date_str = datetime.now().strftime("%Y%m%d")
    folder = settings.get("export_folder") or os.path.join(os.getcwd(), "exports")
    os.makedirs(folder, exist_ok=True)
    filename = f"meridian_notordered{date_str}.txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines).strip() + "\n")
    return path