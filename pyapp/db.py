import os
from datetime import datetime, date
from peewee import (
    SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField,
    ForeignKeyField, TextField, DateField
)

APP_DIR = os.path.join(os.getcwd(), "pyapp")
DATA_DIR = os.path.join(APP_DIR, "data")
EXPORT_DIR = os.path.join(APP_DIR, "exports")
DB_PATH = os.path.join(DATA_DIR, "ussurochki.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Client(BaseModel):
    id = AutoField()
    name = CharField()
    phone = CharField(null=True)


class Product(BaseModel):
    id = AutoField()
    name = CharField()
    description = TextField(null=True)
    price = FloatField(default=0.0)


class MklOrder(BaseModel):
    id = AutoField()
    client = ForeignKeyField(Client, backref="mkl_orders", on_delete="CASCADE")
    status = CharField(default="не заказан")
    date = DateField(default=date.today)
    notes = TextField(null=True)


class MklOrderItem(BaseModel):
    id = AutoField()
    order = ForeignKeyField(MklOrder, backref="items", on_delete="CASCADE")
    product = ForeignKeyField(Product, backref="mkl_items", on_delete="CASCADE")
    qty = IntegerField(default=1)


class MeridianOrder(BaseModel):
    id = AutoField()
    status = CharField(default="не заказан")
    date = DateField(default=date.today)


class MeridianOrderItem(BaseModel):
    id = AutoField()
    order = ForeignKeyField(MeridianOrder, backref="items", on_delete="CASCADE")
    product_name = CharField()
    qty = IntegerField(default=1)


def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([Client, Product, MklOrder, MklOrderItem, MeridianOrder, MeridianOrderItem])


def export_mkl(status: str | None) -> str:
    from peewee import fn
    query = MklOrder.select(MklOrder, Client).join(Client)
    if status:
        query = query.where(MklOrder.status == status)
    lines = []
    lines.append(f"УссурОЧки.рф — Заказы МКЛ — экспорт ({status or 'все'})")
    lines.append(f"Дата выгрузки: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    for o in query.order_by(MklOrder.date.desc(), MklOrder.id.desc()):
        items = MklOrderItem.select(MklOrderItem, Product).join(Product).where(MklOrderItem.order == o)
        items_str = ", ".join([f"{it.product.name} x{it.qty}" for it in items]) or "—"
        client_part = f"{o.client.name} ({o.client.phone or '—'})"
        lines.append(f"#{o.id} | {o.date} | {client_part} | {o.status} | Товары: {items_str}")
    out_path = os.path.join(EXPORT_DIR, f"mkl_{status or 'all'}_{int(datetime.now().timestamp())}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def export_meridian(status: str | None) -> str:
    query = MeridianOrder.select()
    if status:
        query = query.where(MeridianOrder.status == status)
    lines = []
    lines.append(f"УссурОЧки.рф — Заказы Меридиан — экспорт ({status or 'все'})")
    lines.append(f"Дата выгрузки: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    for o in query.order_by(MeridianOrder.date.desc(), MeridianOrder.id.desc()):
        items = MeridianOrderItem.select().where(MeridianOrderItem.order == o)
        items_str = ", ".join([f"{it.product_name} x{it.qty}" for it in items]) or "—"
        lines.append(f"#{o.id} | {o.date} | {o.status} | Товары: {items_str}")
    out_path = os.path.join(EXPORT_DIR, f"meridian_{status or 'all'}_{int(datetime.now().timestamp())}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path