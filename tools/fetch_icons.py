"""
Fetch a minimal icon set for the app toolbars.

Primary method:
  - Download ready-to-use PNGs from Iconify API (no converters required).

Fallback (if Iconify blocked):
  - Download Lucide SVGs from GitHub and convert to PNG via cairosvg (if installed).

Usage:
  python tools/fetch_icons.py

Creates PNG icons in app/assets/icons:
  add.png, edit.png, delete.png, status.png, products.png, clients.png, export.png, settings.png, back.png
"""
from __future__ import annotations

import os
from typing import Dict, Optional

import requests

# Optional converter
try:
    import cairosvg  # type: ignore
except Exception:
    cairosvg = None  # type: ignore


# Map target filename -> lucide icon slug
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
COLOR_HEX = "111111"  # without '#', for Iconify query


def ensure_dir(p: str) -> None:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def fetch_png_via_iconify(slug: str, size_px: int, color_hex: str) -> Optional[bytes]:
    """
    Use Iconify API to get a PNG directly:
      https://api.iconify.design/lucide:{slug}.png?color=%23{hex}&width={w}&height={h}
    """
    url = f"https://api.iconify.design/lucide:{slug}.png?color=%23{color_hex}&width={size_px}&height={size_px}"
    resp = requests.get(url, timeout=20)
    if resp.ok and resp.content:
        return resp.content
    return None


def fetch_svg_lucide(slug: str) -> Optional[str]:
    url = f"https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{slug}.svg"
    resp = requests.get(url, timeout=20)
    if resp.ok:
        return resp.text
    return None


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
    s = s.replace("<svg", f'<svg stroke="#{color_hex}" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"', 1)
    return s


def svg_to_png(svg_text: str, size_px: int) -> Optional[bytes]:
    if cairosvg is None:
        return None
    return cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), output_width=size_px, output_height=size_px)


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icons_dir = os.path.join(project_root, "app", "assets", "icons")
    ensure_dir(icons_dir)

    ok = 0
    for name, slug in ICON_MAP.items():
        out_path = os.path.join(icons_dir, f"{name}.png")

        # 1) Try direct PNG from Iconify
        content: Optional[bytes] = None
        try:
            content = fetch_png_via_iconify(slug, SIZE_PX, COLOR_HEX)
            if content:
                with open(out_path, "wb") as f:
                    f.write(content)
                print(f"[ok] {name}.png ← Iconify {slug}")
                ok += 1
                continue
        except Exception as e:
            print(f"[warn] Iconify failed for {name}: {e}")

        # 2) Fallback: SVG from GitHub + cairosvg conversion (if available)
        try:
            svg = fetch_svg_lucide(slug)
            if not svg:
                raise RuntimeError("SVG not downloaded")
            svg = recolor_svg(svg, COLOR_HEX)
            png_bytes = svg_to_png(svg, SIZE_PX)
            if not png_bytes:
                raise RuntimeError("cairosvg not installed or conversion failed")
            with open(out_path, "wb") as f:
                f.write(png_bytes)
            print(f"[ok] {name}.png ← Lucide+SVG {slug}")
            ok += 1
            continue
        except Exception as e:
            print(f"[fail] {name} ({slug}): {e}")

    print(f"Done: {ok}/{len(ICON_MAP)} icons")
    if ok == 0:
        print("No icons fetched. Check your internet connection or firewall, then try again.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())