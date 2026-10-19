"""Packaged executable check. Uses only a temporary, fictitious database."""
import tempfile
from pathlib import Path


def run():
    import tkinter as tk
    from .gui import App
    from .store import Store
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / "medilocal.db")
        profile = store.save_profile("Example", "Persona")
        store.save_product(profile, "Medicamento", "Example entry", "Fictitious instruction", "08:00,20:00")
        backup = Path(directory) / "backup.db"
        store.backup(backup)
        store.restore(backup)
        assert len(Store(store.path).products(profile)[0]["horarios"]) == 2
        root = tk.Tk()
        try:
            app = App(root, store)
            errors = []
            root.report_callback_exception = lambda *args: errors.append(True)
            for language in ("es", "en"):
                app.change_setting("language", language)
                for theme in ("dark", "light"):
                    app.change_setting("theme", theme)
                    app.profile_id = profile
                    app.show("products")
                    root.update()
            root.after(200, root.quit)
            root.mainloop()
            return int(bool(errors))
        finally:
            root.destroy()
