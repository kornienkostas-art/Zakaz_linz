@echo on
setlocal ENABLEDELAYEDEXPANSION

REM Build Windows .exe with PyInstaller
REM You can double-click this file. It will:
REM  - cd to the project root (parent of scripts)
REM  - create .venv if missing, install deps and PyInstaller
REM  - build dist\UssurochkiRF.exe

REM --- Go to repo root (parent of this script) ---
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\.."

echo Current directory: %CD%
if not exist "main.py" (
  echo ERROR: main.py not found in %CD%
  echo Please run this script from the project root or keep folder structure.
  pause
  exit /b 1
)

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
echo === Creating/Using venv ===
if not exist ".venv" (
  %PYCMD% -m venv ".venv"
)

if not exist ".venv\Scripts\activate.bat" (
  echo ERROR: venv activation script not found.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

echo === Upgrading pip ===
python -m pip install --upgrade pip

echo === Installing requirements (if any) ===
if exist requirements.txt (
  pip install -r requirements.txt
) else (
  echo No requirements.txt found, skipping.
)

echo === Installing PyInstaller ===
pip install pyinstaller

echo === Building EXE ===
REM Clean previous build artifacts to avoid stale state
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist UssurochkiRF.spec del /q UssurochkiRF.spec

python -m PyInstaller --clean --noconsole --onefile --name UssurochkiRF main.py
set "ERR=%ERRORLEVEL%"

echo.
if "%ERR%" NEQ "0" (
  echo Build failed with error code %ERR%.
  echo See the console output above for details.
  pause
  exit /b %ERR%
)

if not exist "dist\UssurochkiRF.exe" (
  echo Build finished but EXE not found at dist\UssurochkiRF.exe
  pause
  exit /b 1
)

echo === Done ===
echo Output: %CD%\dist\UssurochkiRF.exe
pause