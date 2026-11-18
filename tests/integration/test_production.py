"""
test_production.py - Pruebas de la configuración de producción (Guía 8).

- /health responde 200 si la base de datos funciona y 503 si no.
- El primer ADMIN se crea con variables de entorno (Render no tiene terminal).
- La app escoge PostgreSQL cuando existe DATABASE_URL.
"""
from fastapi.testclient import TestClient

from app.domain.identity.user import ADMIN
from app.infrastructure.persistence.postgres_song_repository import PostgresSongRepository
from app.infrastructure.persistence.postgres_user_repository import PostgresUserRepository
from app.infrastructure.persistence.sqlite_song_repository import SqliteSongRepository
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from app.main import build_repositories
from tests.helpers import make_app


def test_health_checks_the_database(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    with TestClient(make_app(tmp_path, monkeypatch)) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok", "version": "dev"}


def test_health_reports_the_deployed_version(tmp_path, monkeypatch):
    """El job DEPLOY espera hasta que Render responda con la versión (commit) recién subida."""
    monkeypatch.setenv("APP_VERSION", "96a98f6")
    with TestClient(make_app(tmp_path, monkeypatch)) as client:
        assert client.get("/health").json()["version"] == "96a98f6"


def test_health_returns_503_when_the_database_fails(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch)) as client:
        def broken():
            raise OSError("connection refused")
        monkeypatch.setattr(client.app.state.auth_service, "count_users", broken)
        resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "error", "database": "unavailable"}
    assert "connection refused" not in resp.text  # no se filtran detalles internos (OWASP API8)


def test_first_admin_is_created_from_environment_variables(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    monkeypatch.setenv("ADMIN_USERNAME", "jefe")
    monkeypatch.setenv("ADMIN_PASSWORD", "clave-del-admin-123")
    with TestClient(app) as client:  # al entrar se ejecuta el arranque (lifespan)
        resp = client.post("/api/v1/auth/login", data={"username": "jefe", "password": "clave-del-admin-123"})
        assert resp.status_code == 200
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"})
    assert me.json()["role"] == ADMIN


def test_without_admin_variables_no_user_is_created(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch)) as client:
        assert client.app.state.auth_service.count_users() == 0


def test_database_url_selects_postgresql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/enlace")
    songs, users = build_repositories()
    assert isinstance(songs, PostgresSongRepository) and isinstance(users, PostgresUserRepository)
    assert songs.database_url == users.database_url == "postgresql://user:pass@db:5432/enlace"


def test_without_database_url_sqlite_is_used(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_PATH", str(tmp_path / "local.db"))
    songs, users = build_repositories()
    assert isinstance(songs, SqliteSongRepository) and isinstance(users, SqliteUserRepository)
    assert songs.db_path == users.db_path == str(tmp_path / "local.db")
