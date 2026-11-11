"""
opendata_service.py - Caso de uso: análisis de datos abiertos colombianos.

Recibe por CONSTRUCTOR:
  - municipalities: fuente datos.gov.co (DIVIPOLA)
  - studies:        fuente DANE (catálogo de microdatos)
  - store:          donde se guarda la última copia JSON de cada fuente
  - analytics:      motor de consultas (DuckDB)

Si una fuente falla (o su circuit breaker está abierto), se usa la última copia guardada.
Así la app sigue respondiendo aunque datos.gov.co o el DANE estén caídos.
"""
from app.domain.opendata.ports import (AnalyticsPort, DatasetStore, OpenDataSource,
                                       OpenDataUnavailableError)


class OpenDataService:

    def __init__(self, municipalities: OpenDataSource, studies: OpenDataSource,
                 store: DatasetStore, analytics: AnalyticsPort):
        self.municipalities = municipalities
        self.studies = studies
        self.store = store
        self.analytics = analytics

    def _load(self, source: OpenDataSource) -> dict:
        """Descarga la fuente; si falla, usa la copia guardada. Devuelve la ruta del JSON y el origen."""
        try:
            records = source.fetch()
            path = self.store.save(source.name, records)
            return {"path": path, "from_cache": False}
        except OpenDataUnavailableError:
            path = self.store.path_for(source.name)
            if path is None:
                raise  # no hay datos nuevos ni copia guardada
            return {"path": path, "from_cache": True}

    def municipalities_stats(self) -> dict:
        data = self._load(self.municipalities)
        return {
            "source": self.municipalities.name,
            "from_cache": data["from_cache"],
            "by_department": self.analytics.municipalities_by_department(data["path"]),
            "summary": self.analytics.municipalities_summary(data["path"]),
        }

    def culture_studies_stats(self) -> dict:
        data = self._load(self.studies)
        return {
            "source": self.studies.name,
            "from_cache": data["from_cache"],
            "studies": self.analytics.culture_studies(data["path"]),
            "summary": self.analytics.culture_studies_summary(data["path"]),
        }

    def status(self) -> dict:
        return {"sources": [self.municipalities.status(), self.studies.status()]}
