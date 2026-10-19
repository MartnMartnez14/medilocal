"""SQLite persistence, safe legacy import and atomic backup restoration."""
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .paths import data_dir, private_dir, private_file
from .validation import ValidationError, product_values, profile_values, valid_time

SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE perfiles (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 nombre TEXT NOT NULL,
 tipo TEXT NOT NULL CHECK(tipo IN ('Persona','Mascota'))
);
CREATE TABLE productos (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 perfil_id INTEGER NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
 tipo TEXT NOT NULL CHECK(tipo IN ('Medicamento','Suplemento')),
 nombre TEXT NOT NULL,
 cantidad TEXT NOT NULL,
 notas TEXT NOT NULL DEFAULT '',
 hora_original TEXT DEFAULT NULL
);
CREATE TABLE horarios (
 producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
 hora TEXT NOT NULL CHECK(length(hora)=5 AND hora GLOB '[0-2][0-9]:[0-5][0-9]' AND hora < '24:00'),
 PRIMARY KEY(producto_id, hora)
);
CREATE INDEX productos_perfil ON productos(perfil_id);
PRAGMA user_version=1;
"""
COLUMNS = {
    "perfiles": ["id", "nombre", "tipo"],
    "productos": ["id", "perfil_id", "tipo", "nombre", "cantidad", "notas", "hora_original"],
    "horarios": ["producto_id", "hora"],
}


class DataError(ValueError):
    """A safe translation key, never the contents of an SQL error."""


@contextmanager
def connect(path, readonly=False):
    path = Path(path).resolve()
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) if readonly else sqlite3.connect(path, timeout=3)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        if readonly:
            conn.execute("PRAGMA query_only=ON")
        with conn:
            yield conn
    finally:
        conn.close()


def check_source(path, legacy=False):
    """Accept only known ordinary tables. Never execute imported schema/triggers."""
    try:
        if Path(path).stat().st_size > 100 * 1024 * 1024:
            raise DataError("backup_too_large")
        with connect(path, True) as conn:
            conn.set_progress_handler(lambda: 1, 5_000_000)
            objects = conn.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            expected = {"perfiles", "productos"} if legacy else set(COLUMNS)
            tables = {r["name"] for r in objects if r["type"] == "table"}
            if tables != expected or any(r["type"] not in ("table", "index") for r in objects):
                raise DataError("invalid_backup")
            if any("VIRTUAL" in (r["sql"] or "").upper() for r in objects):
                raise DataError("invalid_backup")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version != (0 if legacy else SCHEMA_VERSION):
                raise DataError("unsupported_version")
            for table in sorted(expected):
                columns = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
                wanted = (["id", "perfil_id", "tipo", "nombre", "cantidad", "hora", "notas"]
                          if legacy and table == "productos" else COLUMNS[table])
                if columns != wanted:
                    raise DataError("invalid_backup")
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise DataError("invalid_backup")
            if conn.execute("PRAGMA foreign_key_check").fetchone():
                raise DataError("invalid_backup")
            rows = {table: [dict(r) for r in conn.execute(f"SELECT * FROM {table}")] for table in expected}
        profiles = {r["id"] for r in rows["perfiles"]}
        for p in rows["perfiles"]:
            if type(p["id"]) is not int or p["id"] < 1:
                raise DataError("invalid_backup")
            profile_values(p["nombre"], p["tipo"])
        products = {r["id"] for r in rows["productos"]}
        schedules = {pid: [] for pid in products}
        if not legacy:
            for s in rows["horarios"]:
                if s["producto_id"] not in products or not valid_time(s["hora"]):
                    raise DataError("invalid_backup")
                schedules[s["producto_id"]].append(s["hora"])
        for p in rows["productos"]:
            if type(p["id"]) is not int or p["id"] < 1 or p["perfil_id"] not in profiles:
                raise DataError("invalid_backup")
            original = p["hora"] if legacy else p["hora_original"]
            if (legacy and not isinstance(original, str)) or (original is not None and (not isinstance(original, str) or len(original) > 4000)):
                raise DataError("invalid_backup")
            schedule = ([original] if valid_time(original) else ["00:00"]) if legacy else schedules[p["id"]]
            if not schedule and original is None:
                raise DataError("invalid_backup")
            product_values(p["tipo"], p["nombre"], p["cantidad"], schedule or ["00:00"], p["notas"] or "")
        return rows
    except (sqlite3.Error, OSError, ValidationError, TypeError, KeyError) as error:
        raise DataError("invalid_backup") from error


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_dir() / "medilocal.db"
        private_dir(self.path.parent)
        if self.path.exists():
            check_source(self.path)
            private_file(self.path)
        else:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            with connect(self.path) as conn:
                conn.executescript(SCHEMA)

    def profiles(self, search=""):
        with connect(self.path) as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM perfiles ORDER BY nombre COLLATE NOCASE, id")]
        return [r for r in rows if search.casefold() in r["nombre"].casefold()]

    def save_profile(self, name, kind, profile_id=None):
        values = profile_values(name, kind)
        with connect(self.path) as conn:
            if profile_id is None:
                return conn.execute("INSERT INTO perfiles(nombre,tipo) VALUES (?,?)", values).lastrowid
            if conn.execute("UPDATE perfiles SET nombre=?,tipo=? WHERE id=?", (*values, profile_id)).rowcount != 1:
                raise DataError("not_found")
            return profile_id

    def delete_profile(self, profile_id):
        with connect(self.path) as conn:
            conn.execute("DELETE FROM perfiles WHERE id=?", (profile_id,))

    def products(self, profile_id, search=""):
        with connect(self.path) as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM productos WHERE perfil_id=?", (profile_id,))]
            for row in rows:
                row["horarios"] = [r[0] for r in conn.execute("SELECT hora FROM horarios WHERE producto_id=? ORDER BY hora", (row["id"],))]
        rows = [r for r in rows if search.casefold() in r["nombre"].casefold()]
        return sorted(rows, key=lambda r: (r["horarios"][0] if r["horarios"] else "99:99", r["nombre"].casefold(), r["id"]))

    def save_product(self, profile_id, kind, name, amount, schedule, notes="", product_id=None):
        kind, name, amount, schedule, notes = product_values(kind, name, amount, schedule, notes)
        with connect(self.path) as conn:
            if not conn.execute("SELECT 1 FROM perfiles WHERE id=?", (profile_id,)).fetchone():
                raise DataError("not_found")
            if product_id is None:
                product_id = conn.execute("INSERT INTO productos(perfil_id,tipo,nombre,cantidad,notas) VALUES (?,?,?,?,?)", (profile_id, kind, name, amount, notes)).lastrowid
            else:
                changed = conn.execute("UPDATE productos SET tipo=?,nombre=?,cantidad=?,notas=?,hora_original=NULL WHERE id=? AND perfil_id=?", (kind, name, amount, notes, product_id, profile_id)).rowcount
                if changed != 1:
                    raise DataError("not_found")
                conn.execute("DELETE FROM horarios WHERE producto_id=?", (product_id,))
            conn.executemany("INSERT INTO horarios(producto_id,hora) VALUES (?,?)", [(product_id, hour) for hour in schedule])
        return product_id

    def delete_product(self, profile_id, product_id):
        with connect(self.path) as conn:
            conn.execute("DELETE FROM productos WHERE id=? AND perfil_id=?", (product_id, profile_id))

    def backup(self, destination):
        destination = Path(destination)
        if destination.is_symlink():
            raise DataError("same_path")
        destination = destination.resolve()
        if destination == self.path.resolve() or (destination.exists() and destination.samefile(self.path)):
            raise DataError("same_path")
        # Stage in the destination filesystem, then replace atomically.
        fd, name = tempfile.mkstemp(prefix=".medilocal-", suffix=".tmp", dir=destination.parent)
        os.close(fd)
        try:
            with connect(self.path, True) as source, connect(name) as target:
                source.backup(target)
            check_source(name)
            private_file(name)
            os.replace(name, destination)
        finally:
            Path(name).unlink(missing_ok=True)

    def restore(self, source):
        source = Path(source)
        if source.resolve() == self.path.resolve():
            raise DataError("same_path")
        rows = check_source(source)
        # Rebuild with our schema, not SQL supplied by an imported file.
        fd, name = tempfile.mkstemp(prefix="restore-", suffix=".db", dir=self.path.parent)
        os.close(fd)
        try:
            with connect(name) as conn:
                conn.executescript(SCHEMA)
                for table in ("perfiles", "productos", "horarios"):
                    cols = COLUMNS[table]
                    marks = ",".join("?" for _ in cols)
                    conn.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks})", [tuple(r[c] for c in cols) for r in rows[table]])
            check_source(name)
            private_file(name)
            safety = self.path.parent / ("before-restore-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".db")
            self.backup(safety)
            os.replace(name, self.path)
            return safety
        finally:
            Path(name).unlink(missing_ok=True)

    def import_legacy(self, source):
        rows = check_source(source, legacy=True)
        with connect(self.path) as conn:
            if conn.execute("SELECT COUNT(*) FROM perfiles").fetchone()[0]:
                raise DataError("import_empty_only")
            for p in rows["perfiles"]:
                conn.execute("INSERT INTO perfiles(id,nombre,tipo) VALUES (?,?,?)", (p["id"], p["nombre"], p["tipo"]))
            for p in rows["productos"]:
                valid = valid_time(p["hora"])
                conn.execute("INSERT INTO productos(id,perfil_id,tipo,nombre,cantidad,notas,hora_original) VALUES (?,?,?,?,?,?,?)", (p["id"], p["perfil_id"], p["tipo"], p["nombre"], p["cantidad"], p["notas"] or "", None if valid else p["hora"]))
                if valid:
                    conn.execute("INSERT INTO horarios(producto_id,hora) VALUES (?,?)", (p["id"], p["hora"]))
        return len(rows["productos"])
