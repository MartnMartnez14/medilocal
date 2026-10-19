"""Allowlisted diagnostics: no exception messages, locals, source lines or paths."""
import json
import platform
import re
import sqlite3
import sys

from . import __version__

MODULES = {
    "app": "app.py", "__main__": "app.py",
    "medilocal.gui": "gui.py", "medilocal.store": "store.py",
    "medilocal.validation": "validation.py", "medilocal.i18n": "i18n.py",
    "medilocal.paths": "paths.py", "medilocal.diagnostics": "diagnostics.py",
    "tkinter": "tkinter", "tkinter.ttk": "ttk",
}
ACTIONS = {"details", "edit_product", "add_product", "new_profile", "edit_profile",
           "open_profile", "delete_product", "delete_profile", "backups", "export",
           "restore", "import_legacy", "dialog_layout", "dialog_focus", "callback"}
ERROR_TYPES = {"KeyError", "TypeError", "ValueError", "AttributeError", "RuntimeError",
               "IndexError", "NameError", "UnboundLocalError", "TclError", "OSError",
               "PermissionError", "OperationalError", "DatabaseError", "IntegrityError"}
SAFE_KEYS = {"id", "perfil_id", "tipo", "nombre", "cantidad", "notas", "horarios",
             "hora_original", "hours_column", "language", "theme", "font_size"}


def numeric_version(value):
    return value if isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,3}", value) else "unknown"


def report(error, action="callback", settings=None, tk_version=None, tcl_version=None):
    """Return a small safe report in memory; never persist or transmit it."""
    settings = settings or {}
    frames = []
    tb = error.__traceback__
    while tb is not None:
        module = tb.tb_frame.f_globals.get("__name__")
        if module in MODULES:
            function = tb.tb_frame.f_code.co_name
            frames.append({"module": MODULES[module],
                           "function": function if re.fullmatch(r"[a-zA-Z_<>][a-zA-Z_0-9<>]*", function) else "callback",
                           "line": tb.tb_lineno})
        tb = tb.tb_next
    name = type(error).__name__
    result = {
        "diagnostic": "ML-DIAG-1", "version": __version__,
        "action": action if action in ACTIONS else "callback",
        "exception": name if name in ERROR_TYPES else "OtherError",
        "platform": sys.platform if sys.platform in ("linux", "win32", "darwin") else "other",
        "packaged": bool(getattr(sys, "frozen", False)),
        "python": numeric_version(platform.python_version()),
        "sqlite": numeric_version(sqlite3.sqlite_version),
        "tk": numeric_version(tk_version), "tcl": numeric_version(tcl_version),
        "language": settings.get("language") if settings.get("language") in ("es", "en") else "unknown",
        "theme": settings.get("theme") if settings.get("theme") in ("dark", "light") else "unknown",
        "font_size": settings.get("font_size") if type(settings.get("font_size")) is int and 10 <= settings["font_size"] <= 20 else None,
        "frames": frames[-12:],
    }
    if isinstance(error, KeyError) and len(error.args) == 1 and isinstance(error.args[0], str) and error.args[0] in SAFE_KEYS:
        result["missing_key"] = error.args[0]
    # Match known technical categories locally; never export the original text.
    if name == "TclError":
        message = str(error)
        patterns = {"geometry_conflict": "cannot use geometry manager", "window_not_viewable": "window not viewable",
                    "grab_failed": "grab failed", "invalid_widget": "bad window path name",
                    "invalid_command": "invalid command name", "unknown_option": "unknown option"}
        result["tk_category"] = next((code for code, marker in patterns.items() if marker in message), "other")
    return json.dumps(result, indent=2, ensure_ascii=True)
