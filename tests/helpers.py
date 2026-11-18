"""helpers.py - Utilidades para las pruebas de integración con autenticación."""
from fastapi.testclient import TestClient

from app.main import create_app
from app.infrastructure.security.pbkdf2_hasher import Pbkdf2PasswordHasher
from tests.fakes import FakeLLM

PASSWORD = "Clave-de-prueba-123"


def make_app(tmp_path, monkeypatch, **overrides):
    """Crea la app con base de datos temporal y un hasher rápido (pocas iteraciones, solo para pruebas)."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_LOG_PATH", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("OPEN_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("JWT_SECRET", "secreto-de-pruebas-con-mas-de-32-caracteres")
    overrides.setdefault("llm", FakeLLM())
    return create_app(password_hasher=Pbkdf2PasswordHasher(iterations=1_000), **overrides)


def auth_headers(client: TestClient, username: str, role: str) -> dict:
    """Registra un usuario con el rol pedido, hace login y devuelve la cabecera Authorization."""
    client.app.state.auth_service.register(username, PASSWORD, role)
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
