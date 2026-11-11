"""
main.py - COMPOSITION ROOT de Enlace Sonoro.

Es el ÚNICO lugar donde se crean los adaptadores concretos (SQLite, Gemini, datos.gov.co,
DANE, DuckDB) y se inyectan en los servicios por su constructor.
Las demás capas solo conocen interfaces (puertos).

Arquitectura hexagonal:
    api/            -> adaptadores de ENTRADA (FastAPI)
    application/    -> casos de uso (servicios)
    domain/         -> entidades, reglas de negocio y puertos (sin librerías externas)
    infrastructure/ -> adaptadores de SALIDA (SQLite, Gemini, APIs colombianas, DuckDB)

Ejecutar:   uvicorn app.main:app --reload
Swagger UI: http://127.0.0.1:8000/docs
Dashboard:  http://127.0.0.1:8000/dashboard
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routers import ai, dashboard, opendata, songs
from app.application.opendata_service import OpenDataService
from app.application.recommendation_service import RecommendationService
from app.application.song_service import SongService
from app.domain.opendata.ports import OpenDataSource
from app.domain.recommendation.ports import LLMPort
from app.infrastructure.analytics.duckdb_analytics import DuckDBAnalytics
from app.infrastructure.llm.gemini_client import GeminiClient
from app.infrastructure.llm.jsonl_call_log import JsonlCallLog
from app.infrastructure.opendata.dane_client import DANE_CATALOG_URL, DaneCatalogClient
from app.infrastructure.opendata.datos_gov_client import DIVIPOLA_URL, DatosGovDivipolaClient
from app.infrastructure.opendata.json_dataset_store import JsonDatasetStore
from app.infrastructure.persistence.sqlite_song_repository import SqliteSongRepository
from app.infrastructure.resilience.circuit_breaker import CircuitBreaker

load_dotenv()  # lee el archivo .env (GEMINI_API_KEY)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def create_app(llm: Optional[LLMPort] = None,
               municipalities: Optional[OpenDataSource] = None,
               studies: Optional[OpenDataSource] = None) -> FastAPI:
    """
    Arma la aplicación. Los parámetros permiten que las pruebas inyecten dobles (fakes/mocks)
    en lugar de Gemini o de las APIs reales.
    """
    # ---- adaptadores de salida (infraestructura) ----
    repository = SqliteSongRepository(os.getenv("DB_PATH", "enlace_sonoro.db"))
    call_log = JsonlCallLog(os.getenv("LLM_LOG_PATH", os.path.join("logs", "llm_calls.jsonl")))
    llm = llm or GeminiClient()
    municipalities = municipalities or DatosGovDivipolaClient(
        DIVIPOLA_URL, CircuitBreaker("datos.gov.co", failure_threshold=3, recovery_timeout=30))
    studies = studies or DaneCatalogClient(
        DANE_CATALOG_URL, CircuitBreaker("DANE", failure_threshold=3, recovery_timeout=30))
    store = JsonDatasetStore(os.getenv("OPEN_DATA_DIR", "data"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.init_schema()  # crea la tabla al arrancar la API
        yield

    app = FastAPI(
        title="Enlace Sonoro API",
        version="2.0.0",
        description=(
            "REST API for **Enlace Sonoro**, a music player developed for the Taller de Programación "
            "course (UMB). Hexagonal architecture: song catalog (CRUD), an AI music assistant powered by "
            "an LLM, and analytics over Colombian open data (datos.gov.co and DANE) with DuckDB. "
            "Charts: [/dashboard](/dashboard)"
        ),
        contact={"name": "Nicolas Montenegro Gonzalez & Jhorman David Pardo Villamil"},
        lifespan=lifespan,
    )

    # ---- servicios (aplicación) con inyección de dependencias por constructor ----
    app.state.song_service = SongService(repository)
    app.state.recommendation_service = RecommendationService(repository, llm, call_log)
    app.state.opendata_service = OpenDataService(municipalities, studies, store, DuckDBAnalytics())

    # ---- adaptadores de entrada (api) ----
    app.include_router(songs.router)
    app.include_router(ai.router)
    app.include_router(opendata.router)
    app.include_router(dashboard.router)

    @app.get("/", tags=["Health"], summary="Health check", description="Confirms the API is running.")
    def root():
        return {"status": "ok", "docs": "/docs", "dashboard": "/dashboard"}

    return app


app = create_app()
