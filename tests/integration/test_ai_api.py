"""
test_ai_api.py - Pruebas del asistente /api/v1/ai.

No se llama al Gemini real: se INYECTA un FakeLLM en create_app().
Esto es posible gracias a la inyección de dependencias (antes había que usar monkeypatch).
"""
from fastapi.testclient import TestClient

from app.domain.recommendation.ports import LLMRateLimitError, LLMTimeoutError
from app.main import create_app
from tests.fakes import FakeLLM

SONGS = [
    {"title": "Lofi Study Session", "artist": "Chillhop Beats", "album": "Focus", "genre": "Lo-fi", "duration_seconds": 180},
    {"title": "Gasolina", "artist": "Daddy Yankee", "album": "Barrio Fino", "genre": "Reggaeton", "duration_seconds": 192},
]


def make_client(tmp_path, monkeypatch, llm):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_LOG_PATH", str(tmp_path / "calls.jsonl"))
    return TestClient(create_app(llm=llm))


def test_ai_answer_uses_catalog_context(tmp_path, monkeypatch):
    """El RAG envía al LLM la canción de estudio del catálogo y la llamada queda registrada."""
    llm = FakeLLM()
    with make_client(tmp_path, monkeypatch, llm) as client:
        for song in SONGS:
            client.post("/api/v1/songs", json=song)
        resp = client.post("/api/v1/ai", json={"question": "canciones para estudiar", "technique": "chain_of_thought"})

        assert resp.status_code == 200
        assert resp.json()["retrieved_songs"][0] == "Lofi Study Session - Chillhop Beats"
        assert "Lofi Study Session" in llm.last_prompt
        assert "step by step" in llm.last_prompt  # se usó la plantilla Chain-of-Thought
        assert len(client.get("/api/v1/ai/calls").json()) == 1


def test_ai_rate_limit_returns_429(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, FakeLLM(error=LLMRateLimitError("rate limit"))) as client:
        assert client.post("/api/v1/ai", json={"question": "music for a party"}).status_code == 429


def test_ai_timeout_returns_504(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, FakeLLM(error=LLMTimeoutError("timeout"))) as client:
        assert client.post("/api/v1/ai", json={"question": "music for a party"}).status_code == 504


def test_ai_without_api_key_returns_503(tmp_path, monkeypatch):
    """Aquí sí se usa el GeminiClient real, pero sin API key: debe responder 503 sin llamar a internet."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with make_client(tmp_path, monkeypatch, None) as client:
        assert client.post("/api/v1/ai", json={"question": "music for a party"}).status_code == 503
