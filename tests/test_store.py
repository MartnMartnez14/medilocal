import hashlib
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from medilocal.i18n import STRINGS, tr
from medilocal.instance import InstanceLock
from medilocal.paths import load_settings, save_settings
from medilocal.store import DataError, Store, check_source, connect
from medilocal.validation import ValidationError, times


def legacy(path, hour="08:00", orphan=False):
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executescript("""
        CREATE TABLE perfiles(id INTEGER PRIMARY KEY AUTOINCREMENT,nombre TEXT NOT NULL,tipo TEXT NOT NULL);
        CREATE TABLE productos(id INTEGER PRIMARY KEY AUTOINCREMENT,perfil_id INTEGER NOT NULL,tipo TEXT NOT NULL,nombre TEXT NOT NULL,cantidad TEXT NOT NULL,hora TEXT NOT NULL,notas TEXT,FOREIGN KEY(perfil_id) REFERENCES perfiles(id));
        INSERT INTO perfiles VALUES(1,'Perfil ficticio','Persona');
        """)
        conn.execute("INSERT INTO productos VALUES(1,?,'Medicamento','Ejemplo','Texto ficticio',?,NULL)", (999 if orphan else 1, hour))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.store = Store(self.directory / "app" / "medilocal.db")
        self.profile = self.store.save_profile("Perfil ficticio", "Persona")

    def add(self, profile=None, **kw):
        args = dict(kind="Medicamento", name="Ejemplo", amount="Indicación ficticia", schedule="20:00, 08:00, 08:00", notes="Nota ficticia")
        args.update(kw)
        return self.store.save_product(profile or self.profile, **args)

    def test_profile_crud_search_unicode(self):
        self.store.save_profile("Ángela", "Mascota", self.profile)
        self.assertEqual(self.store.profiles("ÁNG")[0]["tipo"], "Mascota")
        self.store.delete_profile(self.profile)
        self.assertEqual(self.store.profiles(), [])

    def test_product_multitime_sort_and_edit(self):
        pid = self.add()
        self.assertEqual(self.store.products(self.profile)[0]["horarios"], ["08:00", "20:00"])
        self.add(name="Primero", schedule="06:30")
        self.assertEqual(self.store.products(self.profile)[0]["nombre"], "Primero")
        self.add(product_id=pid, notes="", schedule="10:00")
        edited = self.store.products(self.profile, "Ejemplo")[0]
        self.assertEqual(edited["horarios"], ["10:00"])
        self.assertEqual(edited["notas"], "")

    def test_isolation(self):
        other = self.store.save_profile("Otro ficticio", "Mascota")
        pid = self.add()
        self.store.delete_product(other, pid)
        with self.assertRaises(DataError):
            self.add(profile=other, product_id=pid)
        self.assertEqual(len(self.store.products(self.profile)), 1)
        self.assertEqual(self.store.products(other), [])

    def test_cascade(self):
        self.add()
        self.store.delete_profile(self.profile)
        with connect(self.store.path) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM horarios").fetchone()[0], 0)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO horarios VALUES (999,'10:00')")

    def test_no_interpretation_of_dose_and_sql_parameterization(self):
        self.add(name="'); DROP TABLE perfiles;--", amount="Consultar indicación escrita; no calcular")
        self.assertEqual(len(self.store.profiles()), 1)
        self.assertIn("no calcular", self.store.products(self.profile)[0]["cantidad"])

    def test_invalid_times(self):
        for value in ("24:00", "8:00", "12:60", "", "-1:00", "08:00,", "０８:００", None, ["08:00", 1]):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                times(value)
        self.assertEqual(times("00:00,23:59"), ["00:00", "23:59"])

    def test_required_and_limits(self):
        for changes in ({"name": " "}, {"amount": ""}, {"name": "a"*201}, {"notes": "x"*4001}, {"kind": "Other"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.add(**changes)
        with self.assertRaises(ValidationError):
            self.store.save_profile("", "Persona")

    def test_failed_edit_is_atomic(self):
        pid = self.add()
        before = self.store.products(self.profile)
        with self.assertRaises(ValidationError):
            self.add(product_id=pid, schedule="25:00")
        self.assertEqual(self.store.products(self.profile), before)

    def test_backup_restore_and_safety_copy(self):
        self.add()
        backup = self.directory / "backup.db"
        self.store.backup(backup)
        expected = self.store.products(self.profile)
        self.store.delete_profile(self.profile)
        safety = self.store.restore(backup)
        self.assertEqual(self.store.products(self.profile), expected)
        self.assertEqual(check_source(safety)["perfiles"], [])
        self.assertEqual(len(Store(self.store.path).products(self.profile)), 1)

    def test_reject_bad_backups_without_modifying_current(self):
        self.add()
        expected = self.store.path.read_bytes()
        bad = self.directory / "bad.db"
        bad.write_bytes(b"not sqlite")
        with self.assertRaises(DataError):
            self.store.restore(bad)
        self.assertEqual(expected, self.store.path.read_bytes())

    def test_reject_version(self):
        source = self.directory / "future.db"
        self.store.backup(source)
        with closing(sqlite3.connect(source)) as conn, conn:
            conn.execute("PRAGMA user_version=999")
        with self.assertRaisesRegex(DataError, "unsupported_version"):
            self.store.restore(source)

    def test_reject_triggers(self):
        source = self.directory / "trigger.db"
        self.store.backup(source)
        with closing(sqlite3.connect(source)) as conn, conn:
            conn.execute("CREATE TRIGGER injected AFTER INSERT ON perfiles BEGIN DELETE FROM productos; END")
        with self.assertRaises(DataError):
            self.store.restore(source)

    def test_reject_orphan_even_without_fk_declaration(self):
        source = self.directory / "orphan.db"
        self.store.backup(source)
        with closing(sqlite3.connect(source)) as conn, conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("INSERT INTO productos(perfil_id,tipo,nombre,cantidad) VALUES (99,'Medicamento','Ficticio','Texto')")
        with self.assertRaises(DataError):
            self.store.restore(source)

    def test_same_path_and_hardlink(self):
        with self.assertRaises(DataError):
            self.store.backup(self.store.path)
        with self.assertRaises(DataError):
            self.store.restore(self.store.path)
        link = self.directory / "link.db"
        os.link(self.store.path, link)
        with self.assertRaises(DataError):
            self.store.backup(link)

    def test_backup_failed_write_preserves_existing(self):
        source = self.directory / "existing.db"
        source.write_bytes(b"original")
        with patch("medilocal.store.os.replace", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.store.backup(source)
        self.assertEqual(source.read_bytes(), b"original")

    def test_restore_failed_replace_keeps_current(self):
        self.add()
        source = self.directory / "backup.db"
        self.store.backup(source)
        self.store.save_profile("Cambio ficticio", "Persona", self.profile)
        expected = self.store.profiles()
        original_replace = os.replace
        def fail_restore(src, dest):
            if Path(dest) == self.store.path:
                raise PermissionError
            return original_replace(src, dest)
        with patch("medilocal.store.os.replace", side_effect=fail_restore):
            with self.assertRaises(PermissionError):
                self.store.restore(source)
        self.assertEqual(self.store.profiles(), expected)
        self.assertEqual(len(list(self.store.path.parent.glob("before-restore-*.db"))), 1)

    def test_restore_safety_failure_keeps_current(self):
        source = self.directory / "backup.db"
        self.store.backup(source)
        before = self.store.profiles()
        with patch.object(self.store, "backup", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.store.restore(source)
        self.assertEqual(self.store.profiles(), before)

    def test_legacy_migration_keeps_original_and_ids(self):
        source = self.directory / "old.db"
        legacy(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = Store(self.directory / "new" / "medilocal.db")
        self.assertEqual(target.import_legacy(source), 1)
        self.assertEqual(target.products(1)[0]["horarios"], ["08:00"])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)

    def test_legacy_invalid_hours_preserved_including_empty(self):
        for index, hour in enumerate(("a la noche", "25:90", "")):
            source = self.directory / f"old{index}.db"
            legacy(source, hour)
            target = Store(self.directory / f"new{index}" / "medilocal.db")
            target.import_legacy(source)
            row = Store(target.path).products(1)[0]
            self.assertEqual(row["hora_original"], hour)
            self.assertEqual(row["horarios"], [])
            target.save_product(1, row["tipo"], row["nombre"], row["cantidad"], "10:00", product_id=row["id"])
            self.assertIsNone(target.products(1)[0]["hora_original"])

    def test_legacy_nonempty_target_rejected(self):
        source = self.directory / "old.db"
        legacy(source)
        with self.assertRaisesRegex(DataError, "import_empty_only"):
            self.store.import_legacy(source)

    def test_legacy_orphans_rejected(self):
        source = self.directory / "old.db"
        legacy(source, orphan=True)
        with self.assertRaises(DataError):
            check_source(source, True)

    def test_import_not_requested_does_not_touch_source(self):
        source = self.directory / "old.db"
        legacy(source)
        before = source.read_bytes()
        target = Store(self.directory / "new" / "medilocal.db")
        self.assertEqual(target.profiles(), [])
        self.assertEqual(source.read_bytes(), before)

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_private_permissions(self):
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.store.path.parent.stat().st_mode & 0o777, 0o700)
        target = self.directory / "backup.db"
        self.store.backup(target)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_preferences_persistence_and_invalid_fallback(self):
        settings = {"language": "en", "theme": "light", "font_size": 16}
        save_settings(settings, self.directory)
        self.assertEqual(load_settings(self.directory), settings)
        (self.directory / "settings.json").write_text('{"language":"xx","font_size":999,"theme":"red"}')
        self.assertEqual(load_settings(self.directory), {"language": "es", "theme": "dark", "font_size": 12})
        (self.directory / "settings.json").write_text("[]")
        self.assertEqual(load_settings(self.directory)["language"], "es")

    def test_single_instance_lock_released(self):
        first = InstanceLock(self.directory)
        try:
            with self.assertRaises(OSError):
                InstanceLock(self.directory)
        finally:
            first.close()
        InstanceLock(self.directory).close()

    def test_translations_have_matching_placeholders(self):
        import string
        for key, values in STRINGS.items():
            with self.subTest(key=key):
                fields = [{v for _, v, _, _ in string.Formatter().parse(s) if v} for s in values]
                self.assertEqual(fields[0], fields[1])
                for lang in ("es", "en"):
                    self.assertTrue(tr(key, lang, **{f: "X" for f in fields[0]}))


if __name__ == "__main__":
    unittest.main()
