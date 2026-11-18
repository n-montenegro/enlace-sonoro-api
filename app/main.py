"""
main.py - COMPOSITION ROOT de Enlace Sonoro.

Es el ÚNICO lugar donde se crean los adaptadores concretos (SQLite o PostgreSQL, Gemini,
datos.gov.co, DANE, DuckDB) y se inyectan en los servicios por su constructor.
Las demás capas solo conocen interfaces (puertos).

Arquitectura hexagonal:
    api/            -> adaptadores de ENTRADA (FastAPI)
    application/    -> casos de uso (servicios)
    domain/         -> entidades, reglas de negocio y puertos (sin librerías externas)
    infrastructure/ -> adaptadores de SALIDA (SQLite/PostgreSQL, Gemini, APIs colombianas, DuckDB)

Seguridad (Guía 7): JWT + RBAC (ADMIN / USER), límites de solicitudes, CORS restringido
y cabeceras de seguridad. Ver docs/security/owasp-api-top10-2023.md

Producción (Guía 8): si existe la variable DATABASE_URL se usa PostgreSQL; si no, SQLite (desarrollo y pruebas).

Ejecutar:   uvicorn app.main:app --reload
Swagger UI: http://127.0.0.1:8000/docs
Dashboard:  http://127.0.0.1:8000/dashboard
"""
import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.rate_limit import RateLimiter
from app.api.routers import admin, ai, auth, dashboard, opendata, songs
from app.application.auth_service import AuthService
from app.application.opendata_service import OpenDataService
from app.application.recommendation_service import RecommendationService
from app.application.song_service import SongService
from app.domain.catalog.ports import SongRepository
from app.domain.identity.ports import PasswordHasher, UserRepository
from app.domain.opendata.ports import OpenDataSource
from app.domain.recommendation.ports import LLMPort
from app.infrastructure.analytics.duckdb_analytics import DuckDBAnalytics
from app.infrastructure.llm.gemini_client import GeminiClient
from app.infrastructure.llm.jsonl_call_log import JsonlCallLog
from app.infrastructure.opendata.dane_client import DANE_CATALOG_URL, DaneCatalogClient
from app.infrastructure.opendata.datos_gov_client import DIVIPOLA_URL, DatosGovDivipolaClient
from app.infrastructure.opendata.json_dataset_store import JsonDatasetStore
from app.infrastructure.persistence.postgres_song_repository import PostgresSongRepository
from app.infrastructure.persistence.postgres_user_repository import PostgresUserRepository
from app.infrastructure.persistence.sqlite_song_repository import SqliteSongRepository
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from app.infrastructure.resilience.circuit_breaker import CircuitBreaker
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.pbkdf2_hasher import Pbkdf2PasswordHasher

load_dotenv()  # lee el archivo .env (GEMINI_API_KEY)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("enlace_sonoro")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",         # el navegador no "adivina" el tipo de archivo
    "X-Frame-Options": "DENY",                   # la app no se puede meter en un iframe (clickjacking)
    "Referrer-Policy": "no-referrer",            # no se filtra la URL a otros sitios
    "Cache-Control": "no-store",                 # respuestas con datos personales no se guardan en caché
}


def jwt_secret() -> str:
    """La clave del JWT viene del .env. Si falta, se genera una temporal (los tokens mueren al reiniciar)."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        logger.warning("JWT_SECRET is not set: using a temporary random secret (development only)")
        secret = secrets.token_urlsafe(48)
    return secret


def build_repositories() -> tuple[SongRepository, UserRepository]:
    """PostgreSQL si hay DATABASE_URL (Render y docker-compose); SQLite en desarrollo y pruebas."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Database: PostgreSQL")
        return PostgresSongRepository(database_url), PostgresUserRepository(database_url)
    db_path = os.getenv("DB_PATH", "enlace_sonoro.db")
    logger.info("Database: SQLite (%s)", db_path)
    return SqliteSongRepository(db_path), SqliteUserRepository(db_path)


