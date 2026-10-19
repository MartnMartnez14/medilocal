import json
import tkinter as tk
import unittest

from medilocal.diagnostics import report


class DiagnosticTests(unittest.TestCase):
    def test_no_values_paths_or_source_lines(self):
        namespace = {"__name__": "medilocal.gui"}
        source = "def product_details():\n    private_name = 'PRIVATE_NAME'\n    raise ValueError('PRIVATE_MEDICATION PRIVATE_DOSE PRIVATE_NOTE /home/PRIVATE_USER/private.db')\n"
        exec(compile(source, "/home/PRIVATE_USER/private-project/gui.py", "exec"), namespace)
        try:
            namespace["product_details"]()
        except Exception as error:
            result = report(error, "details", {"language": "es", "theme": "light", "font_size": 10}, "8.6.12", "8.6.12")
        self.assertNotIn("PRIVATE", result)
        self.assertNotIn("/home", result)
        data = json.loads(result)
        self.assertEqual(data["exception"], "ValueError")
        self.assertEqual(data["frames"], [{"module": "gui.py", "function": "product_details", "line": 3}])

    def test_keyerror_values_are_allowlisted(self):
        self.assertNotIn("missing_key", json.loads(report(KeyError("PRIVATE_NAME"))))
        self.assertEqual(json.loads(report(KeyError("horarios")))["missing_key"], "horarios")

    def test_tcl_category_without_message(self):
        data = report(tk.TclError('cannot use geometry manager pack inside PRIVATE_NAME /home/PRIVATE_USER'))
        self.assertNotIn("PRIVATE", data)
        self.assertEqual(json.loads(data)["tk_category"], "geometry_conflict")

    def test_untrusted_metadata_does_not_get_serialized(self):
        error_class = type("PRIVATE_NAME", (Exception,), {})
        result = report(error_class("PRIVATE_NOTE"), "PRIVATE_ACTION", {"language": "PRIVATE_LANG", "theme": "PRIVATE_THEME", "font_size": "PRIVATE_SIZE"}, "/home/PRIVATE_USER", "PRIVATE_TCL")
        self.assertNotIn("PRIVATE", result)
        data = json.loads(result)
        self.assertEqual(data["exception"], "OtherError")
        self.assertEqual(data["action"], "callback")
        self.assertEqual(data["tk"], "unknown")
