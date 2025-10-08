@echo off
setlocal

REM Создать и активировать виртуальное окружение
if not exist .venv (
    py -m venv .venv
)

call .venv\Scripts\activate

REM Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

REM Запуск приложения как пакет
python -m ussurochki_app.main

endlocal