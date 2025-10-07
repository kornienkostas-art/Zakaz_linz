import csv
from typing import Iterable, List
from pathlib import Path

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None  # type: ignore


def export_txt(path: str, rows: Iterable[List[str]], sep: str = "|") -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(sep.join(row) + "\n")


def export_csv(path: str, rows: Iterable[List[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def export_xlsx(path: str, rows: Iterable[List[str]]) -> None:
    if Workbook is None:
        raise RuntimeError("openpyxl is not installed. Please install it to export XLSX.")
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    # Ensure the directory exists
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)