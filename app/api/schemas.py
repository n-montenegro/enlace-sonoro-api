"""
schemas.py - Modelos Pydantic: definen y validan los datos que entran y salen de la API.

Las descripciones y ejemplos están en INGLÉS porque la guía exige
la documentación OpenAPI 3.0 en inglés (aparecen en Swagger UI).
"""
from typing import Optional

from pydantic import BaseModel, Field


class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, description="Song title", examples=["Bohemian Rhapsody"])
    artist: str = Field(..., min_length=1, max_length=100, description="Artist or band name", examples=["Queen"])
    album: Optional[str] = Field(None, max_length=150, description="Album name (optional)", examples=["A Night at the Opera"])
    genre: str = Field(..., min_length=1, max_length=50, description="Music genre", examples=["Rock"])
    duration_seconds: int = Field(..., gt=0, le=3600, description="Duration in seconds (1 to 3600)", examples=[354])


class SongCreate(SongBase):
    """Data required to create a song."""


class SongUpdate(SongBase):
    """Data required to fully update a song (PUT replaces every field)."""


class SongOut(SongBase):
    """Song as returned by the API, including its id."""
    id: int = Field(..., description="Unique song identifier", examples=[1])


class ErrorResponse(BaseModel):
    """Standard error body returned by the API."""
    detail: str = Field(..., examples=["Song with id 99 not found"])
