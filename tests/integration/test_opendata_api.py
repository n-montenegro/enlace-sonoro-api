"""
test_opendata_api.py - Pruebas de los endpoints de datos abiertos.

Se inyectan fuentes FALSAS (no se llama a datos.gov.co ni al DANE) pero el resto es real:
OpenDataService + JsonDatasetStore + DuckDB.
"""
from fastapi.testclient import TestClient

from tests.fakes import DANE_SAMPLE, DIVIPOLA_SAMPLE, FakeSource
from tests.helpers import make_app


def make_client(tmp_path, monkeypatch, mun, dane):
    return TestClient(make_app(tmp_path, monkeypatch, municipalities=mun, studies=dane))


def test_municipalities_stats_with_duckdb(tmp_path, monkeypatch):
    mun = FakeSource("datos.gov.co - DIVIPOLA", DIVIPOLA_SAMPLE)
    with make_client(tmp_path, monkeypatch, mun, FakeSource("DANE", DANE_SAMPLE)) as client:
        data = client.get("/api/v1/opendata/municipalities/stats").json()
    assert data["from_cache"] is False
    assert data["by_department"][0] == {"departamento": "ANTIOQUIA", "municipios": 3}
    assert data["summary"]["departamentos"] == 3
    assert data["summary"]["total_municipios"] == 6


def test_culture_stats_only_counts_ecc(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, FakeSource("mun", DIVIPOLA_SAMPLE), FakeSource("DANE", DANE_SAMPLE)) as client:
        data = client.get("/api/v1/opendata/culture/stats").json()
    assert [e["anio"] for e in data["studies"]] == [2009, 2010, 2012]  # la EDIT no es de consumo cultural
    assert data["summary"]["total_descargas"] == 21399 + 14615 + 12146


def test_uses_saved_copy_when_api_is_down(tmp_path, monkeypatch):
    """Primero la API responde y se guarda el JSON; luego se cae y se usa la copia."""
    mun = FakeSource("datos.gov.co - DIVIPOLA", DIVIPOLA_SAMPLE)
    with make_client(tmp_path, monkeypatch, mun, FakeSource("DANE", DANE_SAMPLE)) as client:
        assert client.get("/api/v1/opendata/municipalities/stats").json()["from_cache"] is False
        mun.down = True
        data = client.get("/api/v1/opendata/municipalities/stats").json()
    assert data["from_cache"] is True
    assert data["summary"]["total_municipios"] == 6


def test_returns_503_when_api_is_down_and_no_copy(tmp_path, monkeypatch):
    down = FakeSource("DANE", DANE_SAMPLE, down=True)
    with make_client(tmp_path, monkeypatch, FakeSource("mun", DIVIPOLA_SAMPLE), down) as client:
        assert client.get("/api/v1/opendata/culture/stats").status_code == 503


def test_dashboard_page_is_served(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch, FakeSource("m", []), FakeSource("d", [])) as client:
        resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "Enlace Sonoro" in resp.text


def test_503_does_not_leak_internal_error_details(tmp_path, monkeypatch):
    """OWASP API8: el cliente no ve el error interno (rutas, nombres de excepciones, URLs)."""
    down = FakeSource("DANE", DANE_SAMPLE, down=True)
    with make_client(tmp_path, monkeypatch, FakeSource("mun", DIVIPOLA_SAMPLE), down) as client:
        resp = client.get("/api/v1/opendata/culture/stats")
    assert resp.json() == {"detail": "The data source is temporarily unavailable. Try again later."}
