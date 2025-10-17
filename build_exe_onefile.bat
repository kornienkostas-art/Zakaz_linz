@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Build a single-file Windows EXE (portable) using PyInstaller.
REM Tries Windows 'py' launcher first, then falls back to 'python'.

REM 0) Pick a Python interpreter (pref: 3.11/3.10 via py launcher)
set "PYEXE="
for %%V in (3.11 3.10 3) do (
  where py >NUL 2>&1
  if not errorlevel 1 (
    py -%%V --version >NUL 2>&1
    if not errorlevel 1 (
      set "PYEXE=py -%%V"
      goto :have_python
    )
  )
)
where python >NUL 2>&1
if not errorlevel 1 (
  python --version >NUL 2>&1
  if not errorlevel 1 (
    set "PYEXE=python"
    goto :have_python
  )
)

echo [ERROR] Python is not available.
echo Install Python 3.10+ from https://www.python.org/downloads/windows/
echo or enable the Windows 'py' launcher, then re-run this script.
pause
exit /b 1

:have_python
echo Using interpreter: %PYEXE%
echo.

REM 1) Upgrade pip (optional)
%PYEXE% -m pip install --upgrade pip

REM 2) Install PyInstaller
%PYEXE% -m pip install --upgrade pyinstaller

REM 3) Install runtime dependencies
if exist requirements.txt (
  %PYEXE% -m pip install -r requirements.txt
)

REM 4) Clean previous artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 5) Build
REM --onefile: produce a single exe
REM --windowed: no console window
REM --icon: use application icon
REM --add-data: include assets and default settings into the bundle
set ADD_DATA=--add-data "app\assets;app\assets" --add-data "settings.json;."
%PYEXE% -m PyInstaller --clean --noconfirm ^
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
echo Note: Running the one-file EXE unpacks to a temporary folder on first start.
echo.
pause

endlocal