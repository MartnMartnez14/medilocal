"""Packaged executable check: real UI actions and temporary fictitious data only."""
import tempfile
from pathlib import Path


def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)


def invoke(app, parent, key):
    from tkinter import ttk
    button = next(w for w in widgets(parent) if isinstance(w, ttk.Button) and w.cget('text') == app.t(key))
    button.invoke()


def exercise_details(app, root, product_id):
    """Exercise actual button and key bindings, not just Python methods."""
    from tkinter import ttk
    import time
    for route in ('button', 'enter', 'double_click'):
        app.tree.selection_set(str(product_id))
        app.tree.see(str(product_id))
        app.tree.focus_force()
        root.update()
        if route == 'button':
            invoke(app, app.content, 'details')
        elif route == 'enter':
            app.tree.event_generate('<Return>')
        else:
            x, y, width, height = app.tree.bbox(str(product_id))
            timestamp = int(time.monotonic() * 1000) & 0x7fffffff
            for event, offset in (('<ButtonPress-1>', 0), ('<ButtonRelease-1>', 10), ('<ButtonPress-1>', 80), ('<ButtonRelease-1>', 90)):
                app.tree.event_generate(event, x=x+10, y=y+height//2, time=timestamp+offset)
        root.update()
        assert not app.last_diagnostic, 'Unexpected diagnostic during details check'
        dialogs = list(app.dialog_windows)
        assert len(dialogs) == 1, 'Details dialog did not open'
        dialog = dialogs[0]
        labels = [str(w.cget('text')) for w in widgets(dialog) if isinstance(w, ttk.Label)]
        assert 'Example supplement' in labels, 'Details content is missing'
        assert app.t('Suplemento') in labels, 'Supplement kind is missing'
        assert '09:00, 21:00' in labels, 'Daily times are missing'
        invoke(app, dialog, 'close')
        root.update()
        assert not app.dialog_windows
        assert root.grab_current() is None
    invoke(app, app.content, 'edit_product')
    root.update()
    assert not app.last_diagnostic
    dialog = next(iter(app.dialog_windows))
    entries = [w for w in widgets(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
    assert entries[0].get() == 'Example supplement'
    invoke(app, dialog, 'cancel')
    root.update()


def run():
    import json
    import tkinter as tk
    from tkinter import ttk
    from .gui import App
    from .store import Store
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / 'medilocal.db')
        profile = store.save_profile('Example', 'Persona')
        root = tk.Tk()
        try:
            app = App(root, store)
            errors = []
            root.report_callback_exception = lambda *args: errors.append(True)
            root.update()
            app.profile_id = profile
            app.show('products')
            invoke(app, app.content, 'add_product')
            dialog = next(iter(app.dialog_windows))
            next(w for w in widgets(dialog) if isinstance(w, ttk.Combobox)).current(1)
            entries = [w for w in widgets(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
            for entry, value in zip(entries, ('Example supplement', 'Fictitious instruction', '09:00,21:00')):
                entry.insert(0, value)
            invoke(app, dialog, 'save')
            root.update()
            assert not app.dialog_windows
            product_id = store.products(profile)[0]['id']
            backup = Path(directory) / 'backup.db'
            store.backup(backup)
            store.restore(backup)
            # Reopen persistence and rebuild the UI, as after a restart.
            app.store = Store(store.path)
            assert len(app.store.products(profile)[0]['horarios']) == 2
            for language in ('es', 'en'):
                app.change_setting('language', language)
                for theme in ('dark', 'light'):
                    app.change_setting('theme', theme)
                    app.profile_id = profile
                    app.show('products')
                    root.update()
                    exercise_details(app, root, product_id)
            # Fault injection verifies the diagnostic UI inside the frozen binary too.
            before = app.store.products(profile)
            app.tree.selection_set(str(product_id))
            del app.rows[str(product_id)]['hora_original']
            invoke(app, app.content, 'details')
            root.update()
            assert not app.dialog_windows
            assert root.grab_current() is None
            diagnostic = json.loads(app.last_diagnostic)
            assert diagnostic['exception'] == 'KeyError'
            assert diagnostic['missing_key'] == 'hora_original'
            assert 'Example supplement' not in app.last_diagnostic
            assert str(directory) not in app.last_diagnostic
            invoke(app, app.error_window, 'copy_diagnostic')
            root.update()
            assert root.clipboard_get() == app.last_diagnostic
            invoke(app, app.error_window, 'close')
            app.last_diagnostic = ''
            app.refresh()
            assert app.store.products(profile) == before
            assert not errors
            root.after(200, root.quit)
            root.mainloop()
            return int(bool(errors) or bool(app.last_diagnostic))
        finally:
            root.destroy()
