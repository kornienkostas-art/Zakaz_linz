# УссурОЧки.рф — desktop-приложение (Tkinter + SQLite)

Проект содержит исходный код приложения. Ниже — быстрый старт.

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
3. Установите зависимости (опциональные для трея и логотипа):
   ```
   pip install -r requirements.txt
   ```
4. Запуск:
   ```
   python main.py
   ```

## Зависимости

- Стандартные библиотеки: tkinter, sqlite3, json, os, re, threading, datetime
- Опционально:
  - pystray — системный трей (Windows/Mac/Linux)
  - Pillow — загрузка/ресайз логотипа для трея

Если pystray/Pillow не установлены, приложение запустится без трея.

## Файлы

- `main.py` — основной файл приложения (содержит UI `MainWindow` и логику запуска).
- `db.py` — работа с SQLite.
- `requirements.txt` — список опциональных зависимостей.
- `.gitignore` — стандартные исключения (кэш, виртуальное окружение, сборки).
- `settings.json` и `data.db` создаются автоматически рядом с `main.py`.

## Сборка в EXE (по желанию)

Можно собрать приложение в единый exe с помощью PyInstaller:
```
pip install pyinstaller
pyinstaller --noconsole --onefile --name UssurochkiRF main.py
```
Готовый файл будет в папке `dist/`.

## Примечание

Приведено к изначальной концепции: основной интерфейс находится в `main.py` (без пакета `app/`). Далее можно расширять UI и CRUD.