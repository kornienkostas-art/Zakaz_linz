import os
import re
from datetime import datetime
from typing import List, Dict, Optional


PHONE_RE = re.compile(r"^(\+7|8)-\d{3}-\d{3}-\d{2}-\d{2}$")


def validate_phone(phone: str) -> bool:
    if not phone:
        return True  # phone is optional
    return bool(PHONE_RE.match(phone))


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def normalize_sph(value: float) -> float:
    value = clamp(value, -30.0, +30.0)
    # step 0.25
    step = 0.25
    return round(round(value / step) * step, 2)


def normalize_cyl(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    value = clamp(value, -10.0, +10.0)
    step = 0.25
    return round(round(value / step) * step, 2)


def normalize_ax(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    return int(clamp(int(value), 0, 180))


def normalize_bc(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    value = clamp(value, 8.0, 9.0)
    step = 0.1
    return round(round(value / step) * step, 1)


def normalize_qty(value: int) -> int:
    return int(clamp(int(value), 1, 20))


def ensure_export_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def export_txt(path: str, filename: str, rows: List[Dict], fields: List[str]) -> str:
    ensure_export_dir(path)
    sep = "\t"
    fname = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    full = os.path.join(path, fname)
    with open(full, "w", encoding="utf-8") as f:
        f.write(sep.join(fields) + "\n")
        for r in rows:
            line = sep.join(str(r.get(k, "")) for k in fields)
            f.write(line + "\n")
    return full