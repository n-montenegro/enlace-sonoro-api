"""
sqlite_song_repository.py - ADAPTADOR que implementa el puerto SongRepository con SQLite.

Es el único archivo del proyecto que escribe SQL sobre la tabla songs.
"""
import sqlite3
from typing import List, Optional

from app.domain.catalog.errors import DuplicateSongError
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song


class SqliteSongRepository(SongRepository):

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # permite leer columnas por nombre: fila["title"]
        return conn

    def init_schema(self) -> None:
        """Crea la tabla de canciones si no existe (se llama al arrancar la API)."""
        conn = self._connect()
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

    @staticmethod
    def _to_song(row: sqlite3.Row) -> Song:
        return Song(id=row["id"], title=row["title"], artist=row["artist"], album=row["album"],
                    genre=row["genre"], duration_seconds=row["duration_seconds"])

    def add(self, song: Song) -> Song:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO songs (title, artist, album, genre, duration_seconds) VALUES (?, ?, ?, ?, ?)",
                (song.title, song.artist, song.album, song.genre, song.duration_seconds),
            )
            conn.commit()
            song.id = cursor.lastrowid
            return song
        except sqlite3.IntegrityError:
            raise DuplicateSongError()
        finally:
            conn.close()

    def get(self, song_id: int) -> Optional[Song]:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
            return self._to_song(row) if row else None
        finally:
            conn.close()

    def list(self, genre: Optional[str] = None) -> List[Song]:
        conn = self._connect()
        try:
            if genre:
                rows = conn.execute("SELECT * FROM songs WHERE LOWER(genre) = LOWER(?) ORDER BY id", (genre,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM songs ORDER BY id").fetchall()
            return [self._to_song(r) for r in rows]
        finally:
            conn.close()

    def update(self, song: Song) -> Song:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE songs SET title = ?, artist = ?, album = ?, genre = ?, duration_seconds = ? WHERE id = ?",
                (song.title, song.artist, song.album, song.genre, song.duration_seconds, song.id),
            )
            conn.commit()
            return song
        except sqlite3.IntegrityError:
            raise DuplicateSongError()
        finally:
            conn.close()

    def delete(self, song_id: int) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
            conn.commit()
        finally:
            conn.close()