def create_app(llm: Optional[LLMPort] = None,
               municipalities: Optional[OpenDataSource] = None,
               studies: Optional[OpenDataSource] = None,
               password_hasher: Optional[PasswordHasher] = None) -> FastAPI:
    """
    Arma la aplicación. Los parámetros permiten que las pruebas inyecten dobles (fakes/mocks)
    en lugar de Gemini o de las APIs reales.
    """
    # ---- adaptadores de salida (infraestructura) ----
    repository, user_repository = build_repositories()
    call_log = JsonlCallLog(os.getenv("LLM_LOG_PATH", os.path.join("logs", "llm_calls.jsonl")))
    llm = llm or GeminiClient()
    municipalities = municipalities or DatosGovDivipolaClient(
        DIVIPOLA_URL, CircuitBreaker("datos.gov.co", failure_threshold=3, recovery_timeout=30))
    studies = studies or DaneCatalogClient(
        DANE_CATALOG_URL, CircuitBreaker("DANE", failure_threshold=3, recovery_timeout=30))
    store = JsonDatasetStore(os.getenv("OPEN_DATA_DIR", "data"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.init_schema()  # crea las tablas al arrancar la API
        user_repository.init_schema()
        # En Render no hay terminal para correr scripts/create_user.py: el primer ADMIN se crea
        # con las variables ADMIN_USERNAME y ADMIN_PASSWORD (solo si la tabla de usuarios está vacía)
        if app.state.auth_service.ensure_admin(os.getenv("ADMIN_USERNAME", ""), os.getenv("ADMIN_PASSWORD", "")):
            logger.info("First ADMIN user created from environment variables")
        yield

    app = FastAPI(
        title="Enlace Sonoro API",
        version="3.0.0",
        description=(
            "REST API for **Enlace Sonoro**, a music player developed for the Taller de Programación "
            "course (UMB). Hexagonal architecture: song catalog (CRUD), an AI music assistant powered by "
            "an LLM, and analytics over Colombian open data (datos.gov.co and DANE) with DuckDB. "
            "Secured with JWT and role-based access control (ADMIN / USER): use **Authorize** to log in. "
            "Charts: [/dashboard](/dashboard)"
        ),
        contact={"name": "Nicolas Montenegro Gonzalez & Jhorman David Pardo Villamil"},
        lifespan=lifespan,
        # En producción se puede ocultar la documentación con ENABLE_DOCS=false (OWASP API8/API9)
        docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
        redoc_url=None,
    )

    # ---- seguridad transversal ----
    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"])

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response

    app.state.limiters = {
        "auth": RateLimiter(max_requests=5, window_seconds=60),       # 5 intentos de login por minuto
        "ai": RateLimiter(max_requests=10, window_seconds=60),        # 10 preguntas al LLM por minuto
        "opendata": RateLimiter(max_requests=30, window_seconds=60),  # 30 consultas por minuto
    }

    # ---- servicios (aplicación) con inyección de dependencias por constructor ----
    app.state.song_service = SongService(repository)
    app.state.recommendation_service = RecommendationService(repository, llm, call_log)
    app.state.opendata_service = OpenDataService(municipalities, studies, store, DuckDBAnalytics())
    app.state.auth_service = AuthService(user_repository, password_hasher or Pbkdf2PasswordHasher(),
                                         JwtTokenService(jwt_secret()))

    # ---- adaptadores de entrada (api) ----
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(songs.router)
    app.include_router(ai.router)
    app.include_router(opendata.router)
    app.include_router(dashboard.router)

    @app.get("/", tags=["Health"], summary="Health check", description="Confirms the API is running.")
    def root():
        return {"status": "ok", "docs": "/docs", "dashboard": "/dashboard"}

    @app.get("/health", tags=["Health"], summary="Readiness check (API + database)",
             description="Used by Docker, docker-compose and Render: returns 503 if the database is not reachable.",
             responses={503: {"description": "Database unavailable"}})
    def health():
        try:
            app.state.auth_service.count_users()  # consulta mínima a la base de datos
        except Exception:
            logger.exception("Health check failed: database unavailable")
            return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
        # version = commit desplegado (lo pone el pipeline al construir la imagen); "dev" en local
        return {"status": "ok", "database": "ok", "version": os.getenv("APP_VERSION", "dev")}

    return app


app = create_app()
