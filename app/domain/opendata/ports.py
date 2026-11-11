"""
ports.py - Puertos del bounded context "Datos abiertos".

  OpenDataSource -> una fuente de datos abiertos (datos.gov.co, DANE...).
  DatasetStore   -> guarda la última copia JSON de cada fuente (sirve de respaldo).
  AnalyticsPort  -> motor de análisis (implementado con DuckDB).
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class OpenDataUnavailableError(Exception):
    """La fuente no respondió (o el circuit breaker está abierto) y no hay copia guardada."""


class OpenDataSource(ABC):
    name: str = "source"

    @abstractmethod
    def fetch(self) -> List[dict]:
        """Descarga los registros JSON. Lanza OpenDataUnavailableError si falla."""

    @abstractmethod
    def status(self) -> dict:
        """Estado actual de la fuente (estado del circuit breaker, fallos, historial)."""


class DatasetStore(ABC):

    @abstractmethod
    def save(self, name: str, records: List[dict]) -> str:
        """Guarda los registros como JSON y devuelve la ruta del archivo."""

    @abstractmethod
    def path_for(self, name: str) -> Optional[str]:
        """Ruta del último JSON guardado, o None si nunca se ha guardado."""


class AnalyticsPort(ABC):

    @abstractmethod
    def municipalities_by_department(self, json_path: str) -> List[dict]:
        """Consulta 1: número de municipios por departamento."""

    @abstractmethod
    def municipalities_summary(self, json_path: str) -> dict:
        """Consulta 2: estadísticas descriptivas de municipios por departamento."""

    @abstractmethod
    def culture_studies(self, json_path: str) -> List[dict]:
        """Consulta 3: Encuestas de Consumo Cultural del DANE por año."""

    @abstractmethod
    def culture_studies_summary(self, json_path: str) -> dict:
        """Consulta 4: estadísticas descriptivas de descargas de esas encuestas."""
