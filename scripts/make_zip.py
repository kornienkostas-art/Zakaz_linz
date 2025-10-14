import os
import zipfile

EXCLUDES = {
    ".git",
    ".gitignore",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
}

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT = os.path.join(ROOT, "project.zip")


def should_exclude(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(p in EXCLUDES for p in parts)


def add_file(zf: zipfile.ZipFile, root: str, file_path: str):
    rel = os.path.relpath(file_path, root)
    zf.write(file_path, arcname=rel)


def add_dir(zf: zipfile.ZipFile, root: str, dir_path: str):
    for base, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(base, d))]
        for f in files:
            fp = os.path.join(base, f)
            if should_exclude(fp):
                continue
            add_file(zf, root, fp)


def main():
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # root files
        for name in ("README.md", "requirements.txt", "main.py"):
            fp = os.path.join(ROOT, name)
            if os.path.isfile(fp):
                add_file(zf, ROOT, fp)
        # app directory
        app_dir = os.path.join(ROOT, "app")
        if os.path.isdir(app_dir):
            add_dir(zf, ROOT, app_dir)

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()