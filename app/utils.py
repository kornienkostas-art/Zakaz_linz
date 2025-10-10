import re
import tkinter as tk

def set_initial_geometry(win: tk.Tk | tk.Toplevel, min_w: int, min_h: int, center_to: tk.Tk | None = None):
    """Adaptive window sizing: ensure minimum size and center on screen or relative to parent."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()

    # Target size: 70% of screen, but not less than min and not more than 90% of screen
    tw = max(min_w, int(sw * 0.7))
    th = max(min_h, int(sh * 0.7))
    tw = min(tw, int(sw * 0.9))
    th = min(th, int(sh * 0.9))

    win.geometry(f"{tw}x{th}")
    win.minsize(min_w, min_h)

    if center_to:
        x = center_to.winfo_rootx() + (center_to.winfo_width() // 2) - (tw // 2)
        y = center_to.winfo_rooty() + (center_to.winfo_height() // 2) - (th // 2)
    else:
        x = (sw // 2) - (tw // 2)
        y = (sh // 2) - (th // 2)
    win.geometry(f"+{x}+{y}")

def center_on_screen(win: tk.Toplevel | tk.Tk):
    """Center an existing window on the screen without changing its size."""
    try:
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        ww = win.winfo_width()
        wh = win.winfo_height()
        if ww <= 1 or wh <= 1:
            # for newly created Toplevel before geometry calculation
            geo = win.geometry()
            # fallback size
            ww = 400
            wh = 300
        x = (sw // 2) - (ww // 2)
        y = (sh // 2) - (wh // 2)
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass

def fade_transition(root: tk.Tk, swap_callback, duration_ms: int = 120, steps: int = 8):
    """Simple fade-out, swap view, fade-in on the root window."""
    try:
        # Fade out
        for i in range(steps):
            alpha = 1.0 - (i + 1) / steps
            root.attributes("-alpha", max(0.0, alpha))
            root.update_idletasks()
            root.after(int(duration_ms / steps))
        # Swap content
        swap_callback()
        root.update_idletasks()
        # Fade in
        for i in range(steps):
            alpha = (i + 1) / steps
            root.attributes("-alpha", min(1.0, alpha))
            root.update_idletasks()
            root.after(int(duration_ms / steps))
        root.attributes("-alpha", 1.0)
    except tk.TclError:
        # If alpha not supported, just swap
        swap_callback()

def format_phone_mask(raw: str) -> str:
    """Format phone to '+7-XXX-XXX-XX-XX' or '8-XXX-XXX-XX-XX' for display, accepting various inputs."""
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return (raw or "").strip()

    prefix = ""
    tail = ""

    if len(digits) >= 11:
        # Take first digit as prefix if it's 7 or 8
        if digits[0] == "7":
            prefix = "+7"
            tail = digits[1:11]
        elif digits[0] == "8":
            prefix = "8"
            tail = digits[1:11]
        else:
            # Unknown leading, fallback to use last 10 with default '8'
            prefix = "8"
            tail = digits[-10:]
    elif len(digits) == 10:
        # Local format, default to '8'
        prefix = "8"
        tail = digits
    else:
        # Not enough digits to format, return original trimmed
        return (raw or "").strip()

    return f"{prefix}-{tail[0:3]}-{tail[3:6]}-{tail[6:8]}-{tail[8:10]}"

def enable_ru_shortcuts(root: tk.Tk):
    """
    Make Ctrl-based editing shortcuts work under Russian keyboard layout.

    Logic:
    - Bind a single handler to <Control-KeyPress> for editable widgets.
    - If keysym corresponds to Cyrillic letters that map to C/V/X/A, generate the proper virtual event.
    - Do nothing for Latin keys (so default Tk behavior remains and we avoid double actions).

    Cyrillic mapping:
    - Cyrillic_es  -> Copy   (С)
    - Cyrillic_em  -> Paste  (М)
    - Cyrillic_che -> Cut    (Ч)
    - Cyrillic_ef  -> SelectAll (Ф)

    Applies to: Entry, Text, TCombobox.
    """
    try:
        cyr_map = {
            "cyrillic_es": "<<Copy>>",
            "cyrillic_em": "<<Paste>>",
            "cyrillic_che": "<<Cut>>",
            "cyrillic_ef": "<<SelectAll>>",
        }

        def _ctrl_handler(e):
            try:
                ks = (e.keysym or "").lower()
                if ks in cyr_map:
                    try:
                        e.widget.event_generate(cyr_map[ks])
                    except Exception:
                        pass
                    return "break"  # prevent any default handling to avoid duplicates
            except Exception:
                pass
            # For Latin shortcuts, let default Tk bindings work
            return None

        for cls in ("Entry", "Text", "TCombobox"):
            try:
                root.bind_class(cls, "<Control-KeyPress>", _ctrl_handler, add=True)
            except Exception:
                pass
    except Exception:
        # Non-fatal
        pass


