@echo off
setlocal

REM Build Windows .exe with PyInstaller
REM Usage: double-click or run from cmd in repo root

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found in PATH.
  pause
  exit /b 1
)

echo === Creating venv (optional) ===
if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate

echo === Installing requirements ===
python -m pip install --upgrade pip
if exist requirements.txt (
  pip install -r requirements.txt
)

echo === Installing PyInstaller ===
pip install pyinstaller

echo === Building EXE ===
pyinstaller --noconsole --onefile --name UssurochkiRF main.py

echo.
echo === Done ===
echo Output: dist\UssurochkiRF.exe
pause