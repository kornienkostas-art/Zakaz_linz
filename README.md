# УссурОЧки.рф — десктоп-приложение (Python + PyQt6)

Запуск на Windows:

1) Установите Python 3.10+ и добавьте его в PATH.
2) Откройте папку проекта, убедитесь, что внутри есть:
   - папка `ussurochki_app` со файлами:
     - `__init__.py`
     - `main.py`
     - `db.py`
     - `mkl.py`
     - `meridian.py`
     - `settings.py`
     - `theme.py`
     - `validators.py`
   - файл `requirements.txt`
   - файл `run_windows.bat`

3) Запустите `run_windows.bat` (двойным кликом или через CMD/PowerShell).
   - Скрипт создаст виртуальное окружение `.venv`, установит зависимости и запустит приложение.

Альтернативный запуск вручную:

- Установка зависимости:
  - `py -m pip install PyQt6`

- Запуск как пакет:
  - из корня проекта: `python -m ussurochki_app.main`

- Запуск напрямую:
  - перейдите в папку `ussurochki_app` и выполните: `python main.py`

Примечания:

- База данных создаётся автоматически в `ussurochki_app/data/ussurochki.sqlite`. Если раньше у вас был файл `usurochki.sqlite` (с одной S), он будет автоматически переименован при запуске.
- Настройки сохраняются в `ussurochki_app/data/settings.json`.
- Формат телефона: `+7-XXX-XXX-XX-XX` или `8-XXX-XXX-XX-XX` (в форме клиента применяется маска ввода).
- Экспорт TXT-файлов выбирается в разделах «Заказы МКЛ» и «Заказы Меридиан» через соответствующие кнопки.

Типичные проблемы и решения:

- `ModuleNotFoundError: No module named 'PyQt6'`
  - Установите библиотеку: `py -m pip install PyQt6` (или через `run_windows.bat`).

- `ImportError: attempted relative import with no known parent package`
  - Запускайте как пакет: `python -m ussurochki_app.main`, либо запускайте `python main.py` из папки `ussurochki_app`.
  - В файлах `main.py`, `mkl.py`, `meridian.py` добавлены безопасные импорты, поддерживающие оба варианта.

Связь:
- Если нужна сборка `exe` (PyInstaller) или дополнительный UI/UX (иконки, анимации, углублённые стили), дайте знать — добавлю.