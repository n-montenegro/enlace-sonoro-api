"""
datos_gov_client.py - API 1: datos.gov.co (Portal de Datos Abiertos de Colombia).

Conjunto: DIVIPOLA - Códigos municipios (id gdxc-w37w), publicado por el DANE.
Usa la API Socrata (SODA). Cada registro trae:
    cod_dpto, dpto, cod_mpio, nom_mpio, tipo_municipio, longitud, latitud
"""
from app.infrastructure.opendata.http_source import HttpOpenDataSource

DIVIPOLA_URL = "https://www.datos.gov.co/resource/gdxc-w37w.json"


class DatosGovDivipolaClient(HttpOpenDataSource):
    name = "datos.gov.co - DIVIPOLA"

    def params(self) -> dict:
        return {"$limit": 5000}  # hay unos 1.100 municipios; pedimos todos de una vez
