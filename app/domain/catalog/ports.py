"""
ports.py - PUERTO de salida del catálogo.

Un puerto es una interfaz: dice QUÉ necesita el dominio, no CÓMO se hace.
La implementación real (SQLite) está en infrastructure/persistence.
Gracias a esto, en las pruebas podemos reemplazar la base de datos por un mock.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.catalog.song import Song


class SongRepository(ABC):

    @abstractmethod
    def add(self, song: Song) -> Song:
        """Guarda la canción y la devuelve con su id. Lanza DuplicateSongError si ya existe."""

    @abstractmethod
    def get(self, song_id: int) -> Optional[Song]:
        """Devuelve la canción o None si no existe."""

    @abstractmethod
    def list(self, genre: Optional[str] = None) -> List[Song]:
        """Lista las canciones, opcionalmente filtradas por género."""

    @abstractmethod
    def update(self, song: Song) -> Song:
        """Reemplaza todos los campos. Lanza DuplicateSongError si choca con otra canción."""

    @abstractmethod
    def delete(self, song_id: int) -> None:
        """Elimina la canción."""
