"""
songs.py - ADAPTADOR DE ENTRADA (HTTP): los 5 endpoints CRUD de canciones.

  POST   /api/v1/songs        -> crear       (201, 409 si está duplicada, 422 si datos inválidos)
  GET    /api/v1/songs        -> listar      (200)
  GET    /api/v1/songs/{id}   -> consultar   (200, 404 si no existe)
  PUT    /api/v1/songs/{id}   -> actualizar  (200, 404, 409, 422)
  DELETE /api/v1/songs/{id}   -> eliminar    (204, 404)

El router ya no tiene SQL: solo traduce HTTP <-> SongService y errores del dominio -> códigos HTTP.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import get_song_service
from app.api.schemas import ErrorResponse, SongCreate, SongOut, SongUpdate
from app.application.song_service import SongService
from app.domain.catalog.errors import DuplicateSongError, SongNotFoundError
from app.domain.catalog.song import Song

router = APIRouter(prefix="/api/v1/songs", tags=["Songs"])

NOT_FOUND = {"model": ErrorResponse, "description": "Song not found"}
CONFLICT = {
    "model": ErrorResponse,
    "description": "A song with the same title and artist already exists",
    "content": {"application/json": {"example": {"detail": "A song with this title and artist already exists"}}},
}


def to_out(song: Song) -> SongOut:
    return SongOut(id=song.id, title=song.title, artist=song.artist, album=song.album,
                   genre=song.genre, duration_seconds=song.duration_seconds)


@router.post("", response_model=SongOut, status_code=status.HTTP_201_CREATED, summary="Create a song",
             description="Adds a new song to the Enlace Sonoro catalog. Title + artist must be unique.",
             responses={409: CONFLICT})
def create_song(data: SongCreate, service: SongService = Depends(get_song_service)):
    try:
        return to_out(service.create(Song(**data.model_dump())))
    except DuplicateSongError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("", response_model=List[SongOut], summary="List songs",
            description="Returns every song in the catalog. Optionally filters by genre (case-insensitive).")
def list_songs(genre: Optional[str] = Query(None, description="Filter by genre", examples=["Rock"]),
               service: SongService = Depends(get_song_service)):
    return [to_out(s) for s in service.list(genre)]


@router.get("/{song_id}", response_model=SongOut, summary="Get a song by id",
            description="Returns a single song. Responds 404 if the id does not exist.",
            responses={404: NOT_FOUND})
def get_song(song_id: int, service: SongService = Depends(get_song_service)):
    try:
        return to_out(service.get(song_id))
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/{song_id}", response_model=SongOut, summary="Update a song",
            description="Replaces all fields of an existing song.",
            responses={404: NOT_FOUND, 409: CONFLICT})
def update_song(song_id: int, data: SongUpdate, service: SongService = Depends(get_song_service)):
    try:
        return to_out(service.update(song_id, Song(**data.model_dump())))
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DuplicateSongError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a song",
               description="Removes a song from the catalog. Responds 204 with no body.",
               responses={404: NOT_FOUND})
def delete_song(song_id: int, service: SongService = Depends(get_song_service)):
    try:
        service.delete(song_id)
    except SongNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
