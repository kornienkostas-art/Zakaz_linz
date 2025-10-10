import atexit
import tkinter as tk

from app.views.main import MainWindow
from app.utils import enable_ru_shortcuts

def main():
    # High-DPI scaling for readability (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    # Enable RU-layout shortcuts (Copy/Paste/Cut/Select All)
    try:
        enable_ru_shortcuts(root)
    except Exception:
        pass

    # Tk scaling improves text/UI size on HiDPI
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass

    # Ensure DB connection closes on exit
    def _close_db():
        db = getattr(root, "db", None)
        if db:
            try:
                db.conn.close()
            except Exception:
                pass

    atexit.register(_close_db)

    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()