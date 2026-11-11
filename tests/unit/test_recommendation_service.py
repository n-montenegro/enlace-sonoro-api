"""
test_recommendation_service.py - Pruebas UNITARIAS de RecommendationService con unittest.mock.

Se inyectan 3 mocks (repositorio, LLM y registro) para comprobar el comportamiento
sin base de datos, sin internet y sin gastar cuota de Gemini.
"""
from unittest.mock import Mock

import pytest

from app.application.recommendation_service import RecommendationService
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song
from app.domain.recommendation.ports import CallLogPort, LLMConfigError, LLMPort, LLMRateLimitError

CATALOG = [
    Song(id=1, title="Lofi Study Session", artist="Chillhop Beats", genre="Lo-fi", duration_seconds=180),
    Song(id=2, title="Gasolina", artist="Daddy Yankee", genre="Reggaeton", duration_seconds=192),
]


def build(llm_result=None, llm_error=None):
    repo = Mock(spec=SongRepository)
    repo.list.return_value = CATALOG
    llm = Mock(spec=LLMPort)
    llm.model_name.return_value = "mock-model"
    if llm_error:
        llm.ask.side_effect = llm_error
    else:
        llm.ask.return_value = llm_result
    log = Mock(spec=CallLogPort)
    return RecommendationService(repo, llm, log), llm, log


def test_successful_answer_is_logged_with_status_200():
    result = {"text": "Escucha Lofi Study Session", "input_tokens": 100, "output_tokens": 20,
              "thinking_tokens": 5, "latency_ms": 900, "model": "mock-model"}
    service, llm, log = build(llm_result=result)

    answer = service.ask("musica para estudiar", "zero_shot")

    assert answer["retrieved_songs"][0] == "Lofi Study Session - Chillhop Beats"
    assert answer["output_tokens"] == 25  # salida + thinking tokens
    prompt_sent = llm.ask.call_args.args[0]
    assert "Lofi Study Session" in prompt_sent
    assert log.save.call_args.args[0]["status"] == 200


def test_rate_limit_is_logged_and_re_raised():
    service, _, log = build(llm_error=LLMRateLimitError("429"))
    with pytest.raises(LLMRateLimitError):
        service.ask("party music", "few_shot")
    assert log.save.call_args.args[0]["status"] == 429


def test_missing_api_key_is_not_logged():
    service, _, log = build(llm_error=LLMConfigError("no key"))
    with pytest.raises(LLMConfigError):
        service.ask("party music", "few_shot")
    log.save.assert_not_called()
