"""test_duckdb_analytics.py - Las consultas SQL de DuckDB sobre archivos JSON de ejemplo."""
import json

from app.infrastructure.analytics.duckdb_analytics import DuckDBAnalytics
from tests.fakes import DANE_SAMPLE, DIVIPOLA_SAMPLE


def save(tmp_path, name, records):
    path = tmp_path / name
    path.write_text(json.dumps(records), encoding="utf-8")
    return str(path)


def test_municipalities_by_department_and_summary(tmp_path):
    path = save(tmp_path, "divipola.json", DIVIPOLA_SAMPLE)
    db = DuckDBAnalytics()
    by_dpto = db.municipalities_by_department(path)
    assert by_dpto[0] == {"departamento": "ANTIOQUIA", "municipios": 3}
    summary = db.municipalities_summary(path)
    assert summary["departamentos"] == 3
    assert summary["promedio"] == 2.0
    assert summary["mediana"] == 2
    assert summary["minimo"] == 1 and summary["maximo"] == 3


def test_culture_studies_are_filtered_and_typed(tmp_path):
    path = save(tmp_path, "dane.json", DANE_SAMPLE)
    db = DuckDBAnalytics()
    studies = db.culture_studies(path)
    assert [s["anio"] for s in studies] == [2009, 2010, 2012]
    assert studies[0]["descargas"] == 21399  # venía como texto "21399"
    summary = db.culture_studies_summary(path)
    assert summary["encuestas"] == 3
    assert summary["maximo_descargas"] == 21399
