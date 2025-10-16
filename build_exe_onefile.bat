@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Build a single-file Windows EXE (portable) using PyInstaller.
REM Uses `python -m PyInstaller` to avoid PATH issues.

REM 1) Ensure Python is available
python --version >NUL 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not available in PATH.
  echo Install Python 3.10+ and try again.
  pause
  exit /b 1
)

REM 2) Upgrade pip (optional)
python -m pip install --upgrade pip

REM 3) Install PyInstaller
python -m pip install --upgrade pyinstaller

REM 4) Install runtime dependencies
if exist requirements.txt (
  python -m pip install -r requirements.txt
)

REM 5) Clean previous artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 6) Build
REM --onefile: produce a single exe
REM --windowed: no console window
REM --icon: use application icon
REM --add-data: include assets and default settings into the bundle
set ADD_DATA=--add-data "app\assets;app\assets" --add-data "settings.json;."
python -m PyInstaller --clean --noconfirm ^
  --onefile ^
  --windowed ^
  --name "UssurochkiRF" ^
  --icon "app\assets\favicon.ico" ^
  %ADD_DATA% ^
  main.py

if errorlevel 1 (
  echo.
  echo [ERROR] Build failed. See the messages above.
  pause
  exit /b 1
)

echo.
echo [OK] One-file build completed.
echo     EXE: dist\UssurochkiRF.exe
echo.
echo Note: When running the one-file EXE, it will unpack to a temp folder on first start.
echo.
pause

endlocal