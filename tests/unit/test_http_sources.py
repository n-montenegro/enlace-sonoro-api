"""test_http_sources.py - Clientes de datos.gov.co y DANE con respuestas HTTP simuladas (sin internet)."""
import httpx
import pytest

from app.domain.opendata.ports import OpenDataUnavailableError
from app.infrastructure.opendata.dane_client import DANE_CATALOG_URL, DaneCatalogClient
from app.infrastructure.opendata.datos_gov_client import DIVIPOLA_URL, DatosGovDivipolaClient
from app.infrastructure.resilience.circuit_breaker import OPEN, CircuitBreaker, CircuitOpenError
from tests.fakes import DANE_SAMPLE, DIVIPOLA_SAMPLE


class FakeHttp:
    """Simula httpx.get devolviendo, en orden, las respuestas de la lista."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, params=None, timeout=None):
        self.calls.append(params)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_divipola_returns_records_and_sends_limit():
    http = FakeHttp([httpx.Response(200, json=DIVIPOLA_SAMPLE)])
    client = DatosGovDivipolaClient(DIVIPOLA_URL, CircuitBreaker("t"), http_get=http, base_delay=0)
    assert client.fetch() == DIVIPOLA_SAMPLE
    assert http.calls[0] == {"$limit": 5000}


def test_dane_reads_rows_inside_result():
    http = FakeHttp([httpx.Response(200, json={"result": {"rows": DANE_SAMPLE, "found": "4"}})])
    client = DaneCatalogClient(DANE_CATALOG_URL, CircuitBreaker("t"), http_get=http, base_delay=0)
    assert len(client.fetch()) == 4
    assert http.calls[0] == {"sk": "musica"}


def test_retries_after_503_and_connection_error():
    http = FakeHttp([httpx.Response(503), httpx.ConnectError("sin red"), httpx.Response(200, json=DIVIPOLA_SAMPLE)])
    client = DatosGovDivipolaClient(DIVIPOLA_URL, CircuitBreaker("t"), http_get=http, base_delay=0)
    assert client.fetch() == DIVIPOLA_SAMPLE
    assert len(http.calls) == 3


def test_three_failed_fetches_open_the_circuit():
    http = FakeHttp([httpx.ConnectError("caída")] * 3)  # retries=0: 1 intento por fetch
    breaker = CircuitBreaker("t", failure_threshold=3)
    client = DatosGovDivipolaClient(DIVIPOLA_URL, breaker, http_get=http, retries=0, base_delay=0)
    for _ in range(3):
        with pytest.raises(OpenDataUnavailableError):
            client.fetch()
    assert breaker.state == OPEN
    with pytest.raises(CircuitOpenError):
        client.fetch()  # ya ni siquiera intenta la conexión
    assert len(http.calls) == 3
