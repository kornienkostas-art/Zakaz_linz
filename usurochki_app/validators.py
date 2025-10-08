import re
from typing import Optional


PHONE_RE = re.compile(r"^(\+7|8)-\d{3}-\d{3}-\d{2}-\d{2}$")


def validate_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone))


def validate_sph(value: float) -> bool:
    # -30.0 .. +30.0 шаг 0.25
    if value < -30.0 or value > 30.0:
        return False
    return ((value * 100) % 25) == 0  # кратно 0.25


def validate_cyl(value: float) -> bool:
    # -10.0 .. +10.0 шаг 0.25
    if value < -10.0 or value > 10.0:
        return False
    return ((value * 100) % 25) == 0


def validate_ax(value: int) -> bool:
    # 0 .. 180 шаг 1
    return 0 <= value <= 180


def validate_bc(value: float) -> bool:
    # 8.0 .. 9.0 шаг 0.1
    if value < 8.0 or value > 9.0:
        return False
    return ((value * 10) % 1) == 0  # кратно 0.1


def validate_qty(value: int) -> bool:
    return 1 <= value <= 20


def normalize_empty_str(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s or None