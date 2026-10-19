"""Run desktop UI (default) or shared terminal UI (--cli)."""
import argparse
import sqlite3
import sys

from medilocal import __version__
from medilocal.i18n import tr
from medilocal.instance import InstanceLock
from medilocal.paths import data_dir, load_settings
from medilocal.store import DataError, Store


def main():
    parser = argparse.ArgumentParser(description="MediLocal — offline medication organizer")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--cli", action="store_true", help="Use terminal interface")
    parser.add_argument("--lang", choices=("es", "en"), help="Interface language for this session")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.smoke_test:
        from medilocal.smoke import run
        return run()
    directory = data_dir()
    language = args.lang or load_settings(directory)["language"]
    root = None
    lock = None
    try:
        if not args.cli:
            import tkinter as tk
            try:
                root = tk.Tk()
            except tk.TclError:
                notify(None, tr("startup_error", language))
                return 1
            root.withdraw()
        try:
            lock = InstanceLock(directory)
        except OSError:
            notify(root, tr("single_instance", language))
            return 1
        store = Store(directory / "medilocal.db")
        if args.cli:
            from medilocal.cli import run
            run(store, language)
        else:
            from medilocal.gui import App
            app = App(root, store)
            if args.lang:
                app.settings["language"] = args.lang
                app.build()
            root.deiconify()
            root.mainloop()
        return 0
    except (sqlite3.Error, OSError, DataError, ImportError, RuntimeError):
        notify(root, tr("startup_error", language))
        return 1
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
        if lock:
            lock.close()


def notify(root, text):
    if root is not None:
        from tkinter import messagebox
        messagebox.showerror("MediLocal", text, parent=root)
    elif sys.stderr is not None:
        print(text, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
