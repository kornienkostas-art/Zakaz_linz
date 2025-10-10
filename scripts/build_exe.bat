@echo off
setlocal

REM Build Windows .exe with PyInstaller
REM Usage: double-click or run from cmd in repo root

REM --- Find Python (prefer py launcher) ---
set "PYCMD="
py -3 -V >nul 2>&1 && set "PYCMD=py -3"
if not defined PYCMD python -V >nul 2>&1 && set "PYCMD=python"

if not defined PYCMD (
  echo Python not found.
  echo 1) Install Python 3 from https://www.python.org/downloads/ and check "Add python.exe to PATH"
  echo 2) Or install Microsoft Store "Python 3.x"
  echo 3) After install, re-run this script.
  pause
  exit /b 1
)

echo Using: %PYCMD%
echo === Creating venv (optional) ===
if not exist .venv (
  %PYCMD% -m venv .venv
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