# PowerShell script to build OrdersApp and create an installer on Windows
# Usage: Right-click this file and "Run with PowerShell" (or run from PowerShell):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\build\build_windows.ps1

$ErrorActionPreference = "Stop"

# 1) Create venv if missing
if (!(Test-Path ".venv")) {
    python -m venv .venv
}
# 2) Activate venv
$venvActivate = ".\.venv\Scripts\Activate.ps1"
if (!(Test-Path $venvActivate)) {
    Write-Error "Virtual environment activation script not found at $venvActivate"
}
. $venvActivate

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4) Build exe with PyInstaller
# --windowed hides console, --onefile packs into single exe
pyinstaller --noconfirm --clean --windowed --onefile --name OrdersApp main.py

# 5) Build installer with Inno Setup if available
$inno = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $inno) {
    & "$inno" "build\installer.iss"
    Write-Host ""
    Write-Host "Installer created: $(Resolve-Path .\Output\OrdersAppSetup.exe)" -ForegroundColor Green
} else {
    Write-Warning "Inno Setup not found at: $inno"
    Write-Warning "Please install Inno Setup from https://jrsoftware.org/isinfo.php and run:"
    Write-Warning "`"$inno`" build\installer.iss"
    Write-Host ""
    Write-Host "Portable EXE available at: $(Resolve-Path .\dist\OrdersApp.exe)" -ForegroundColor Yellow
}