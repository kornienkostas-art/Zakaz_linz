import os
import shutil
import sqlite3
from datetime import datetime

# Use the same storage resolution as the app so we hit the correct data.db
def _get_storage_dir() -> str:
    try:
        import sys
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()

STORAGE_DIR = _get_storage_dir()
DB_PATH = os.path.join(STORAGE_DIR, "data.db")

def backup_db(path: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(STORAGE_DIR, f"data.db.bak_{ts}")
    shutil.copy2(path, dst)
    return dst

def purge():
    if not os.path.isfile(DB_PATH):
        print(f"База данных не найдена: {DB_PATH}")
        return

    bak = backup_db(DB_PATH)
    print(f"Сделан резервный файл: {bak}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Clear orders (MKL + Meridian)
    try:
        cur.execute("DELETE FROM meridian_items;")
    except Exception:
        pass
    try:
        cur.execute("DELETE FROM meridian_orders;")
    except Exception:
        pass
    try:
        cur.execute("DELETE FROM mkl_orders;")
    except Exception:
        pass

    # Clear product catalogs (generic + MKL + Meridian)
    for sql in [
        "DELETE FROM products;",
        "DELETE FROM product_groups;",
        "DELETE FROM products_mkl;",
        "DELETE FROM product_groups_mkl;",
        "DELETE FROM products_meridian;",
        "DELETE FROM product_groups_meridian;",
    ]:
        try:
            cur.execute(sql)
        except Exception:
            pass

    conn.commit()
    try:
        conn.execute("VACUUM;")
    except Exception:
        pass
    conn.close()
    print("Очистка завершена: товары и заказы удалены.")

if __name__ == "__main__":
    purge()