"""Capture ONLY the application's client rectangle, using fictitious temp data."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    import tkinter as tk
    from PIL import ImageGrab
    from medilocal.gui import App
    from medilocal.store import Store
    output = Path(__file__).resolve().parent.parent / "docs/images"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / "medilocal.db")
        pid = store.save_profile("Ana · Ejemplo / Example", "Persona")
        store.save_profile("Luna · Ejemplo / Example", "Mascota")
        store.save_product(pid, "Medicamento", "Producto ficticio / Example entry", "Indicación de ejemplo / Example instruction", "08:00,20:00", "Datos ficticios / Fictitious data")
        root = tk.Tk()
        try:
            app = App(root, store)
            root.geometry("1000x720+0+0")
            root.attributes("-topmost", True)
            variants = iter((language, theme) for language in ("es", "en") for theme in ("dark", "light"))
            def advance():
                pair = next(variants, None)
                if pair is None:
                    root.quit()
                    return
                language, theme = pair
                app.change_setting("language", language)
                app.change_setting("theme", theme)
                app.profile_id = pid
                app.show("products")
                root.lift()
                def capture():
                    x, y = root.winfo_rootx(), root.winfo_rooty()
                    ImageGrab.grab(bbox=(x, y, x+root.winfo_width(), y+root.winfo_height())).save(output / f"{language}-{theme}.png")
                    root.after(100, advance)
                root.after(900, capture)
            root.after(500, advance)
            root.mainloop()
            print("4 screenshots captured using fictitious data.")
        finally:
            root.destroy()


if __name__ == "__main__":
    main()
