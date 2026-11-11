# Enlace Sonoro API

REST API for **Enlace Sonoro** (music player) — Taller de Programación, UMB.
Authors: Nicolas Montenegro Gonzalez & Jhorman David Pardo Villamil.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs  
Dashboard (DuckDB charts): http://127.0.0.1:8000/dashboard

## Architecture (Lab Guide 6)

Hexagonal architecture (ports and adapters). See [ADR 0001](docs/adr/0001-hexagonal-architecture.md) and the [bounded contexts diagram](docs/bounded-contexts.md).

```
app/
├── domain/            # entities, business rules and ports (no external libraries)
│   ├── catalog/       # Song, SongRepository
│   ├── playback/      # Playlist (doubly linked list)
│   ├── recommendation/# RAG, prompts, LLMPort, CallLogPort
│   └── opendata/      # OpenDataSource, DatasetStore, AnalyticsPort
├── application/       # SongService, RecommendationService, OpenDataService
├── infrastructure/    # SQLite, Gemini, datos.gov.co, DANE, circuit breaker, DuckDB
├── api/               # FastAPI routers, schemas, dashboard
└── main.py            # composition root (dependency injection)
```

Circuit breaker demo:

```bash
py -3.14 scripts/demo_circuit_breaker.py
```

## AI music assistant (Gemini)

1. Copy `.env.example` to `.env` and paste your Gemini API key (never commit `.env`).
2. Start the API and use `POST /api/v1/ai` in Swagger UI.
3. Run the 10 real calls and the reports:

```bash
py -3.14 scripts/run_experiments.py   # generates docs/prompting_comparison.md
py -3.14 scripts/cost_estimate.py     # generates docs/cost_estimate.md
```

## Run tests

```bash
pytest -v
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/songs | Create a song |
| GET | /api/v1/songs | List songs (optional `?genre=`) |
| GET | /api/v1/songs/{id} | Get a song |
| PUT | /api/v1/songs/{id} | Update a song |
| DELETE | /api/v1/songs/{id} | Delete a song |
| POST | /api/v1/ai | Ask the AI music assistant (RAG + Gemini) |
| GET | /api/v1/ai/calls | List logged LLM calls |
| GET | /api/v1/opendata/municipalities/stats | DIVIPOLA (datos.gov.co) analyzed with DuckDB |
| GET | /api/v1/opendata/culture/stats | Cultural Consumption Survey (DANE) analyzed with DuckDB |
| GET | /api/v1/opendata/status | Circuit breaker states |
| GET | /dashboard | Charts page |
