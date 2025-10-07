# Build a ZIP archive with project sources (Windows PowerShell)
# Usage:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\build\build_zip.ps1

$ErrorActionPreference = "Stop"

$files = @(
    "main.py",
    "database.py",
    "mkl_interface.py",
    "meridian_interface.py",
    "utils_export.py",
    "requirements.txt",
    "README_INSTALLER.md",
    "build\installer.iss",
    "build\build_windows.ps1"
)

# Validate
$missing = @()
foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        $missing += $f
    }
}
if ($missing.Count -gt 0) {
    Write-Error "Missing files: `n$($missing -join "`n")"
}

$zip = "OrdersApp.zip"
if (Test-Path $zip) {
    Remove-Item $zip -Force
}

Compress-Archive -Path $files -DestinationPath $zip -Force
Write-Host "Created: $(Resolve-Path $zip)" -ForegroundColor Green