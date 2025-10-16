import os
import re
import sqlite3
import sys
from typing import Iterable, List, Tuple

"""
Импорт товаров из PDF-прайса "прайс WEIYA нал.pdf" в таблицу products.

Использование:
    python scripts/import_weiya_pdf.py
    python scripts/import_weiya_pdf.py "путь/к/прайс WEIYA нал.pdf"

Логика:
- Извлекаем текст из PDF с помощью pdfplumber.
- Для каждой строковой строки на странице берём самый левый текстовый блок (первый столбец).
- Чистим пробелы, переносы и повторяющиеся пробелы.
- Пропускаем пустые строки и строки-крошки (менее 3 символов).
- Добавляем в таблицу "products", избегая дублей по точному совпадению name.
"""

PDF_DEFAULT = "прайс WEIYA нал.pdf"
DB_PATH = os.path.join(os.getcwd(), "data.db")


def _normalize_name(s: str) -> str:
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" –—-·•\t ")
    return s.strip()


def _extract_first_column_lines(pdf_path: str) -> List[str]:
    import pdfplumber  # lazy import

    results: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Получаем слова с координатами
            words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
            # Группируем по строкам по y0/y1 с небольшим допуском
            lines: dict[Tuple[int, int], List[dict]] = {}
            for w in words:
                y_key = (int(round(w.get("top", 0))), int(round(w.get("bottom", 0))))
                lines.setdefault(y_key, []).append(w)
            # Для каждой строки выбираем самое левое слово и собираем блок вокруг него
            for y_key, ws in sorted(lines.items(), key=lambda kv: kv[0][0]):
                if not ws:
                    continue
                # Сортировка по x0
                ws_sorted = sorted(ws, key=lambda d: d.get("x0", 0.0))
                # Берём “левую группу” — слова вблизи минимального x0 (±20pt)
                left_x0 = ws_sorted[0].get("x0", 0.0)
                group = [w for w in ws_sorted if (w.get("x0", 0.0) - left_x0) <= 20.0]
                text = " ".join(w.get("text", "") for w in group)
                text = _normalize_name(text)
                if len(text) >= 3:
                    results.append(text)
    return results


def _load_existing_products(conn: sqlite3.Connection) -> set:
    rows = conn.execute("SELECT name FROM products;").fetchall()
    return {r[0] for r in rows}


def _ensure_products_table(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        """
    )
    conn.commit()


def import_pdf_to_products(pdf_path: str, db_path: str = DB_PATH) -> Tuple[int, int]:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    lines = _extract_first_column_lines(pdf_path)
    # Фильтруем очевидный мусор и заголовки
    bad_prefixes = (
        "ПРАЙС", "Прайс", "WEIYA", "WeiYa", "Тел.", "Список", "Цена", "Позиции",
        "Код", "№", "Описание", "Диаметр", "Диоптрии",
    )
    cleaned: List[str] = []
    for s in lines:
        if any(s.startswith(p) for p in bad_prefixes):
            continue
        # иногда в первом столбце попадаются номера строк — выкидываем “№ 1” и подобные
        if re.fullmatch(r"[№#]?\s*\d{1,4}", s):
            continue
        cleaned.append(s)

    added = 0
    skipped = 0
    conn = sqlite3.connect(db_path)
    try:
        _ensure_products_table(conn)
        existing = _load_existing_products(conn)
        for name in cleaned:
            if name in existing:
                skipped += 1
                continue
            # вставляем
            conn.execute("INSERT INTO products (name) VALUES (?);", (name,))
            added += 1
            existing.add(name)
        conn.commit()
    finally:
        conn.close()

    return added, skipped


def main(argv: Iterable[str] = None):
    argv = list(sys.argv[1:] if argv is None else argv)
    pdf_path = argv[0] if argv else PDF_DEFAULT
    try:
        added, skipped = import_pdf_to_products(pdf_path)
        print(f"[OK] Импорт завершён. Добавлено: {added}, пропущено (дубликаты): {skipped}")
        print(f"База: {DB_PATH}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()