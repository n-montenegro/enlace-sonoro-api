"""
http_source.py - Base común para las fuentes de datos abiertos que se consumen por HTTP.

Cada descarga pasa por:  circuit breaker  ->  retry con backoff  ->  httpx.get
"""
from typing import List

import httpx

from app.domain.opendata.ports import OpenDataSource, OpenDataUnavailableError
from app.infrastructure.resilience.circuit_breaker import (CircuitBreaker, CircuitOpenError,
                                                           TemporaryError, retry_with_backoff)


class HttpOpenDataSource(OpenDataSource):
    name = "http-source"

    def __init__(self, url: str, breaker: CircuitBreaker, timeout: float = 10,
                 retries: int = 3, base_delay: float = 0.5, http_get=httpx.get):
        self.url = url
        self.breaker = breaker
        self.timeout = timeout
        self.retries = retries
        self.base_delay = base_delay
        self.http_get = http_get  # se inyecta para poder simular respuestas en las pruebas

    def params(self) -> dict:
        return {}

    def parse(self, data) -> List[dict]:
        """Cada fuente sabe en qué parte del JSON vienen los registros."""
        return data

    def _request_once(self):
        try:
            response = self.http_get(self.url, params=self.params(), timeout=self.timeout)
        except httpx.TransportError as exc:  # sin conexión, DNS, timeout...
            raise TemporaryError(f"{type(exc).__name__}: {exc}")
        if response.status_code >= 500 or response.status_code == 429:
            raise TemporaryError(f"HTTP {response.status_code}")
        if response.status_code != 200:
            raise OpenDataUnavailableError(f"{self.name} returned HTTP {response.status_code}")
        return response.json()

    def fetch(self) -> List[dict]:
        try:
            data = self.breaker.call(
                lambda: retry_with_backoff(self._request_once, self.retries, self.base_delay))
        except CircuitOpenError:
            raise
        except TemporaryError as exc:
            raise OpenDataUnavailableError(f"{self.name} unavailable after {self.retries} retries: {exc}")
        return self.parse(data)

    def status(self) -> dict:
        return {"source": self.name, "url": self.url, **self.breaker.status()}
