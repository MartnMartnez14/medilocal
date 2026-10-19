"""Opt-in native UI checks; all databases are temporary and fictitious."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(os.environ.get("MEDILOCAL_GUI_TESTS") == "1", "Set MEDILOCAL_GUI_TESTS=1 with a display")
class GuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from medilocal.gui import App
        from medilocal.store import Store
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.store = Store(Path(self.temp.name) / "medilocal.db")
        self.profile = self.store.save_profile("Ana · Ejemplo", "Persona")
        self.pid = self.store.save_product(self.profile, "Medicamento", "Producto ficticio", "Indicación de ejemplo", "08:00,20:00", "Datos ficticios; sin recomendaciones.")
        self.app = App(self.root, self.store)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.root.update()

    def test_all_themes_languages_screens(self):
        for language in ("es", "en"):
            for theme in ("dark", "light"):
                self.app.change_setting("language", language)
                self.app.change_setting("theme", theme)
                for screen in ("profiles", "products", "backups"):
                    self.app.profile_id = self.profile
                    self.app.show(screen)
                    self.root.update()
                    self.assertEqual(self.app.screen, screen)
        self.assertEqual(self.errors, [])

    def test_open_profile_forms_details_and_escape(self):
        self.app.tree.selection_set(str(self.profile))
        self.app.open_selected()
        self.app.tree.selection_set(str(self.pid))
        for method in (self.app.product_details, self.app.edit_product, self.app.profile_form):
            method()
            self.root.update()
            dialogs = [w for w in self.root.winfo_children() if w.winfo_class() == "Toplevel"]
            self.assertEqual(len(dialogs), 1)
            dialogs[0].destroy()
            self.root.update()
        self.assertEqual(self.errors, [])

    def test_cancel_file_dialogs_and_confirmations(self):
        before = self.store.products(self.profile)
        with patch("medilocal.gui.filedialog.askopenfilename", return_value=""), patch("medilocal.gui.filedialog.asksaveasfilename", return_value=""):
            self.app.export()
            self.app.restore()
            self.app.import_legacy()
        self.app.tree.selection_set(str(self.profile))
        with patch("medilocal.gui.messagebox.askyesno", return_value=False):
            self.app.delete_profile()
        self.assertEqual(self.store.products(self.profile), before)

    def test_text_size_and_preferences_survive_restart(self):
        from medilocal.paths import load_settings
        self.app.change_setting("language", "en")
        self.app.change_setting("theme", "light")
        self.app.change_setting("font_size", 20)
        self.root.update()
        self.assertEqual(load_settings(self.store.path.parent), {"language": "en", "theme": "light", "font_size": 20})
        self.app.profile_form()
        self.root.update()
        self.assertEqual(self.errors, [])

    def test_form_validation_and_save_real_widgets(self):
        from tkinter import ttk
        self.app.profile_id = self.profile
        self.app.show("products")
        self.app.product_form()
        self.root.update()
        dialog = next(w for w in self.root.winfo_children() if w.winfo_class() == "Toplevel")
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        fields = [w for w in descendants(dialog) if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
        self.assertEqual(len(fields), 3)
        for entry, value in zip(fields, ("Otro ficticio", "Texto ficticio", "25:00")):
            entry.insert(0, value)
        save = next(w for w in descendants(dialog) if isinstance(w, ttk.Button) and w.cget("text") == self.app.t("save"))
        save.invoke()
        self.root.update()
        self.assertEqual(len(self.store.products(self.profile)), 1)
        fields[2].delete(0, "end")
        fields[2].insert(0, "07:30, 19:30")
        save.invoke()
        self.root.update()
        self.assertEqual(len(self.store.products(self.profile)), 2)
        self.assertEqual(self.store.products(self.profile)[0]["horarios"], ["07:30", "19:30"])
        self.assertEqual(self.errors, [])

    def test_details_failure_cleans_up_and_diagnostic_is_copyable(self):
        from medilocal.smoke import invoke, widgets
        from tkinter import ttk
        self.app.profile_id = self.profile
        self.app.show("products")
        self.app.tree.selection_set(str(self.pid))
        before = self.store.products(self.profile)
        # An intentional cache fault tests recovery; it is not the confirmed user cause.
        del self.app.rows[str(self.pid)]["hora_original"]
        self.app.run_action(self.app.product_details, "details")
        self.root.update()
        self.assertEqual(self.app.dialog_windows, set())
        self.assertIsNone(self.root.grab_current())
        self.assertIn('"exception": "KeyError"', self.app.last_diagnostic)
        self.assertIn('"missing_key": "hora_original"', self.app.last_diagnostic)
        self.assertNotIn("Producto ficticio", self.app.last_diagnostic)
        self.assertNotIn("Ana", self.app.last_diagnostic)
        self.assertNotIn(str(self.store.path.parent), self.app.last_diagnostic)
        self.assertTrue(self.app.error_window.winfo_exists())
        invoke(self.app, self.app.error_window, "copy_diagnostic")
        self.root.update()
        self.assertEqual(self.root.clipboard_get(), self.app.last_diagnostic)
        invoke(self.app, self.app.error_window, "close")
        self.app.refresh()
        self.app.tree.selection_set(str(self.pid))
        self.app.product_details()
        self.root.update()
        dialog = next(iter(self.app.dialog_windows))
        labels = [str(w.cget("text")) for w in widgets(dialog) if isinstance(w, ttk.Label)]
        self.assertIn("Producto ficticio", labels)
        invoke(self.app, dialog, "close")
        self.assertEqual(self.store.products(self.profile), before)
        self.assertEqual(self.errors, [])

    def test_real_details_routes_for_supplement_in_all_preferences(self):
        from medilocal.smoke import exercise_details
        product = self.store.save_product(self.profile, "Suplemento", "Example supplement", "Fictitious instruction", "09:00,21:00")
        for language in ("es", "en"):
            self.app.change_setting("language", language)
            for theme in ("dark", "light"):
                self.app.change_setting("theme", theme)
                self.app.profile_id = self.profile
                self.app.show("products")
                self.root.update()
                exercise_details(self.app, self.root, product)
        self.assertEqual(self.errors, [])


if __name__ == "__main__":
    unittest.main()
