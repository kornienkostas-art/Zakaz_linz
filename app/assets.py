import os
import tkinter as tk


def load_logo(master: tk.Misc) -> tk.PhotoImage | None:
    """
    Try to load app logo from assets/logo.png, fallback to assets/лого.jpeg.
    Returns a Tk PhotoImage or None if not found/failed.
    """
    base = os.getcwd()
    candidates = [
        os.path.join(base, "assets", "logo.png"),
        os.path.join(base, "assets", "лого.jpeg"),
        os.path.join(base, "assets", "logo.jpg"),
    ]
    for path in candidates:
        try:
            if os.path.isfile(path):
                # PNG is supported directly; JPEG via PhotoImage starting from Tk 8.6 with PIL not required on Windows
                # If JPEG isn't supported, this may raise _tkinter.TclError, we'll try next candidate.
                img = tk.PhotoImage(file=path)
                return img
        except Exception:
            continue
    return None