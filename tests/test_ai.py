"""
test_ai.py - Pruebas del asistente /api/v1/ai.

Aquí NO se llama al Gemini real: se reemplaza ask_gemini por una función falsa (mock).
Así las pruebas no gastan cuota, no necesitan la API key y pueden correr en GitHub Actions.
"""
import pytest
from fastapi.testclient import TestClient

from app import llm_client
from app.main import app

SONGS = [
    {"title": "Lofi Study Session", "artist": "Chillhop Beats", "album": "Focus", "genre": "Lo-fi", "duration_seconds": 180},
    {"title": "Gasolina", "artist": "Daddy Yankee", "album": "Barrio Fino", "genre": "Reggaeton", "duration_seconds": 192},
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LLM_LOG_PATH", str(tmp_path / "calls.jsonl"))
    with TestClient(app) as c:
        for song in SONGS:
            c.post("/api/v1/songs", json=song)
        yield c


def test_ai_answer_uses_catalog_context(client, monkeypatch):
    """El RAG envía al LLM la canción de estudio del catálogo y la llamada queda registrada."""
    received = {}

    def fake_gemini(prompt, system_instruction):
        received["prompt"] = prompt
        return {"text": "Te recomiendo Lofi Study Session.", "input_tokens": 120, "output_tokens": 15,
                "thinking_tokens": 0, "latency_ms": 5, "model": "fake-model"}

    monkeypatch.setattr(llm_client, "ask_gemini", fake_gemini)
    resp = client.post("/api/v1/ai", json={"question": "canciones para estudiar", "technique": "chain_of_thought"})

    assert resp.status_code == 200
    assert resp.json()["retrieved_songs"][0] == "Lofi Study Session - Chillhop Beats"
    assert "Lofi Study Session" in received["prompt"]
    assert "step by step" in received["prompt"]  # se usó la plantilla Chain-of-Thought
    assert len(client.get("/api/v1/ai/calls").json()) == 1


def test_ai_rate_limit_returns_429(client, monkeypatch):
    def fake_gemini(prompt, system_instruction):
        raise llm_client.LLMRateLimitError("rate limit")

    monkeypatch.setattr(llm_client, "ask_gemini", fake_gemini)
    resp = client.post("/api/v1/ai", json={"question": "music for a party"})
    assert resp.status_code == 429


def test_ai_timeout_returns_504(client, monkeypatch):
    def fake_gemini(prompt, system_instruction):
        raise llm_client.LLMTimeoutError("timeout")

    monkeypatch.setattr(llm_client, "ask_gemini", fake_gemini)
    resp = client.post("/api/v1/ai", json={"question": "music for a party"})
    assert resp.status_code == 504


def test_ai_without_api_key_returns_503(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resp = client.post("/api/v1/ai", json={"question": "music for a party"})
    assert resp.status_code == 503
