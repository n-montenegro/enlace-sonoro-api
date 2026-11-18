"""
test_auth_api.py - Pruebas de JWT + RBAC y de los controles OWASP API Security Top 10 2023.

Cada prueba indica qué control verifica (API1, API2...).
"""
from fastapi.testclient import TestClient

from tests.helpers import PASSWORD, auth_headers, make_app

SONG = {"title": "Snowman", "artist": "WYS", "album": "Snowman", "genre": "Lo-fi", "duration_seconds": 158}


def client_for(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


# ---------- los 3 endpoints de prueba: login, USER y ADMIN ----------

def test_login_returns_bearer_token(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        client.app.state.auth_service.register("laura", PASSWORD, "USER")
        resp = client.post("/api/v1/auth/login", data={"username": "laura", "password": PASSWORD})
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"].count(".") == 2  # un JWT tiene 3 partes: header.payload.firma


def test_user_endpoint_returns_own_profile(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        resp = client.get("/api/v1/auth/me", headers=auth_headers(client, "laura", "USER"))
    assert resp.status_code == 200
    assert resp.json() == {"username": "laura", "role": "USER"}


def test_admin_endpoint_rejects_user_and_accepts_admin(tmp_path, monkeypatch):
    """API5 - Broken Function Level Authorization."""
    with client_for(tmp_path, monkeypatch) as client:
        user = auth_headers(client, "laura", "USER")
        admin = auth_headers(client, "admin", "ADMIN")
        assert client.get("/api/v1/admin/stats", headers=user).status_code == 403
        resp = client.get("/api/v1/admin/stats", headers=admin)
    assert resp.status_code == 200
    assert resp.json()["users"] == 2


# ---------- API2 - Broken Authentication ----------

def test_missing_or_fake_token_returns_401(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer inventado.x.y"}).status_code == 401
        assert client.get("/api/v1/songs").status_code == 401


def test_wrong_password_and_unknown_user_get_the_same_message(tmp_path, monkeypatch):
    """No se revela qué usuarios existen (evita enumeración de usuarios)."""
    with client_for(tmp_path, monkeypatch) as client:
        client.app.state.auth_service.register("laura", PASSWORD, "USER")
        wrong_pass = client.post("/api/v1/auth/login", data={"username": "laura", "password": "otra-clave-123"})
        no_user = client.post("/api/v1/auth/login", data={"username": "nadie", "password": "otra-clave-123"})
    assert wrong_pass.status_code == no_user.status_code == 401
    assert wrong_pass.json() == no_user.json()


def test_login_is_rate_limited(tmp_path, monkeypatch):
    """API4 - después de 5 intentos por minuto se bloquea (fuerza bruta)."""
    with client_for(tmp_path, monkeypatch) as client:
        codes = [client.post("/api/v1/auth/login", data={"username": "laura", "password": "x" * 8}).status_code
                 for _ in range(6)]
    assert codes == [401] * 5 + [429]


# ---------- API3 - Broken Object Property Level Authorization ----------

def test_register_cannot_choose_role(tmp_path, monkeypatch):
    """Si alguien intenta registrarse como ADMIN, la petición se rechaza (mass assignment)."""
    with client_for(tmp_path, monkeypatch) as client:
        resp = client.post("/api/v1/auth/register", json={"username": "hacker", "password": PASSWORD, "role": "ADMIN"})
        assert resp.status_code == 422
        ok = client.post("/api/v1/auth/register", json={"username": "laura", "password": PASSWORD})
    assert ok.status_code == 201
    assert ok.json() == {"username": "laura", "role": "USER"}  # sin password_hash


def test_weak_password_is_rejected(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        resp = client.post("/api/v1/auth/register", json={"username": "laura", "password": "123"})
    assert resp.status_code == 422


# ---------- RBAC sobre el catálogo ----------

def test_user_can_read_but_not_modify_the_catalog(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        admin = auth_headers(client, "admin", "ADMIN")
        user = auth_headers(client, "laura", "USER")
        song_id = client.post("/api/v1/songs", json=SONG, headers=admin).json()["id"]

        assert client.get("/api/v1/songs", headers=user).status_code == 200
        assert client.post("/api/v1/songs", json=SONG, headers=user).status_code == 403
        assert client.put(f"/api/v1/songs/{song_id}", json=SONG, headers=user).status_code == 403
        assert client.delete(f"/api/v1/songs/{song_id}", headers=user).status_code == 403


# ---------- API8 - Security Misconfiguration ----------

def test_security_headers_are_present(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_cors_only_allows_known_origins(tmp_path, monkeypatch):
    with client_for(tmp_path, monkeypatch) as client:
        good = client.options("/api/v1/songs", headers={"Origin": "http://localhost:8000",
                                                         "Access-Control-Request-Method": "GET"})
        bad = client.options("/api/v1/songs", headers={"Origin": "https://sitio-malicioso.com",
                                                        "Access-Control-Request-Method": "GET"})
    assert good.headers.get("access-control-allow-origin") == "http://localhost:8000"
    assert "access-control-allow-origin" not in bad.headers


def test_docs_can_be_disabled_in_production(tmp_path, monkeypatch):
    """API9 - en producción la documentación interna se puede ocultar."""
    monkeypatch.setenv("ENABLE_DOCS", "false")
    with client_for(tmp_path, monkeypatch) as client:
        assert client.get("/docs").status_code == 404
