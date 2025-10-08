from typing import List, Dict
import os


def export_mkl_by_status(orders: List[Dict], status: str, filepath: str, delimiter: str = "\t") -> str:
    lines = []
    header = delimiter.join(["ФИО", "Телефон", "Товары", "Статус", "Дата"])
    lines.append(header)
    for od in orders:
        if od["status"] != status:
            continue
        items_strs = []
        for it in od["items"]:
            parts = [f"{it['product_name']}"]
            parts.append(f"SPH {it['sph']:+.2f}")
            if it.get("cyl") is not None:
                parts.append(f"CYL {it['cyl']:+.2f}")
            if it.get("ax") is not None:
                parts.append(f"AX {int(it['ax'])}")
            if it.get("bc") is not None:
                parts.append(f"BC {it['bc']:.1f}")
            parts.append(f"x{it['qty']}")
            items_strs.append(" ".join(parts))
        row = delimiter.join([
            str(od["client_name"] or ""),
            str(od["phone"] or ""),
            "; ".join(items_strs),
            str(od["status"]),
            str(od["created_at"]),
        ])
        lines.append(row)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


def export_meridian_not_ordered(orders: List[Dict], filepath: str, delimiter: str = "\t") -> str:
    lines = []
    header = delimiter.join(["Номер заказа", "Товар", "Статус"])
    lines.append(header)
    for od in orders:
        if od["status"] != "Не заказан":
            continue
        for it in od["items"]:
            parts = [f"{it['product_name']}"]
            parts.append(f"SPH {it['sph']:+.2f}")
            if it.get("cyl") is not None:
                parts.append(f"CYL {it['cyl']:+.2f}")
            if it.get("ax") is not None:
                parts.append(f"AX {int(it['ax'])}")
            parts.append(f"x{it['qty']}")
            row = delimiter.join([
                str(od["number"]),
                " ".join(parts),
                str(od["status"]),
            ])
            lines.append(row)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath