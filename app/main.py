"""
main.py - Punto de entrada de la API REST de Enlace Sonoro.

Ejecutar:   uvicorn app.main:app --reload
Swagger UI: http://127.0.0.1:8000/docs
OpenAPI:    http://127.0.0.1:8000/openapi.json
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import songs


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


@app.get("/", tags=["Health"], summary="Health check", description="Confirms the API is running.")
def root():
    return {"status": "ok", "docs": "/docs"}
