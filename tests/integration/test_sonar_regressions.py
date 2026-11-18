"""
test_sonar_regressions.py - Pruebas de REGRESIÓN de los bugs que reportó SonarQube Cloud (Guía 7).

Bug 1 (Reliability, 6 issues): sqlite_song_repository.py leía cada columna con row["..."].
       Se cambió a dict(row). Estas pruebas aseguran que la conversión fila -> entidad sigue correcta,
       incluso con el álbum vacío (NULL), y lo mismo en el repositorio de usuarios.
Bug 2 (Reliability, 3 issues): las tablas del dashboard no tenían encabezados <th> (accesibilidad WCAG 2).
Hallazgos de seguridad del pipeline (2 issues): dependencias sin versiones bloqueadas e instalación
       que podía ejecutar scripts. Se verifica que el CI use el lock con hashes y --only-binary.
"""
import pathlib
import re

from fastapi.testclient import TestClient

from app.domain.catalog.song import Song
from app.domain.identity.user import User
from app.infrastructure.persistence.sqlite_song_repository import SqliteSongRepository
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from tests.fakes import FakeSource
from tests.helpers import make_app

ROOT = pathlib.Path(__file__).resolve().parents[2]


def song_repo(tmp_path):
    repo = SqliteSongRepository(str(tmp_path / "test.db"))
    repo.init_schema()
    return repo


def test_song_row_is_mapped_to_entity_with_every_field(tmp_path):
    repo = song_repo(tmp_path)
    saved = repo.add(Song(title="Snowman", artist="WYS", album="Snowman", genre="Lo-fi", duration_seconds=158))
    assert repo.get(saved.id) == Song(id=saved.id, title="Snowman", artist="WYS", album="Snowman",
                                      genre="Lo-fi", duration_seconds=158)


def test_song_without_album_keeps_none(tmp_path):
    repo = song_repo(tmp_path)
    saved = repo.add(Song(title="Take Five", artist="Brubeck", genre="Jazz", duration_seconds=324))
    assert repo.get(saved.id).album is None
    assert repo.list("jazz")[0].title == "Take Five"


def test_user_row_is_mapped_to_entity(tmp_path):
    repo = SqliteUserRepository(str(tmp_path / "test.db"))
    repo.init_schema()
    saved = repo.add(User(username="laura", password_hash="h", role="USER"))
    assert repo.get_by_username("laura") == User(id=saved.id, username="laura", password_hash="h", role="USER")
    assert repo.get_by_username("nadie") is None


def test_dashboard_tables_have_header_cells(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch, municipalities=FakeSource("m", []),
                             studies=FakeSource("d", []))) as client:
        html = client.get("/dashboard").text
    tables = re.findall(r"<table.*?</table>", html, flags=re.S)
    assert len(tables) == 3
    for table in tables:
        assert '<th scope="col">' in table


def test_ci_installs_locked_binary_dependencies():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    installs = [line for line in ci.splitlines() if "pip install" in line]
    assert installs, "the pipeline must install dependencies"
    for line in installs:
        assert "--only-binary :all:" in line and "--require-hashes" in line
    assert "--hash=sha256:" in (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")


def test_ci_actions_are_pinned_to_a_full_commit_sha():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for ref in re.findall(r"uses:\s*\S+@(\S+)", ci):
        assert re.fullmatch(r"[0-9a-f]{40}", ref), ref
