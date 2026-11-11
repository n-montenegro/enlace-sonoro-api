"""
dane_client.py - API 2: DANE, Archivo Nacional de Datos (ANDA) - catálogo de microdatos.

Endpoint de búsqueda del catálogo:  /index.php/api/catalog/search?sk=<palabra>
La respuesta trae los estudios en  result.rows  con campos como:
    title, year_start, repo_title, total_views, total_downloads, url
"""
from typing import List

from app.infrastructure.opendata.http_source import HttpOpenDataSource

DANE_CATALOG_URL = "https://microdatos.dane.gov.co/index.php/api/catalog/search"


class DaneCatalogClient(HttpOpenDataSource):
    name = "DANE - ANDA microdatos"
    search_term = "musica"

    def params(self) -> dict:
        return {"sk": self.search_term}

    def parse(self, data) -> List[dict]:
        return data["result"]["rows"]
