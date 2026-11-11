"""
recommendation_service.py - Caso de uso: pedirle una recomendación al asistente musical.

Recibe por CONSTRUCTOR sus 3 dependencias (todas son puertos del dominio):
  - songs:    repositorio del catálogo (para el RAG)
  - llm:      el modelo de lenguaje
  - call_log: dónde se registran las llamadas

Flujo:
  1. RAG: recupera canciones del catálogo relacionadas con la pregunta.
  2. Arma el prompt con la técnica elegida.
  3. Llama al LLM.
  4. Registra la llamada (también las fallidas) y devuelve el resultado.
"""
from typing import List

from app.domain.catalog.ports import SongRepository
from app.domain.recommendation.ports import (CallLogPort, LLMConfigError, LLMError,
                                             LLMPort, LLMRateLimitError, LLMTimeoutError)
from app.domain.recommendation.prompts import SYSTEM_INSTRUCTION, build_prompt
from app.domain.recommendation.rag import build_context, retrieve_songs


class RecommendationService:

    def __init__(self, songs: SongRepository, llm: LLMPort, call_log: CallLogPort):
        self.songs = songs
        self.llm = llm
        self.call_log = call_log

    def ask(self, question: str, technique: str) -> dict:
        retrieved = retrieve_songs(question, self.songs.list())
        prompt = build_prompt(technique, question, build_context(retrieved))
        labels = [s.label() for s in retrieved]
        base_log = {"technique": technique, "question": question,
                    "model": self.llm.model_name(), "retrieved_songs": labels}

        try:
            result = self.llm.ask(prompt, SYSTEM_INSTRUCTION)
        except LLMConfigError:
            raise  # sin API key no hubo llamada real, no se registra
        except LLMRateLimitError as exc:
            self.call_log.save({**base_log, "status": 429, "error": str(exc)})
            raise
        except LLMTimeoutError as exc:
            self.call_log.save({**base_log, "status": 504, "error": str(exc)})
            raise
        except LLMError as exc:
            self.call_log.save({**base_log, "status": 502, "error": str(exc)})
            raise

        self.call_log.save({**base_log, "status": 200, "answer": result["text"],
                            "input_tokens": result["input_tokens"], "output_tokens": result["output_tokens"],
                            "thinking_tokens": result["thinking_tokens"], "latency_ms": result["latency_ms"]})
        return {"answer": result["text"], "technique": technique, "model": result["model"],
                "retrieved_songs": labels, "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"] + result["thinking_tokens"],
                "latency_ms": result["latency_ms"]}

    def calls(self) -> List[dict]:
        return self.call_log.read_all()
