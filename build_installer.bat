@echo off
setlocal EnableDelayedExpansion

REM Build installer for UssurochkiRF using Inno Setup (ISCC).
REM Prerequisites:
REM   1) Python + PyInstaller to produce the app binaries (use build_exe.bat / build_exe_onefile.bat)
REM   2) Inno Setup installed (ISCC.exe available) — https://jrsoftware.org/isdl.php

set "APP_NAME=UssurochkiRF"
set "DIST_DIR_FOLDER=dist\%APP_NAME%"
set "DIST_ONEFILE=dist\%APP_NAME%.exe"
set "ISS_FILE_FOLDER=installer\%APP_NAME%.iss"
set "ISS_FILE_ONEFILE=installer\%APP_NAME%_onefile.iss"

REM 0) Build the application binaries first (prefer spec-based build)
if exist build_exe.bat (
  call build_exe.bat
) else (
  echo [WARN] build_exe.bat not found. Trying one-file build...
  if exist build_exe_onefile.bat (
    call build_exe_onefile.bat
  )
)

REM 1) Determine which build output exists
set "ISS_FILE="
if exist "%DIST_DIR_FOLDER%" (
  set "ISS_FILE=%ISS_FILE_FOLDER%"
  echo Using folder build: "%DIST_DIR_FOLDER%"
) else if exist "%DIST_ONEFILE%" (
  set "ISS_FILE=%ISS_FILE_ONEFILE%"
  echo Using one-file build: "%DIST_ONEFILE%"
) else (
  echo [ERROR] Build output not found: "%DIST_DIR_FOLDER%" or "%DIST_ONEFILE%"
  echo Make sure the build step completed successfully.
  pause
  exit /b 1
)

REM 2) Locate Inno Setup compiler (ISCC.exe)
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

REM 3) Compile installer script (folder vs onefile)
if not exist "%ISS_FILE%" (
  echo [ERROR] Installer script not found: "%ISS_FILE%"
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
echo Check: installer\Output\%APP_NAME%*.exe
echo.
pause

endlocal