"""
songs.py - Los 5 endpoints CRUD de canciones.

  POST   /api/v1/songs        -> crear       (201, 409 si está duplicada, 422 si datos inválidos)
  GET    /api/v1/songs        -> listar      (200)
  GET    /api/v1/songs/{id}   -> consultar   (200, 404 si no existe)
  PUT    /api/v1/songs/{id}   -> actualizar  (200, 404, 409, 422)
  DELETE /api/v1/songs/{id}   -> eliminar    (204, 404)

El error 422 lo genera FastAPI automáticamente cuando Pydantic rechaza los datos.
"""
import sqlite3
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.database import get_connection
from app.schemas import ErrorResponse, SongCreate, SongOut, SongUpdate

router = APIRouter(prefix="/api/v1/songs", tags=["Songs"])

NOT_FOUND = {"model": ErrorResponse, "description": "Song not found"}
CONFLICT = {
    "model": ErrorResponse,
    "description": "A song with the same title and artist already exists",
    "content": {"application/json": {"example": {"detail": "A song with this title and artist already exists"}}},
}


def row_to_song(row: sqlite3.Row) -> SongOut:
    """Convierte una fila de SQLite en un objeto SongOut."""
    return SongOut(**dict(row))


def find_song_or_404(conn: sqlite3.Connection, song_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Song with id {song_id} not found")
    return row


@router.post(
    "",
    response_model=SongOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a song",
    description="Adds a new song to the Enlace Sonoro catalog. Title + artist must be unique.",
    responses={409: CONFLICT},
)
def create_song(song: SongCreate):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO songs (title, artist, album, genre, duration_seconds) VALUES (?, ?, ?, ?, ?)",
            (song.title, song.artist, song.album, song.genre, song.duration_seconds),
        )
        conn.commit()
        new_row = find_song_or_404(conn, cursor.lastrowid)
        return row_to_song(new_row)
    except sqlite3.IntegrityError:
        # Se viola la restricción UNIQUE(title, artist)
        raise HTTPException(status_code=409, detail="A song with this title and artist already exists")
    finally:
        conn.close()


@router.get(
    "",
    response_model=List[SongOut],
    summary="List songs",
    description="Returns every song in the catalog. Optionally filters by genre (case-insensitive).",
)
def list_songs(genre: Optional[str] = Query(None, description="Filter by genre", examples=["Rock"])):
    conn = get_connection()
    try:
        if genre:
            rows = conn.execute("SELECT * FROM songs WHERE LOWER(genre) = LOWER(?) ORDER BY id", (genre,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM songs ORDER BY id").fetchall()
        return [row_to_song(r) for r in rows]
    finally:
        conn.close()


@router.get(
    "/{song_id}",
    response_model=SongOut,
    summary="Get a song by id",
    description="Returns a single song. Responds 404 if the id does not exist.",
    responses={404: NOT_FOUND},
)
def get_song(song_id: int):
    conn = get_connection()
    try:
        return row_to_song(find_song_or_404(conn, song_id))
    finally:
        conn.close()


@router.put(
    "/{song_id}",
    response_model=SongOut,
    summary="Update a song",
    description="Replaces all fields of an existing song.",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def update_song(song_id: int, song: SongUpdate):
    conn = get_connection()
    try:
        find_song_or_404(conn, song_id)
        conn.execute(
            "UPDATE songs SET title = ?, artist = ?, album = ?, genre = ?, duration_seconds = ? WHERE id = ?",
            (song.title, song.artist, song.album, song.genre, song.duration_seconds, song_id),
        )
        conn.commit()
        return row_to_song(find_song_or_404(conn, song_id))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A song with this title and artist already exists")
    finally:
        conn.close()


@router.delete(
    "/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a song",
    description="Removes a song from the catalog. Responds 204 with no body.",
    responses={404: NOT_FOUND},
)
def delete_song(song_id: int):
    conn = get_connection()
    try:
        find_song_or_404(conn, song_id)
        conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    finally:
        conn.close()
