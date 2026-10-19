import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from medilocal.cli import run
from medilocal.store import Store


class CliTests(unittest.TestCase):
    def test_create_profile_product_edit_and_exit_in_english(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "medilocal.db")
            inputs = iter(["2", "Example", "1", "3", "1", "2", "1", "Example entry", "Fictitious instruction", "08:00,20:00", "Example note", "3", "1", "2", "Edited example", "Fictitious instruction", "09:00", "", "0", "0"])
            with patch("builtins.input", side_effect=lambda _: next(inputs)), redirect_stdout(io.StringIO()):
                run(store, "en")
            row = store.products(1)[0]
            self.assertEqual(row["nombre"], "Edited example")
            self.assertEqual(row["tipo"], "Suplemento")
            self.assertEqual(row["horarios"], ["09:00"])
            self.assertEqual(row["notas"], "")

    def test_cancel_delete_and_exit_on_eof(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "medilocal.db")
            store.save_profile("Ejemplo", "Persona")
            with patch("builtins.input", side_effect=["5", "1", "NO", EOFError]), redirect_stdout(io.StringIO()):
                run(store)
            self.assertEqual(len(store.profiles()), 1)
