"""
test_song_service.py - Pruebas UNITARIAS de SongService con unittest.mock.

unittest.mock es el equivalente en Python de Mockito (Java):
creamos un repositorio FALSO con Mock(spec=SongRepository) y se lo inyectamos al servicio.
No se toca SQLite: solo se prueba la lógica del servicio.
"""
from unittest.mock import Mock

import pytest

from app.application.song_service import SongService
from app.domain.catalog.errors import SongNotFoundError
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song


def test_get_returns_song_from_repository():
    repo = Mock(spec=SongRepository)
    repo.get.return_value = Song(id=1, title="Snowman", artist="WYS", genre="Lo-fi", duration_seconds=158)
    service = SongService(repo)  # inyección por constructor

    song = service.get(1)

    assert song.title == "Snowman"
    repo.get.assert_called_once_with(1)


def test_get_missing_song_raises_not_found():
    repo = Mock(spec=SongRepository)
    repo.get.return_value = None
    with pytest.raises(SongNotFoundError):
        SongService(repo).get(99)


def test_delete_missing_song_never_calls_repository_delete():
    """Si la canción no existe, el servicio NO debe intentar borrar nada."""
    repo = Mock(spec=SongRepository)
    repo.get.return_value = None
    with pytest.raises(SongNotFoundError):
        SongService(repo).delete(5)
    repo.delete.assert_not_called()


def test_update_assigns_id_before_saving():
    repo = Mock(spec=SongRepository)
    repo.get.return_value = Song(id=7, title="Old", artist="A", genre="Rock", duration_seconds=100)
    repo.update.side_effect = lambda song: song
    new_data = Song(title="New", artist="A", genre="Rock", duration_seconds=120)

    result = SongService(repo).update(7, new_data)

    assert result.id == 7
    repo.update.assert_called_once()
