import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
ZIP_NAME = "OrdersApp.zip"

FILES = [
    "main.py",
    "database.py",
    "mkl_interface.py",
    "meridian_interface.py",
    "utils_export.py",
    "requirements.txt",
    "README_INSTALLER.md",
    "build/installer.iss",
    "build/build_windows.ps1",
]

def main():
    missing = [f for f in FILES if not (ROOT / f).exists()]
    if missing:
        print("Cannot build zip, missing files:")
        for m in missing:
            print(" -", m)
        sys.exit(1)

    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in FILES:
            p = ROOT / rel
            zf.write(p, arcname=rel)
    print(f"Created: {zip_path.as_posix()}")

if __name__ == "__main__":
    main()