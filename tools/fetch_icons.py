"""
Fetch a minimal icon set (SVG) from Lucide and convert to PNG for the app toolbars.

Usage:
  python tools/fetch_icons.py

Requirements:
  pip install requests cairosvg

It will create PNG icons in app/assets/icons with specific names expected by the UI:
  - add.png, edit.png, delete.png, status.png, products.png, clients.png, export.png, settings.png, back.png

You can adjust ICON_MAP below to change the source icon slugs or target names.
"""
from __future__ import annotations

import io
import os
import sys
from typing import Dict

import requests
import cairosvg


# Map target filename -> lucide icon slug (https://github.com/lucide-icons/lucide/tree/main/icons)
ICON_MAP: Dict[str, str] = {
    "add": "plus-circle",
    "edit": "pencil",
    "delete": "trash-2",
    "status": "check-circle",
    "products": "package",
    "clients": "users",
    "export": "download",
    "settings": "settings",
    "back": "arrow-left",
}

SIZE_PX = 20  # toolbar icon size
COLOR = "#111111"  # monochrome, works in both light and dark themes


def ensure_dir(p: str) -> None:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def fetch_svg(slug: str) -> str:
    url = f"https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{slug}.svg"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def recolor_svg(svg_text: str, color_hex: str) -> str:
    """
    Lucide icons are stroke-based. Force stroke color and remove any hard-coded color attributes.
    """
    s = svg_text
    # Remove existing stroke/fill attributes to avoid conflicts
    s = s.replace('stroke="currentColor"', "")
    s = s.replace('fill="none"', "")
    s = s.replace("stroke-linecap", "data-linecap")
    s = s.replace("stroke-linejoin", "data-linejoin")
    # Inject our style on the root svg tag
    s = s.replace("<svg", f'<svg stroke="{color_hex}" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"', 1)
    return s


def svg_to_png(svg_text: str, out_path: str, size_px: int) -> None:
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=out_path, output_width=size_px, output_height=size_px)


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icons_dir = os.path.join(project_root, "app", "assets", "icons")
    ensure_dir(icons_dir)

    ok = 0
    for name, slug in ICON_MAP.items():
        try:
            svg = fetch_svg(slug)
            svg = recolor_svg(svg, COLOR)
            out_path = os.path.join(icons_dir, f"{name}.png")
            svg_to_png(svg, out_path, SIZE_PX)
            print(f"[ok] {name}.png ← {slug}")
            ok += 1
        except Exception as e:
            print(f"[fail] {name} ({slug}): {e}")
    print(f"Done: {ok}/{len(ICON_MAP)} icons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())