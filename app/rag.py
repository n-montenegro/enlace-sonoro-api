"""
rag.py - RAG básico (Retrieval-Augmented Generation) para Enlace Sonoro.

RAG = antes de preguntarle al LLM, RECUPERAMOS (Retrieval) información propia
y la AGREGAMOS (Augmented) al prompt para que la GENERACIÓN (Generation)
se base en nuestros datos y no en lo que el modelo "se imagina".

Aquí la información propia es el catálogo de canciones guardado en SQLite.
La recuperación es por palabras clave (sin embeddings), suficiente para un catálogo pequeño:
  1. Se separan las palabras de la pregunta.
  2. Algunas palabras de "ánimo" se traducen a géneros (ej. "estudiar" -> lo-fi, clásica).
  3. Se puntúa cada canción según cuántas palabras coinciden con su título, artista, álbum o género.
  4. Se devuelven las mejores. Si ninguna coincide, se devuelve el catálogo (hasta el límite).
"""
import re
import unicodedata
from typing import List

from app.database import get_connection

# Palabras de ánimo/actividad -> géneros relacionados (español e inglés)
MOOD_TO_GENRES = {
    "estudiar": ["lo-fi", "clasica", "jazz", "ambient"],
    "study": ["lo-fi", "clasica", "jazz", "ambient"],
    "concentrarme": ["lo-fi", "clasica", "ambient"],
    "relajarme": ["lo-fi", "jazz", "ambient", "clasica"],
    "relax": ["lo-fi", "jazz", "ambient", "clasica"],
    "tranquila": ["lo-fi", "jazz", "clasica", "ambient"],
    "tranquilas": ["lo-fi", "jazz", "clasica", "ambient"],
    "dormir": ["ambient", "clasica", "lo-fi"],
    "fiesta": ["reggaeton", "pop", "salsa", "electronica"],
    "party": ["reggaeton", "pop", "salsa", "electronica"],
    "bailar": ["salsa", "reggaeton", "pop", "electronica"],
    "dance": ["salsa", "reggaeton", "pop", "electronica"],
    "gimnasio": ["rock", "electronica", "reggaeton", "hip-hop"],
    "gym": ["rock", "electronica", "reggaeton", "hip-hop"],
    "entrenar": ["rock", "electronica", "hip-hop"],
    "energia": ["rock", "electronica", "pop"],
    "energy": ["rock", "electronica", "pop"],
    "workout": ["rock", "electronica", "hip-hop"],
    "relaxing": ["lo-fi", "jazz", "ambient", "clasica"],
    "calm": ["lo-fi", "jazz", "ambient", "clasica"],
    "sleep": ["ambient", "clasica", "lo-fi"],
    "asleep": ["ambient", "clasica", "lo-fi"],
    "focus": ["lo-fi", "clasica", "ambient"],
}

STOPWORDS = {"de", "la", "el", "los", "las", "un", "una", "para", "por", "que", "y", "o", "a", "en",
             "me", "mi", "con", "algo", "canciones", "cancion", "musica", "recomiendame", "quiero",
             "the", "for", "to", "some", "songs", "song", "music", "recommend", "me", "i", "want"}


def normalize(text: str) -> str:
    """Minúsculas y sin tildes: 'Clásica' -> 'clasica'."""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def extract_keywords(question: str) -> List[str]:
    words = re.findall(r"[a-z0-9\-]+", normalize(question))
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
    for word in list(keywords):
        keywords.extend(MOOD_TO_GENRES.get(word, []))
    return keywords


def retrieve_songs(question: str, limit: int = 8) -> List[dict]:
    """Devuelve las canciones del catálogo más relacionadas con la pregunta."""
    conn = get_connection()
    try:
        rows = [dict(r) for r in conn.execute("SELECT * FROM songs ORDER BY id").fetchall()]
    finally:
        conn.close()

    keywords = extract_keywords(question)
    scored = []
    for song in rows:
        searchable = normalize(f"{song['title']} {song['artist']} {song['album'] or ''} {song['genre']}")
        score = sum(1 for kw in keywords if kw in searchable)
        scored.append((score, song))

    matches = [song for score, song in sorted(scored, key=lambda x: -x[0]) if score > 0]
    if matches:
        return matches[:limit]
    return rows[:limit]  # sin coincidencias: se envía el catálogo para que el LLM elija


def build_context(songs: List[dict]) -> str:
    """Convierte las canciones recuperadas en texto para insertarlo en el prompt."""
    if not songs:
        return "(The catalog is empty.)"
    lines = []
    for s in songs:
        minutes, seconds = divmod(s["duration_seconds"], 60)
        album = f", album: {s['album']}" if s["album"] else ""
        lines.append(f"- [id {s['id']}] \"{s['title']}\" by {s['artist']} (genre: {s['genre']}{album}, {minutes}:{seconds:02d})")
    return "\n".join(lines)
