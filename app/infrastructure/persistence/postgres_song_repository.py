"""
postgres_song_repository.py - ADAPTADOR de SongRepository con PostgreSQL (Guía 8, producción).

En producción (Render / docker-compose) la API usa PostgreSQL porque el disco de un contenedor se
borra en cada despliegue: un archivo SQLite perdería las canciones y los usuarios.
Gracias a la arquitectura hexagonal solo se agrega este adaptador; el dominio y los servicios no cambian.
"""
from typing import List, Optional

import psycopg
from psycopg.rows import dict_row

from app.domain.catalog.errors import DuplicateSongError
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song

SELECT_SONGS = "SELECT id, title, artist, album, genre, duration_seconds FROM songs"


class PostgresSongRepository(SongRepository):

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self) -> psycopg.Connection:
        # dict_row: cada fila llega como diccionario {"title": ..., "artist": ...}
        # "with conn:" hace commit al terminar sin errores (o rollback si hay excepción) y cierra la conexión
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id               SERIAL  PRIMARY KEY,
                    title            TEXT    NOT NULL,
                    artist           TEXT    NOT NULL,
                    album            TEXT,
                    genre            TEXT    NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    UNIQUE (title, artist)
                )
                """
            )

    def add(self, song: Song) -> Song:
        try:
            with self._connect() as conn:
                # RETURNING id: PostgreSQL devuelve el id generado en la misma consulta
                row = conn.execute(
                    "INSERT INTO songs (title, artist, album, genre, duration_seconds) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (song.title, song.artist, song.album, song.genre, song.duration_seconds),
                ).fetchone()
        except psycopg.errors.UniqueViolation:
            raise DuplicateSongError()
        song.id = row["id"]
        return song

    def get(self, song_id: int) -> Optional[Song]:
        with self._connect() as conn:
            row = conn.execute(SELECT_SONGS + " WHERE id = %s", (song_id,)).fetchone()
        return Song(**row) if row else None

    def list(self, genre: Optional[str] = None) -> List[Song]:
        with self._connect() as conn:
            if genre:
                rows = conn.execute(SELECT_SONGS + " WHERE LOWER(genre) = LOWER(%s) ORDER BY id", (genre,)).fetchall()
            else:
                rows = conn.execute(SELECT_SONGS + " ORDER BY id").fetchall()
        return [Song(**r) for r in rows]

    def update(self, song: Song) -> Song:
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE songs SET title = %s, artist = %s, album = %s, genre = %s, duration_seconds = %s "
                    "WHERE id = %s",
                    (song.title, song.artist, song.album, song.genre, song.duration_seconds, song.id),
                )
        except psycopg.errors.UniqueViolation:
            raise DuplicateSongError()
        return song

    def delete(self, song_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM songs WHERE id = %s", (song_id,))
