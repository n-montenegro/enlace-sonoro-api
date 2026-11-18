"""
test_postgres_repositories.py - Pruebas de los adaptadores PostgreSQL contra una base de datos REAL.

En GitHub Actions el job "test" levanta un contenedor de PostgreSQL y define TEST_DATABASE_URL.
En el computador local estas pruebas se SALTAN si no existe esa variable
(o se pueden correr con: docker compose up -d db  y  TEST_DATABASE_URL=postgresql://...).
"""
import os

import psycopg
import pytest

from app.domain.catalog.errors import DuplicateSongError
from app.domain.catalog.song import Song
from app.domain.identity.errors import UserAlreadyExistsError
from app.domain.identity.user import ADMIN, User
from app.infrastructure.persistence.postgres_song_repository import PostgresSongRepository
from app.infrastructure.persistence.postgres_user_repository import PostgresUserRepository

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not set (no PostgreSQL)")


@pytest.fixture
def songs():
    repo = PostgresSongRepository(DATABASE_URL)
    repo.init_schema()
    repo.init_schema()  # se puede llamar dos veces (CREATE TABLE IF NOT EXISTS)
    yield repo
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DROP TABLE songs")


@pytest.fixture
def users():
    repo = PostgresUserRepository(DATABASE_URL)
    repo.init_schema()
    yield repo
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DROP TABLE users")


def make_song(title="Tusa", artist="Karol G", album=None, genre="Reggaeton"):
    return Song(title=title, artist=artist, album=album, genre=genre, duration_seconds=200)


def test_song_crud(songs):
    created = songs.add(make_song(album="KG0516"))
    assert created.id is not None
    assert songs.get(created.id) == created

    created.title = "Tusa (Remix)"
    songs.update(created)
    assert songs.get(created.id).title == "Tusa (Remix)"

    songs.delete(created.id)
    assert songs.get(created.id) is None


def test_song_without_album_keeps_none(songs):
    created = songs.add(make_song())
    assert songs.get(created.id).album is None


def test_list_filters_by_genre_ignoring_case_and_orders_by_id(songs):
    first = songs.add(make_song("A", "X", genre="Rock"))
    songs.add(make_song("B", "Y", genre="Salsa"))
    second = songs.add(make_song("C", "Z", genre="ROCK"))
    assert [s.id for s in songs.list("rock")] == [first.id, second.id]
    assert len(songs.list()) == 3


def test_duplicate_song_is_rejected(songs):
    songs.add(make_song())
    with pytest.raises(DuplicateSongError):
        songs.add(make_song())


def test_update_to_an_existing_song_is_rejected(songs):
    songs.add(make_song("A", "X"))
    other = songs.add(make_song("B", "X"))
    other.title = "A"
    with pytest.raises(DuplicateSongError):
        songs.update(other)


def test_user_add_get_and_count(users):
    assert users.count() == 0
    created = users.add(User(username="laura", password_hash="HASH", role=ADMIN))
    assert created.id is not None
    assert users.get_by_username("laura") == created
    assert users.get_by_username("nadie") is None
    assert users.count() == 1


def test_duplicate_username_is_rejected(users):
    users.add(User(username="laura", password_hash="HASH"))
    with pytest.raises(UserAlreadyExistsError):
        users.add(User(username="laura", password_hash="OTRO"))


def test_role_must_be_valid(users):
    with pytest.raises(psycopg.errors.CheckViolation):
        users.add(User(username="pepe", password_hash="HASH", role="ROOT"))
