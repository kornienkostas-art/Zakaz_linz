@echo off
setlocal EnableDelayedExpansion

REM Build Windows EXE using PyInstaller and the existing spec file.
REM Prefer Windows 'py' launcher (3.11/3.10), fallback to 'python'.

REM 1) Pick Python interpreter
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

REM 2) Upgrade pip (optional but recommended)
%PYEXE% -m pip install --upgrade pip

REM 3) Install build-time dependencies (PyInstaller)
%PYEXE% -m pip install --upgrade pyinstaller

REM 4) Install runtime dependencies (from requirements.txt)
if exist requirements.txt (
  %PYEXE% -m pip install -r requirements.txt
)

REM 5) Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 6) Build with spec (includes assets and icon)
%PYEXE% -m PyInstaller --clean --noconfirm UssurochkiRF.spec

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