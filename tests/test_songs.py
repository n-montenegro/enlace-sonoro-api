"""
test_songs.py - 3 pruebas de integración de la API de canciones.

Son "de integración" porque prueban la API completa (HTTP -> FastAPI -> SQLite)
sin simular nada. Cada prueba usa una base de datos temporal nueva.

Ejecutar: pytest -v
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

SONG = {
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "album": "A Night at the Opera",
    "genre": "Rock",
    "duration_seconds": 354,
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Cada prueba usa su propio archivo .db temporal
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:  # el "with" ejecuta init_db()
        yield c


def test_full_crud_lifecycle(client):
    """Prueba 1: crear -> consultar -> listar -> actualizar -> eliminar -> 404."""
    # Crear
    resp = client.post("/api/v1/songs", json=SONG)
    assert resp.status_code == 201
    song_id = resp.json()["id"]

    # Consultar
    resp = client.get(f"/api/v1/songs/{song_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Bohemian Rhapsody"

    # Listar
    resp = client.get("/api/v1/songs")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Actualizar
    updated = {**SONG, "genre": "Progressive Rock"}
    resp = client.put(f"/api/v1/songs/{song_id}", json=updated)
    assert resp.status_code == 200
    assert resp.json()["genre"] == "Progressive Rock"

    # Eliminar
    resp = client.delete(f"/api/v1/songs/{song_id}")
    assert resp.status_code == 204

    # Ya no existe
    resp = client.get(f"/api/v1/songs/{song_id}")
    assert resp.status_code == 404


def test_invalid_data_returns_422(client):
    """Prueba 2: datos inválidos (duración negativa y título vacío) -> 422."""
    bad_song = {**SONG, "title": "", "duration_seconds": -5}
    resp = client.post("/api/v1/songs", json=bad_song)
    assert resp.status_code == 422


def test_duplicate_song_returns_409(client):
    """Prueba 3: misma canción del mismo artista dos veces -> 409 Conflict."""
    assert client.post("/api/v1/songs", json=SONG).status_code == 201
    resp = client.post("/api/v1/songs", json=SONG)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]
