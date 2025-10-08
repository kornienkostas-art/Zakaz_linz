from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class OrderStatus(IntEnum):
    NOT_ORDERED = 0
    ORDERED = 1
    CALLED = 2
    DELIVERED = 3

    @classmethod
    def from_text(cls, text: str) -> "OrderStatus":
        mapping = {
            "Не заказан": cls.NOT_ORDERED,
            "Заказан": cls.ORDERED,
            "Прозвонен": cls.CALLED,
            "Вручен": cls.DELIVERED,
        }
        return mapping[text]

    def to_text(self) -> str:
        mapping = {
            OrderStatus.NOT_ORDERED: "Не заказан",
            OrderStatus.ORDERED: "Заказан",
            OrderStatus.CALLED: "Прозвонен",
            OrderStatus.DELIVERED: "Вручен",
        }
        return mapping[self]

    def file_token(self) -> str:
        mapping = {
            OrderStatus.NOT_ORDERED: "notordered",
            OrderStatus.ORDERED: "ordered",
            OrderStatus.CALLED: "called",
            OrderStatus.DELIVERED: "delivered",
        }
        return mapping[self]

    def color_hex(self) -> str:
        mapping = {
            OrderStatus.NOT_ORDERED: "#EF5350",
            OrderStatus.ORDERED: "#43A047",
            OrderStatus.CALLED: "#FFA726",
            OrderStatus.DELIVERED: "#66BB6A",
        }
        return mapping[self]


@dataclass
class Client:
    id: int
    name: str
    phone: Optional[str]


@dataclass
class ProductMKL:
    id: int
    name: str


@dataclass
class ProductMeridian:
    id: int
    name: str


@dataclass
class OrderMKL:
    id: int
    client_id: int
    status: OrderStatus
    created_at: str


@dataclass
class OrderMeridian:
    id: int
    order_number: str
    status: OrderStatus
    created_at: str


@dataclass
class ItemMKL:
    id: int
    order_id: int
    product_id: int
    eye: str  # 'OD' or 'OS'
    sph: float
    cyl: Optional[float]
    ax: Optional[int]
    bc: Optional[float]
    quantity: int


@dataclass
class ItemMeridian:
    id: int
    order_id: int
    product_id: int
    eye: str
    sph: float
    cyl: Optional[float]
    ax: Optional[int]
    d: Optional[int]
    quantity: int