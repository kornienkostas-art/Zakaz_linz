# УссурОЧки.рф — desktop-приложение (Tkinter + SQLite)

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
4. Запуск:
   ```
   python main.py
   ```

## Зависимости

- Стандартные библиотеки: tkinter, sqlite3, json, os, re, threading, datetime
- Дополнительно (по желанию):
  - pystray — системный трей (Windows/Mac/Linux)
  - Pillow — загрузка/ресайз логотипа для трея

Если pystray/Pillow не установлены, приложение запустится без трея.

## Структура проекта

- `main.py` — точка входа; инициализация настроек/БД/трея, планировщик уведомлений, запуск `MainWindow`.
- `app/`
  - `db.py` — работа с SQLite (клиенты, товары, заказы МКЛ, заказы «Меридиан» и позиции).
  - `tray.py` — системный трей, автозапуск (Windows). Автозапуск настроен на запуск `main.py` через `pythonw`.
  - `utils.py` — утилиты UI: размеры окон, центрирование, плавные переходы, формат телефона.
  - `views/` — экраны приложения:
    - `main.py` — главное меню: Заказы МКЛ, Заказы Меридиан, Настройки.
    - `orders_mkl.py` — список/редактор заказов МКЛ, экспорт TXT.
    - `orders_meridian.py` — список/редактор заказов «Меридиан», экспорт TXT.
    - `forms_mkl.py` — формы создания/редактирования МКЛ.
    - `forms_meridian.py` — формы создания/редактирования «Меридиан».
    - `settings.py` — настройки (встроенный экран, не отдельное окно).
    - `products_mkl.py`, `products_meridian.py`, `clients.py` — справочники (если нужны).
- `requirements.txt` — зависимости (pystray, Pillow).
- `settings.json` и `data.db` создаются автоматически рядом с `main.py`.

## Сборка в EXE (по желанию)

Сборка в единый exe через PyInstaller:
```
pip install pyinstaller
pyinstaller --noconsole --onefile --name UssurochkiRF main.py
```
Готовый файл будет в папке `dist/`.

## Примечания

- Настройки открываются во встроенном виде (экран `SettingsView`) и позволяют менять масштаб интерфейса, размер шрифта, папку экспорта, поведение трея и уведомлений.
- В Windows доступен автозапуск через трей-меню (HKCU\Software\Microsoft\Windows\CurrentVersion\Run).