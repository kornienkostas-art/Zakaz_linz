# УссурОЧки.рф — desktop-приложение (Tkinter + SQLite, PySide6 вариант)

Приложение для работы с заказами контактных линз (МКЛ и «Меридиан») с поддержкой трея, уведомлений и экспорта.

## Быстрый старт

1. Установите Python 3.10+ (Windows/Mac/Linux).
2. Создайте виртуальное окружение (рекомендуется):
   - Windows:
     ```
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Установите зависимости (для трея и логотипа иконки):
   ```
   pip install -r requirements.txt
   ```
4. Запуск (Tkinter-версия):
   ```
   python main.py
   ```
5. Запуск (новая PySide6-версия, светлая тема):
   ```
   python qt_main.py
   ```

## Зависимости

- Стандартные библиотеки: tkinter, sqlite3, json, os, re, threading, datetime
- Дополнительно:
  - pystray — системный трей (Windows/Mac/Linux)
  - Pillow — загрузка/ресайз логотипа для трея
  - PySide6 — новая десктоп-версия на Qt (Windows 10/11, DPI-aware)

Если pystray/Pillow не установлены, приложение запустится без трея (Tkinter). PySide6 используется только новой версией (`qt_main.py`).

## Структура проекта

- `main.py` — точка входа Tkinter; инициализация настроек/БД/трея, планировщик уведомлений, запуск `MainWindow`.
- `qt_main.py` — новая точка входа PySide6 (Qt) с каркасом главного окна, навигацией, трей-меню и автозапуском (HKCU Run).
- `app/`
  - `db.py` — работа с SQLite (клиенты, товары, заказы МКЛ, заказы «Меридиан» и позиции).
  - `tray.py` — системный трей для Tkinter, автозапуск (Windows).
  - `utils.py` — утилиты UI (Tkinter): размеры окон, центрирование, плавные переходы, формат телефона.
  - `views/` — экраны Tkinter:
    - `main.py` — главное меню: Заказы МКЛ, Заказы Меридиан, Настройки.
    - `orders_mkl.py` — список/редактор заказов МКЛ, экспорт TXT.
    - `orders_meridian.py` — список/редактор заказов «Меридиан», экспорт TXT.
    - `forms_mkl.py` — формы создания/редактирования МКЛ.
    - `forms_meridian.py` — формы создания/редактирования «Меридиан».
    - `settings.py` — настройки (встроенный экран, не отдельное окно).
    - `products_mkl.py`, `products_meridian.py`, `clients.py` — справочники (если нужны).
- `requirements.txt` — зависимости (pystray, Pillow, PySide6).
- `settings.json` и `data.db` создаются автоматически рядом с `main.py`.

## Сборка в EXE (по желанию)

Сборка в единый exe через PyInstaller:
```
pip install pyinstaller
pyinstaller --noconsole --onefile --name UssurochkiRF main.py
```
Для Qt-версии:
```
pyinstaller --noconsole --onefile --name UssurochkiRF_qt qt_main.py
```
Готовые файлы будут в папке `dist/`.

## Примечания

- Настройки (settings.json) используются обеими версиями. По умолчанию для Qt-версии:
  - Тема: светлая
  - Масштаб: 100%
  - Шрифт: Segoe UI, 12pt
  - Папка экспорта: Рабочий стол
  - Трей: включён, сворачивание в трей
  - Автозапуск: включён
- В Windows доступен автозапуск через трей-меню (HKCU\Software\Microsoft\Windows\CurrentVersion\Run).