"""
song_service.py - Casos de uso del catálogo de canciones.

INYECCIÓN DE DEPENDENCIAS POR CONSTRUCTOR:
SongService no crea su repositorio, lo RECIBE en __init__.
No sabe si es SQLite, un mock de pruebas u otra base de datos: solo conoce el puerto SongRepository.
"""
from typing import List, Optional

from app.domain.catalog.errors import SongNotFoundError
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song


class SongService:

    def __init__(self, repository: SongRepository):
        self.repository = repository

    def create(self, song: Song) -> Song:
        return self.repository.add(song)

    def get(self, song_id: int) -> Song:
        song = self.repository.get(song_id)
        if song is None:
            raise SongNotFoundError(song_id)
        return song

    def list(self, genre: Optional[str] = None) -> List[Song]:
        return self.repository.list(genre)

    def update(self, song_id: int, data: Song) -> Song:
        self.get(song_id)  # lanza SongNotFoundError si no existe
        data.id = song_id
        return self.repository.update(data)

    def delete(self, song_id: int) -> None:
        self.get(song_id)
        self.repository.delete(song_id)
