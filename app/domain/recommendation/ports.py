"""
ports.py - Puertos del bounded context "Recomendación".

  LLMPort      -> cualquier modelo de lenguaje (hoy Gemini, mañana podría ser otro).
  CallLogPort  -> dónde se guarda el registro de llamadas al LLM.

También se definen los errores del LLM aquí, en el dominio, para que la capa
de aplicación pueda manejarlos sin depender de la librería httpx ni de Gemini.
"""
from abc import ABC, abstractmethod
from typing import List


class LLMError(Exception):
    """Error general al llamar al LLM."""


class LLMConfigError(LLMError):
    """Falta configurar la API key."""


class LLMTimeoutError(LLMError):
    """El LLM no respondió a tiempo."""


class LLMRateLimitError(LLMError):
    """Se superó el límite de solicitudes (HTTP 429)."""


class LLMPort(ABC):

    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo que se está usando."""

    @abstractmethod
    def ask(self, prompt: str, system_instruction: str) -> dict:
        """
        Devuelve un diccionario con:
        text, input_tokens, output_tokens, thinking_tokens, latency_ms, model
        """


class CallLogPort(ABC):

    @abstractmethod
    def save(self, entry: dict) -> None:
        """Registra una llamada al LLM."""

    @abstractmethod
    def read_all(self) -> List[dict]:
        """Devuelve todas las llamadas registradas."""
