Windows installer build guide

This repository includes scripts to build a Windows installer (OrdersAppSetup.exe) for the desktop application.

Two outputs you can produce:
- Portable EXE (no installation needed): dist/OrdersApp.exe
- Installer EXE (with Start menu/desktop shortcuts): Output/OrdersAppSetup.exe


A) Quick build on Windows (PowerShell)
1) Open PowerShell in the project folder and allow script execution for the session:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

2) Run the build script:
   .\build\build_windows.ps1

What the script does:
- Creates and activates a virtual environment .venv
- Installs dependencies (from requirements.txt) + pyinstaller
- Builds a portable EXE with PyInstaller into dist\OrdersApp.exe
- If Inno Setup is installed at the default path, it builds the installer via build\installer.iss into Output\OrdersAppSetup.exe

If you do not have Inno Setup installed:
- Download and install it: https://jrsoftware.org/isinfo.php
- Then re-run the script or run:
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss


B) Manual steps (alternative)
1) Create virtual environment and install dependencies:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pyinstaller

2) Build the app (portable EXE):
   pyinstaller --noconfirm --clean --windowed --onefile --name OrdersApp main.py
   - Result: dist\OrdersApp.exe

3) Build the installer (optional):
   Install Inno Setup from https://jrsoftware.org/isinfo.php
   Then run:
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss
   - Result: Output\OrdersAppSetup.exe


C) macOS and Linux notes
- macOS portable app:
  pip install pyinstaller
  pyinstaller --windowed --name OrdersApp main.py
  - Result: dist/OrdersApp.app
  To create a DMG you can use a third-party tool like create-dmg.

- Linux portable:
  pip install pyinstaller
  pyinstaller --windowed --name OrdersApp main.py
  - Result: dist/OrdersApp
  For deb/rpm packaging consider fpm, makeself, or your system’s native packager.


Output locations
- Portable EXE: dist\OrdersApp.exe
- Installer EXE: Output\OrdersAppSetup.exe


Troubleshooting
- If PyQt platform plugins error appears when running the EXE, ensure you used --windowed and did a clean build. You can also try:
  pyinstaller --clean --windowed --onefile --name OrdersApp main.py
- If Inno Setup isn’t found, verify the path to ISCC.exe or add it to your PATH.
- If antivirus blocks the EXE, sign it with your code signing certificate (optional, enterprise need).


Unattended installer build (CI-ready)
- You can run build\build_windows.ps1 from CI (Windows runner) if you pre-install Python and Inno Setup on the agent. The script emits paths of the produced artifacts.


Enjoy!