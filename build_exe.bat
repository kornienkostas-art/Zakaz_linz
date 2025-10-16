@echo off
setlocal EnableDelayedExpansion

REM Build Windows EXE using PyInstaller and the existing spec file.
REM Use `python -m PyInstaller` so we don't depend on PATH shims.

REM 1) Ensure Python and pip are available
python --version >NUL 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not available in PATH.
  echo Install Python 3.10+ and try again.
  pause
  exit /b 1
)

REM 2) Upgrade pip (optional but recommended)
python -m pip install --upgrade pip

REM 3) Install build-time dependencies (PyInstaller)
python -m pip install --upgrade pyinstaller

REM 4) Install runtime dependencies (from requirements.txt)
if exist requirements.txt (
  python -m pip install -r requirements.txt
)

REM 5) Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 6) Build with spec (includes assets and icon)
python -m PyInstaller --clean --noconfirm UssurochkiRF.spec

if errorlevel 1 (
  echo.
  echo [ERROR] Build failed. See the messages above.
  pause
  exit /b 1
)

echo.
echo [OK] Build completed.
echo     EXE: dist\UssurochkiRF\UssurochkiRF.exe
echo.
echo You can copy the entire folder "dist\UssurochkiRF" to another machine and run the EXE.
echo.
pause

endlocal