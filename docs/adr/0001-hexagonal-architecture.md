# ADR 0001: Move Enlace Sonoro to a hexagonal architecture

- **Status:** Accepted
- **Date:** 2026-11
- **Authors:** Nicolas Montenegro Gonzalez, Jhorman David Pardo Villamil

## Context

Until Lab Guide 5 the API had a flat structure: every router opened its own SQLite
connection and wrote SQL, and the AI router called the Gemini client directly.
This worked, but it caused some problems:

- Business rules (for example "a song must exist before it can be deleted") were mixed with HTTP and SQL code.
- To test the AI endpoint we had to use `monkeypatch` on module functions, because there was no way to pass a fake LLM.
- Lab Guide 6 asks us to add two Colombian open data APIs (datos.gov.co and DANE) and DuckDB.
  Adding them to the flat structure would make the routers even bigger and harder to test.

We also wanted to keep our linked list playlist (presented at the X Encuentro Nacional de
Semilleros UMB) as pure Python code, without depending on any framework.

## Decision

We reorganize the project into four layers (ports and adapters):

| Layer | Folder | Contains | Can depend on |
|---|---|---|---|
| Domain | `app/domain` | Entities (`Song`, `Playlist`), business errors, ports (interfaces) and pure logic (RAG, prompts) | nothing |
| Application | `app/application` | Use cases: `SongService`, `RecommendationService`, `OpenDataService` | domain |
| Infrastructure | `app/infrastructure` | Output adapters: SQLite repository, Gemini client, datos.gov.co and DANE clients, circuit breaker, DuckDB | domain |
| API | `app/api` | Input adapters: FastAPI routers, Pydantic schemas, dashboard page | application, domain |

Services receive their dependencies **through the constructor** (dependency injection).
`app/main.py` is the only place (composition root) where concrete adapters are created and connected.

We identified four **bounded contexts**:

1. **Catalog**: songs and their persistence.
2. **Playback**: the playlist as a doubly linked list and the play history.
3. **Recommendation**: the AI music assistant (RAG + LLM + call log).
4. **Open Data**: Colombian public data (DIVIPOLA from datos.gov.co, Cultural Consumption Survey from DANE) analyzed with DuckDB.

For the external APIs we use a **circuit breaker** (CLOSED, OPEN, HALF_OPEN) and
**retry with exponential backoff** (0.5 s, 1 s, 2 s). The last downloaded JSON is saved in
`data/` and is used as a fallback when an API is down.

## Consequences

**Positive**

- Each service can be tested alone with `unittest.mock` (the Python equivalent of Mockito), without SQLite or internet.
- The domain does not import FastAPI, httpx, SQLite or DuckDB. `tests/unit/test_architecture.py` checks these rules automatically in CI.
- We can change Gemini for another LLM, or SQLite for another database, by writing a new adapter only.
- If datos.gov.co or DANE fail, the app keeps working with the saved copy and stops calling the API while the circuit is OPEN.

**Negative**

- More files and folders than before; a new team member needs more time to understand the structure.
- Some mapping code is needed (Pydantic schema <-> `Song` entity <-> SQLite row).
- The circuit breaker state lives in memory, so it resets when the server restarts.
