УссурОЧки.рф — десктоп‑приложение (Python + PySide6 + SQLite)

Требования
- Windows 10/11
- Python 3.12+ (рекомендуется 3.12 — для совместимости с PySide6)
- Установленные пакеты: PySide6, PyInstaller (для сборки .exe)

Быстрый старт (PowerShell)
1) Создать папку проекта и перейти в неё:
   mkdir C:\Projects\Ussurochki
   cd C:\Projects\Ussurochki

2) Создать виртуальное окружение:
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   Если PowerShell ругается на выполнение скриптов:
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   затем активируйте снова:
   .\.venv\Scripts\Activate.ps1

3) Установить зависимости:
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt

   ПРИМЕЧАНИЕ: если на Python 3.13 появится ошибка
   "No matching distribution found for PySide6",
   установите Python 3.12 (Windows x86-64) с https://www.python.org/downloads/windows/
   и создайте окружение под 3.12:
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt

4) Запуск приложения:
   python main.py

Структура данных и файлы
- База SQLite: %APPDATA%\Ussurochki\data\app.db
- Экспорт TXT: %APPDATA%\Ussurochki\exports\ (настраивается в «Настройках»)
- Резервные копии (ZIP): %APPDATA%\Ussurochki\backups\
- Логи (зарезервировано): %APPDATA%\Ussurochki\logs\

Функциональность
- Заказы МКЛ:
  - Клиент: ФИО (обязательно), телефон (нормализация в формат +7XXXXXXXXXX при возможности).
  - Позиции: Товар, Глаз (OD/OS), Sph (−30…+30, шаг 0.25), Cyl (опц., шаг 0.25), Ax (0…180, только при Cyl), BC (опц., 8.0…9.0, шаг 0.1), Количество (1…20).
  - Статусы: Не заказан, Заказан, Прозвонен, Вручен.
  - Экспорт: по выбранному статусу, свод по товарам.
- Заказы Меридиан:
  - Позиции: Товар, Глаз (OD/OS), Sph/Cyl/Ax (как выше), D (опц., 45…90, шаг 5), Количество (1…20).
  - Статусы: Не заказан, Заказан.
  - Экспорт: «Не заказан», свод по товарам.
- Настройки:
  - Тема (Системная/Светлая/Тёмная).
  - Папка экспорта.
  - Флажки экспорта: Показывать OD/OS; Показывать BC в МКЛ; Агрегировать одинаковые спецификации.
  - Бэкап базы (ZIP) и восстановление.

Правила экспорта
- Обозначения строго Sph, Cyl, Ax, BC, D (англ.).
- «Количество» — русским словом.
- Пустые параметры не выводятся.
- МКЛ: BC печатается только если заполнен и включён флажок в «Настройках».
- Меридиан: D печатается, если задан.
- Опция «Показывать OD/OS» — добавляет «Глаз: OD/OS».
- Агрегация (если включена): одинаковые спецификации суммируются по количеству.
- Файлы:
  - mkl_{status}_{YYYYMMDD}_by-product.txt
  - meridian_notordered_{YYYYMMDD}.txt
- Кодировка: UTF‑8 с BOM; окончание строк CRLF.

Сборка .exe (по желанию)
- Одним файлом:
  pyinstaller --name "Ussurochki" --onefile --windowed --icon=icon.ico main.py
- Одной папкой:
  pyinstaller --name "Ussurochki" --onedir --windowed --icon=icon.ico main.py

Примечания
- Приложение не использует сторонних UI‑библиотек кроме самого Qt (PySide6). Всё построено на «встроенных» возможностях Qt.
- Если потребуется импорт/экспорт в другие форматы — добавим в следующих итерациях.