"""
test_ai_api.py - Pruebas del asistente /api/v1/ai.

No se llama al Gemini real: se INYECTA un FakeLLM en create_app().
Desde la Guía 7 el asistente exige token y /calls solo lo ve el ADMIN.
"""
from fastapi.testclient import TestClient

from app.api.rate_limit import RateLimiter
from app.domain.recommendation.ports import LLMRateLimitError, LLMTimeoutError
from tests.fakes import FakeLLM
from tests.helpers import auth_headers, make_app

SONGS = [
    {"title": "Lofi Study Session", "artist": "Chillhop Beats", "album": "Focus", "genre": "Lo-fi", "duration_seconds": 180},
    {"title": "Gasolina", "artist": "Daddy Yankee", "album": "Barrio Fino", "genre": "Reggaeton", "duration_seconds": 192},
]


def test_ai_answer_uses_catalog_context(tmp_path, monkeypatch):
    """El RAG envía al LLM la canción de estudio del catálogo y la llamada queda registrada."""
    llm = FakeLLM()
    with TestClient(make_app(tmp_path, monkeypatch, llm=llm)) as client:
        admin = auth_headers(client, "admin", "ADMIN")
        user = auth_headers(client, "laura", "USER")
        for song in SONGS:
            client.post("/api/v1/songs", json=song, headers=admin)
        resp = client.post("/api/v1/ai", json={"question": "canciones para estudiar", "technique": "chain_of_thought"},
                           headers=user)

        assert resp.status_code == 200
        assert resp.json()["retrieved_songs"][0] == "Lofi Study Session - Chillhop Beats"
        assert "Lofi Study Session" in llm.last_prompt
        assert "step by step" in llm.last_prompt  # se usó la plantilla Chain-of-Thought
        assert len(client.get("/api/v1/ai/calls", headers=admin).json()) == 1
        assert client.get("/api/v1/ai/calls", headers=user).status_code == 403  # un USER no ve las preguntas de otros


def test_ai_requires_token(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch)) as client:
        assert client.post("/api/v1/ai", json={"question": "music for a party"}).status_code == 401


def test_ai_rate_limit_returns_429(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch, llm=FakeLLM(error=LLMRateLimitError("rate limit")))) as client:
        user = auth_headers(client, "laura", "USER")
        assert client.post("/api/v1/ai", json={"question": "music for a party"}, headers=user).status_code == 429


def test_ai_has_its_own_request_limit(tmp_path, monkeypatch):
    """Nuestro propio límite (no el de Gemini): al pasar el máximo responde 429 sin llamar al LLM."""
    llm = FakeLLM()
    with TestClient(make_app(tmp_path, monkeypatch, llm=llm)) as client:
        client.app.state.limiters["ai"] = RateLimiter(max_requests=2, window_seconds=60)
        user = auth_headers(client, "laura", "USER")
        codes = [client.post("/api/v1/ai", json={"question": "music to study"}, headers=user).status_code
                 for _ in range(3)]
    assert codes == [200, 200, 429]


def test_ai_timeout_returns_504(tmp_path, monkeypatch):
    with TestClient(make_app(tmp_path, monkeypatch, llm=FakeLLM(error=LLMTimeoutError("timeout")))) as client:
        user = auth_headers(client, "laura", "USER")
        assert client.post("/api/v1/ai", json={"question": "music for a party"}, headers=user).status_code == 504


def test_ai_without_api_key_returns_503(tmp_path, monkeypatch):
    """Aquí sí se usa el GeminiClient real, pero sin API key: debe responder 503 sin llamar a internet."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from app.infrastructure.llm.gemini_client import GeminiClient
    with TestClient(make_app(tmp_path, monkeypatch, llm=GeminiClient())) as client:
        user = auth_headers(client, "laura", "USER")
        assert client.post("/api/v1/ai", json={"question": "music for a party"}, headers=user).status_code == 503
