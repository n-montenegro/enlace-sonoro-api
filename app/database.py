"""
database.py - Conexión a SQLite para Enlace Sonoro.

Usamos sqlite3 (viene incluido en Python, no hay que instalar nada).
La ruta de la base de datos se lee de la variable de entorno DB_PATH;
así las pruebas pueden usar una base de datos temporal distinta.
"""
import os
import sqlite3


def get_db_path() -> str:
    # Si no existe la variable de entorno, usamos el archivo por defecto
    return os.getenv("DB_PATH", "enlace_sonoro.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # permite leer columnas por nombre: fila["title"]
    return conn


def init_db() -> None:
    """Crea la tabla de canciones si no existe."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT    NOT NULL,
            artist           TEXT    NOT NULL,
            album            TEXT,
            genre            TEXT    NOT NULL,
            duration_seconds INTEGER NOT NULL,
            UNIQUE (title, artist)  -- no se permite la misma canción del mismo artista dos veces
        )
        """
    )
    conn.commit()
    conn.close()
