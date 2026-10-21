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
