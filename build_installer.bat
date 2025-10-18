@echo off
setlocal EnableDelayedExpansion

REM Build installer for UssurochkiRF using Inno Setup (ISCC).
REM Prerequisites:
REM   1) Python + PyInstaller to produce the app binaries (use build_exe.bat)
REM   2) Inno Setup installed (ISCC.exe available) — https://jrsoftware.org/isdl.php

set "APP_NAME=UssurochkiRF"
set "DIST_DIR=dist\%APP_NAME%"
set "ISS_FILE=installer\%APP_NAME%.iss"

REM 0) Build the application binaries first (spec-based build)
if exist build_exe.bat (
  call build_exe.bat
) else (
  echo [WARN] build_exe.bat not found. Trying one-file build...
  if exist build_exe_onefile.bat (
    call build_exe_onefile.bat
    REM After onefile build, adjust DIST_DIR
    set "DIST_DIR=dist"
  )
)

if not exist "%DIST_DIR%" (
  echo [ERROR] Build output not found: "%DIST_DIR%"
  echo Make sure the build step completed successfully.
  pause
  exit /b 1
)

REM 1) Locate Inno Setup compiler (ISCC.exe)
set "ISCC="
for %%P in (
  "C:\Program Files\Inno Setup 6\ISCC.exe"
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  "C:\Program Files\Inno Setup 5\ISCC.exe"
  "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) do (
  if exist %%P set "ISCC=%%P"
)

if "%ISCC%"=="" (
  where ISCC.exe >NUL 2>&1
  if not errorlevel 1 (
    for /f "tokens=*" %%i in ('where ISCC.exe') do set "ISCC=%%i"
  )
)

if "%ISCC%"=="" (
  echo [ERROR] Inno Setup ISCC.exe not found.
  echo Install Inno Setup (https://jrsoftware.org/isdl.php) and re-run this script.
  pause
  exit /b 1
)

echo Using Inno Setup: "%ISCC%"

REM 2) Compile installer script
if not exist "%ISS_FILE%" (
  echo [ERROR] Installer script not found: "%ISS_FILE%"
  echo The repository should contain installer\%APP_NAME%.iss
  pause
  exit /b 1
)

"%ISCC%" "%ISS_FILE%"
if errorlevel 1 (
  echo [ERROR] ISCC compilation failed.
  pause
  exit /b 1
)

echo.
echo [OK] Installer built successfully.
echo Check the Output folder near the .iss file (installer\Output\%APP_NAME%*.exe)
echo.
pause

endlocal