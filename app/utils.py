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

    Strategy:
    - Bind a handler to <Control-KeyPress> for Entry, Text, TCombobox and also bind_all as fallback.
    - Detect Cyrillic keys by keysym OR actual char (Unicode), supporting both lowercase and uppercase.
    - Trigger the appropriate action (prefer Tk virtual events; fallback to direct ops for Entry/Text).
    """
    try:
        # Sets of identifiers for each action
        COPY_KEYS = {"c", "C", "cyrillic_es", "Cyrillic_es", "Cyrillic_ES", "с", "С"}
        PASTE_KEYS = {"v", "V", "cyrillic_em", "Cyrillic_em", "Cyrillic_EM", "м", "М"}
        CUT_KEYS = {"x", "X", "cyrillic_che", "Cyrillic_che", "Cyrillic_CHE", "ч", "Ч"}
        SELECT_ALL_KEYS = {"a", "A", "cyrillic_ef", "Cyrillic_ef", "Cyrillic_EF", "ф", "Ф"}

        def _do_copy(widget):
            try:
                widget.event_generate("<<Copy>>")
            except Exception:
                # Fallback direct copy
                try:
                    if widget.winfo_class() in ("Entry", "TCombobox"):
                        try:
                            sel = widget.selection_get()
                        except Exception:
                            # Entry selection range
                            try:
                                i1 = widget.index("sel.first"); i2 = widget.index("sel.last")
                                sel = widget.get()[int(i1):int(i2)]
                            except Exception:
                                sel = ""
                        if sel:
                            root.clipboard_clear()
                            root.clipboard_append(sel)
                    elif widget.winfo_class() == "Text":
                        try:
                            sel = widget.get("sel.first", "sel.last")
                            root.clipboard_clear()
                            root.clipboard_append(sel)
                        except Exception:
                            pass
                except Exception:
                    pass

        def _do_paste(widget):
            try:
                widget.event_generate("<<Paste>>")
            except Exception:
                try:
                    txt = root.clipboard_get()
                    if widget.winfo_class() in ("Entry", "TCombobox"):
                        try:
                            widget.insert("insert", txt)
                        except Exception:
                            pass
                    elif widget.winfo_class() == "Text":
                        try:
                            widget.insert("insert", txt)
                        except Exception:
                            pass
                except Exception:
                    pass

        def _do_cut(widget):
            try:
                widget.event_generate("<<Cut>>")
            except Exception:
                try:
                    # Implement cut: copy selection then delete
                    if widget.winfo_class() in ("Entry", "TCombobox"):
                        try:
                            sel = widget.selection_get()
                        except Exception:
                            try:
                                i1 = widget.index("sel.first"); i2 = widget.index("sel.last")
                                sel = widget.get()[int(i1):int(i2)]
                            except Exception:
                                sel = ""
                        if sel:
                            root.clipboard_clear()
                            root.clipboard_append(sel)
                            try:
                                widget.delete("sel.first", "sel.last")
                            except Exception:
                                pass
                    elif widget.winfo_class() == "Text":
                        try:
                            sel = widget.get("sel.first", "sel.last")
                            root.clipboard_clear()
                            root.clipboard_append(sel)
                            widget.delete("sel.first", "sel.last")
                        except Exception:
                            pass
                except Exception:
                    pass

        def _do_select_all(widget):
            try:
                widget.event_generate("<<SelectAll>>")
            except Exception:
                try:
                    if widget.winfo_class() in ("Entry", "TCombobox"):
                        try:
                            widget.selection_range(0, "end")
                            widget.icursor("end")
                        except Exception:
                            pass
                    elif widget.winfo_class() == "Text":
                        try:
                            widget.tag_add("sel", "1.0", "end-1c")
                        except Exception:
                            pass
                except Exception:
                    pass

        def _ctrl_handler(e):
            try:
                keys = set()
                ks = e.keysym or ""
                kc = e.char or ""
                # Collect possible identifiers
                keys.add(ks)
                keys.add(ks.lower())
                keys.add(kc)
                # Decide action
                widget = e.widget
                if keys & COPY_KEYS:
                    _do_copy(widget)
                    return "break"
                if keys & PASTE_KEYS:
                    _do_paste(widget)
                    return "break"
                if keys & CUT_KEYS:
                    _do_cut(widget)
                    return "break"
                if keys & SELECT_ALL_KEYS:
                    _do_select_all(widget)
                    return "break"
            except Exception:
                pass
            return None  # let default bindings handle other cases

        # Bind to common editable classes
        for cls in ("Entry", "Text", "TCombobox"):
            try:
                root.bind_class(cls, "<Control-KeyPress>", _ctrl_handler, add=True)
            except Exception:
                pass
        # Global fallback in case some widgets don't have class binding
        try:
            root.bind_all("<Control-KeyPress>", _ctrl_handler, add=True)
        except Exception:
            pass
    except Exception:
        # Non-fatal
        pass


