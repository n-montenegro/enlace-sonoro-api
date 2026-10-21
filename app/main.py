"""
main.py - Punto de entrada de la API REST de Enlace Sonoro.

Ejecutar:   uvicorn app.main:app --reload
Swagger UI: http://127.0.0.1:8000/docs
OpenAPI:    http://127.0.0.1:8000/openapi.json
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # lee el archivo .env (GEMINI_API_KEY) antes de importar el resto

from app.database import init_db  # noqa: E402
from app.routers import ai, songs  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # crea la tabla al arrancar la API
    yield


app = FastAPI(
    title="Enlace Sonoro API",
    version="1.0.0",
    description=(
        "REST API for **Enlace Sonoro**, a music player developed for the "
        "Taller de Programación course (UMB). It manages the song catalog "
        "(CRUD) and exposes an AI music assistant powered by an LLM."
    ),
    contact={"name": "Nicolas Montenegro Gonzalez & Jhorman David Pardo Villamil"},
    lifespan=lifespan,
)

app.include_router(songs.router)
app.include_router(ai.router)


@app.get("/", tags=["Health"], summary="Health check", description="Confirms the API is running.")
def root():
    return {"status": "ok", "docs": "/docs"}
