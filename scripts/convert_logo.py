"""
Utility to convert an existing logo image (e.g., assets/лого.jpeg) into:
- assets/logo.png (PNG, square)
- assets/app.ico   (Windows icon with multiple sizes)

Requirements:
  pip install pillow

Usage (from repo root):
  python scripts/convert_logo.py

It will try to find a source image automatically:
- assets/logo.png
- assets/logo.jpg / .jpeg
- assets/лого.jpeg
- the first image in assets/*.(png|jpg|jpeg)
"""

from __future__ import annotations
import os
import sys
from glob import glob
from typing import Optional, Tuple

try:
    from PIL import Image
except Exception as e:
    print("Pillow is required. Install it with: pip install pillow")
    sys.exit(1)


ASSETS_DIR = os.path.join(os.getcwd(), "assets")
OUT_PNG = os.path.join(ASSETS_DIR, "logo.png")
OUT_ICO = os.path.join(ASSETS_DIR, "app.ico")


def _find_source() -> Optional[str]:
    if not os.path.isdir(ASSETS_DIR):
        return None
    candidates = [
        os.path.join(ASSETS_DIR, "logo.png"),
        os.path.join(ASSETS_DIR, "logo.jpg"),
        os.path.join(ASSETS_DIR, "logo.jpeg"),
        os.path.join(ASSETS_DIR, "лого.jpeg"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # Fallback: first image in assets
    for ext in ("png", "jpg", "jpeg"):
        imgs = sorted(glob(os.path.join(ASSETS_DIR, f"*.{ext}")))
        if imgs:
            return imgs[0]
    return None


def _make_square(img: Image.Image, fill=(255, 255, 255, 0)) -> Image.Image:
    w, h = img.size
    size = max(w, h)
    # Transparent background for PNG; for JPEG fallback use white
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGBA", (size, size), fill)
    else:
        bg = Image.new("RGB", (size, size), (255, 255, 255))
    offset = ((size - w) // 2, (size - h) // 2)
    bg.paste(img, offset)
    return bg


def _save_png_square(src_path: str, out_path: str) -> None:
    with Image.open(src_path) as im:
        im = im.convert("RGBA") if im.mode != "RGBA" else im.copy()
        sq = _make_square(im)
        # Normalize to 512x512 for better icon downsampling
        sq = sq.resize((512, 512), Image.LANCZOS)
        sq.save(out_path, format="PNG", optimize=True)
        print(f"Saved PNG: {out_path}")


def _save_ico_from_png(png_path: str, out_path: str) -> None:
    with Image.open(png_path) as im:
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        # PIL will auto-generate sizes if we pass sizes param
        im.save(out_path, format="ICO", sizes=sizes)
        print(f"Saved ICO: {out_path} (sizes: {', '.join(f'{w}x{h}' for w,h in sizes)})")


def main():
    src = _find_source()
    if not src:
        print("No source logo found in 'assets'. Put your image (PNG/JPG/JPEG) there and re-run.")
        sys.exit(1)
    print(f"Source: {src}")

    os.makedirs(ASSETS_DIR, exist_ok=True)
    try:
        _save_png_square(src, OUT_PNG)
    except Exception as e:
        print(f"Failed to save PNG: {e}")
        sys.exit(2)
    try:
        _save_ico_from_png(OUT_PNG, OUT_ICO)
    except Exception as e:
        print(f"Failed to save ICO: {e}")
        sys.exit(3)
    print("Done.")


if __name__ == "__main__":
    main()