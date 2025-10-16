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


def install_copy_paste_bindings(root: tk.Tk):
    """
    Install global copy/paste/cut/select-all shortcuts that work across keyboard layouts
    for common input widgets (Entry, Text, Combobox, Spinbox).

    - Ctrl/Cmd + C/V/X/A
    - Ctrl + Insert (Copy), Shift + Insert (Paste)
    - Cyrillic equivalents based on physical key positions:
      * Copy: Ctrl + 'с' (C key on RU)
      * Paste: Ctrl + 'м' (V key on RU)
      * Cut: Ctrl + 'ч' (X key on RU)
      * Select all: Ctrl + 'ф' (A key on RU)
    """
    try:
        # Map shortcut to a virtual event generation on the focused widget
        def _gen(event_name):
            w = root.focus_get()
            if not w:
                return
            try:
                w.event_generate(event_name)
            except Exception:
                pass

        def _copy(_e=None): _gen("<<Copy>>")
        def _paste(_e=None): _gen("<<Paste>>")
        def _cut(_e=None): _gen("<<Cut>>")
        def _sel_all(_e=None):
            w = root.focus_get()
            if not w:
                return
            try:
                # Try virtual first
                w.event_generate("<<SelectAll>>")
            except Exception:
                # Fallback per widget types
                try:
                    if isinstance(w, (tk.Entry, tk.Spinbox, tk.Text, tk.ttk.Entry, tk.ttk.Combobox)):
                        try:
                            w.select_range(0, "end")
                            w.icursor("end")
                        except Exception:
                            w.event_generate("<Control-Home>")
                            w.event_generate("<Shift-End>")
                except Exception:
                    pass

        # Base Latin bindings
        for seq in ("<Control-c>", "<Control-C>", "<Control-Insert>"):
            root.bind_all(seq, _copy)
        for seq in ("<Control-v>", "<Control-V>", "<Shift-Insert>"):
            root.bind_all(seq, _paste)
        for seq in ("<Control-x>", "<Control-X>"):
            root.bind_all(seq, _cut)
        for seq in ("<Control-a>", "<Control-A>"):
            root.bind_all(seq, _sel_all)

        # MacOS Command key variants
        for seq in ("<Command-c>", "<Command-C>"):
            root.bind_all(seq, _copy)
        for seq in ("<Command-v>", "<Command-V>"):
            root.bind_all(seq, _paste)
        for seq in ("<Command-x>", "<Command-X>"):
            root.bind_all(seq, _cut)
        for seq in ("<Command-a>", "<Command-A>"):
            root.bind_all(seq, _sel_all)

        # Cyrillic letter equivalents by physical key mapping:
        # C->с, V->м, X->ч, A->ф
        for seq in ("<Control-с>", "<Control-С>"):
            root.bind_all(seq, _copy)
        for seq in ("<Control-м>", "<Control-М>"):
            root.bind_all(seq, _paste)
        for seq in ("<Control-ч>", "<Control-Ч>"):
            root.bind_all(seq, _cut)
        for seq in ("<Control-ф>", "<Control-Ф>"):
            root.bind_all(seq, _sel_all)

        # Fallback handler based on key press with Control state bit
        def _on_keypress(e):
            try:
                ctrl = bool(e.state & 0x4)  # Control mask
            except Exception:
                ctrl = False
            if not ctrl:
                return
            ks = (getattr(e, "keysym", "") or "")
            if ks in ("c", "C", "с", "С"):
                _copy(e)
            elif ks in ("v", "V", "м", "М"):
                _paste(e)
            elif ks in ("x", "X", "ч", "Ч"):
                _cut(e)
            elif ks in ("a", "A", "ф", "Ф"):
                _sel_all(e)

        root.bind_all("<KeyPress>", _on_keypress)
        # Tk will propagate bind_all to future widgets.
    except Exception:
        # Avoid breaking startup if platform doesn't support some sequences
        pass


