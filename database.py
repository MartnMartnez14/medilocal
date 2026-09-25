import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "medilocal.db"


def conectar():
    """Conecta con la base de datos local."""
    return sqlite3.connect(DB_PATH)


def crear_base_datos():
    """Crea las tablas necesarias."""

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfil_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cantidad TEXT NOT NULL,
            hora TEXT NOT NULL,
            notas TEXT,
            FOREIGN KEY (perfil_id) REFERENCES perfiles(id)
        )
    """)

    conexion.commit()
    conexion.close()

    print("✓ Base de datos preparada correctamente.")


if __name__ == "__main__":
    crear_base_datos()
