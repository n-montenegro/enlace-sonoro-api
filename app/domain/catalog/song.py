"""
song.py - Entidad Song del bounded context "Catálogo".

Es una clase de Python pura: no sabe nada de FastAPI, SQLite ni HTTP.
Por eso vive en la capa de DOMINIO.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    title: str
    artist: str
    genre: str
    duration_seconds: int
    album: Optional[str] = None
    id: Optional[int] = None  # lo asigna el repositorio al guardar

    def label(self) -> str:
        """Texto corto para mostrar la canción: 'Titulo - Artista'."""
        return f"{self.title} - {self.artist}"
