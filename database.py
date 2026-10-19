"""Compatibility entry points. Data now lives in the OS user's application folder."""
import sqlite3

from medilocal.paths import data_dir
from medilocal.store import Store

DB_PATH = data_dir() / "medilocal.db"


def conectar():
    Store(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA trusted_schema=OFF")
    return conn


def crear_base_datos():
    Store(DB_PATH)


if __name__ == "__main__":
    crear_base_datos()
