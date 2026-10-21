"""
run_experiments.py - Hace las 10 llamadas REALES al asistente y genera la tabla de comparación.

Requisitos: la API debe estar encendida (uvicorn) y el archivo .env debe tener la GEMINI_API_KEY.

Ejecutar (en otra terminal, dentro de la carpeta enlace-sonoro-api):
    py -3.14 scripts/run_experiments.py

Qué hace:
  1. Agrega canciones de ejemplo al catálogo (si ya existen, las ignora: 409).
  2. Hace 3 preguntas x 3 técnicas = 9 llamadas, más 1 llamada extra = 10 llamadas.
  3. Espera unos segundos entre llamadas para no superar el límite gratuito de Gemini.
  4. Escribe docs/prompting_comparison.md con todas las respuestas para evaluarlas.
"""
import os
import time

import httpx

API = "http://127.0.0.1:8000"
WAIT_SECONDS = 6

SAMPLE_SONGS = [
    ("Lofi Study Session", "Chillhop Beats", "Focus", "Lo-fi", 180),
    ("Snowman", "WYS", "Snowman", "Lo-fi", 158),
    ("Clair de Lune", "Claude Debussy", "Suite bergamasque", "Clasica", 305),
    ("Take Five", "The Dave Brubeck Quartet", "Time Out", "Jazz", 324),
    ("Weightless", "Marconi Union", "Weightless", "Ambient", 489),
    ("Gasolina", "Daddy Yankee", "Barrio Fino", "Reggaeton", 192),
    ("Pedro Navaja", "Ruben Blades", "Siembra", "Salsa", 441),
    ("Blinding Lights", "The Weeknd", "After Hours", "Pop", 200),
    ("Thunderstruck", "AC/DC", "The Razors Edge", "Rock", 292),
    ("Levels", "Avicii", "Levels", "Electronica", 202),
]

QUESTIONS = [
    "Recomiéndame canciones tranquilas para estudiar",
    "Quiero música para una fiesta con amigos",
    "Necesito canciones con mucha energía para el gimnasio",
]
TECHNIQUES = ["zero_shot", "few_shot", "chain_of_thought"]
EXTRA_CALL = ("Something relaxing to fall asleep", "few_shot")


def seed_catalog(client: httpx.Client) -> None:
    for title, artist, album, genre, duration in SAMPLE_SONGS:
        client.post(f"{API}/api/v1/songs", json={"title": title, "artist": artist, "album": album,
                                                  "genre": genre, "duration_seconds": duration})
    print(f"Catálogo listo: {len(client.get(f'{API}/api/v1/songs').json())} canciones")


def ask(client: httpx.Client, question: str, technique: str) -> dict:
    resp = client.post(f"{API}/api/v1/ai", json={"question": question, "technique": technique}, timeout=60)
    data = resp.json()
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {data.get('detail')}")
        return {"question": question, "technique": technique, "status": resp.status_code,
                "answer": f"ERROR {resp.status_code}: {data.get('detail')}", "input_tokens": 0,
                "output_tokens": 0, "latency_ms": 0}
    print(f"  OK ({data['latency_ms']} ms, {data['input_tokens']} in / {data['output_tokens']} out tokens)")
    return {"question": question, "technique": technique, "status": 200, **data}


def write_report(results: list) -> None:
    os.makedirs("docs", exist_ok=True)
    lines = ["# Prompting techniques comparison", "",
             "Same requests sent to the `/api/v1/ai` endpoint with three prompting techniques.",
             "Fill in the **Quality (1-5)** column after reading each answer (see criteria at the end).", "",
             "| # | Request | Technique | Input tokens | Output tokens | Latency (ms) | Quality (1-5) |",
             "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['question']} | {r['technique']} | {r['input_tokens']} | "
                     f"{r['output_tokens']} | {r['latency_ms']} | |")
    lines += ["", "## Full answers", ""]
    for i, r in enumerate(results, 1):
        lines += [f"### {i}. {r['technique']} — {r['question']}", "", r["answer"], ""]
    lines += ["## Evaluation criteria", "",
              "- **Grounding:** recommends only songs that exist in the catalog (no invented songs).",
              "- **Relevance:** the songs fit the requested mood or activity.",
              "- **Justification:** explains why each song fits.",
              "- **Format and length:** clear and concise answer.", ""]
    with open("docs/prompting_comparison.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\nTabla generada en docs/prompting_comparison.md")


def main() -> None:
    results = []
    with httpx.Client() as client:
        try:
            seed_catalog(client)
        except httpx.ConnectError:
            raise SystemExit("No se pudo conectar a la API. Enciéndela primero con: "
                             "py -3.14 -m uvicorn app.main:app --reload")
        calls = [(q, t) for q in QUESTIONS for t in TECHNIQUES] + [EXTRA_CALL]
        for n, (question, technique) in enumerate(calls, 1):
            print(f"[{n}/{len(calls)}] {technique}: {question}")
            results.append(ask(client, question, technique))
            if n < len(calls):
                time.sleep(WAIT_SECONDS)
    write_report(results)


if __name__ == "__main__":
    main()
