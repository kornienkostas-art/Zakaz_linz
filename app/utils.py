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


def fade_transition(root: tk.Tk, swap_callback, duration_ms: int = 0, steps: int = 0):
    """Instant view swap (effects disabled for speed). Force window visible."""
    try:
        swap_callback()
    except Exception:
        # Ensure swap still occurs even if callback raises internally
        try:
            swap_callback()
        except Exception:
            pass
    # Ensure window is visible and fully opaque
    try:
        root.deiconify()
        root.attributes("-alpha", 1.0)
    except Exception:
        pass


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


def install_crosslayout_shortcuts(root: tk.Tk):
    """
    Enable common shortcuts (copy/paste/cut/undo/redo/select all) to work regardless of keyboard layout.
    This listens to physical key codes for A/C/V/X/Z/Y with Control (and Shift where applicable)
    and generates Tk virtual events (<<Copy>>, <<Paste>>, <<Cut>>, <<Undo>>, <<Redo>>, <<SelectAll>>)
    for the currently focused widget.

    Works with Entry, Text and most ttk widgets that support these virtual events.
    """

    # Virtual-Key codes are stable across layouts on Windows and most X11 setups
    VK = {
        "A": 65,
        "C": 67,
        "V": 86,
        "X": 88,
        "Y": 89,
        "Z": 90,
    }

    def _generate(widget, virtual_event: str):
        try:
            widget.event_generate(virtual_event)
        except Exception:
            pass

    def on_ctrl_key(event):
        try:
            # event.state bit 0x4 usually indicates Control pressed on Tk
            # But we are bound to <Control-KeyPress> already; treat all as handled.
            widget = event.widget.focus_get() if hasattr(event.widget, "focus_get") else event.widget
            if widget is None:
                widget = root.focus_get()
            keycode = getattr(event, "keycode", None)

            if keycode == VK["C"]:
                _generate(widget, "<<Copy>>")
                return "break"
            if keycode == VK["V"]:
                _generate(widget, "<<Paste>>")
                return "break"
            if keycode == VK["X"]:
                _generate(widget, "<<Cut>>")
                return "break"
            if keycode == VK["A"]:
                _generate(widget, "<<SelectAll>>")
                return "break"
            if keycode == VK["Z"]:
                _generate(widget, "<<Undo>>")
                return "break"
            if keycode == VK["Y"]:
                _generate(widget, "<<Redo>>")
                return "break"
        except Exception:
            pass
        # Do not block default if nothing matched
        return None

    # Bind on the application level to catch keys in any focused widget
    try:
        root.bind_all("<Control-KeyPress>", on_ctrl_key, add="+")
    except Exception:
        pass

    # Also support Shift+Insert (paste), Control+Insert (copy), Shift+Delete (cut)
    def on_shift_insert(event):
        try:
            widget = root.focus_get()
            if widget:
                _generate(widget, "<<Paste>>")
                return "break"
        except Exception:
            pass
        return None

    def on_ctrl_insert(event):
        try:
            widget = root.focus_get()
            if widget:
                _generate(widget, "<<Copy>>")
                return "break"
        except Exception:
            pass
        return None

    def on_shift_delete(event):
        try:
            widget = root.focus_get()
            if widget:
                _generate(widget, "<<Cut>>")
                return "break"
        except Exception:
            pass
        return None

    try:
        root.bind_all("<Shift-Insert>", on_shift_insert, add="+")
        root.bind_all("<Control-Insert>", on_ctrl_insert, add="+")
        root.bind_all("<Shift-Delete>", on_shift_delete, add="+")
    except Exception:
        pass


