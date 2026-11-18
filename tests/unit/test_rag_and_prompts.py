"""
test_rag_and_prompts.py - Pruebas añadidas tras el análisis de mutation testing (Guía 7).

Los mutantes que sobrevivían cambiaban textos del prompt, el orden del RAG o el formato
del contexto sin que ninguna prueba lo notara. Estas pruebas verifican esos detalles exactos.
"""
import pytest

from app.domain.catalog.song import Song
from app.domain.recommendation.prompts import FEW_SHOT_EXAMPLES, build_prompt
from app.domain.recommendation.rag import build_context, extract_keywords, normalize, retrieve_songs

STUDY = Song(id=1, title="Lofi Study Session", artist="Chillhop Beats", album="Focus", genre="Lo-fi", duration_seconds=180)
JAZZ = Song(id=2, title="Take Five", artist="Dave Brubeck", album=None, genre="Jazz", duration_seconds=324)
PARTY = Song(id=3, title="Gasolina", artist="Daddy Yankee", album="Barrio Fino", genre="Reggaeton", duration_seconds=192)


# ---------------- prompts ----------------

def test_zero_shot_prompt_is_exact():
    assert build_prompt("zero_shot", "algo para leer", "CTX") == (
        "Catalog:\nCTX\n\n"
        "User request: algo para leer\n"
        "Recommend the most suitable songs from the catalog and briefly explain why."
    )


def test_few_shot_prompt_is_exact():
    assert build_prompt("few_shot", "algo para leer", "CTX") == (
        "Follow the style of these examples.\n\n"
        f"{FEW_SHOT_EXAMPLES}\n\n"
        "Now your turn\n"
        "Catalog:\nCTX\n"
        "User: algo para leer\n"
        "Assistant:"
    )


def test_chain_of_thought_prompt_is_exact():
    assert build_prompt("chain_of_thought", "algo para leer", "CTX") == (
        "Catalog:\nCTX\n\n"
        "User request: algo para leer\n\n"
        "Think step by step before answering:\n"
        "1. What activity or mood does the user describe?\n"
        "2. Which musical characteristics fit it (genre, energy, tempo)?\n"
        "3. Which catalog songs match those characteristics, and which do not?\n"
        "Then write your final recommendation with a short justification."
    )


def test_unknown_technique_names_the_technique():
    with pytest.raises(ValueError, match="Unknown technique: magic"):
        build_prompt("magic", "q", "ctx")


# ---------------- RAG ----------------

def test_normalize_lowercases_and_removes_accents():
    assert normalize("Clásica ÁNIMO Canción") == "clasica animo cancion"


def test_extract_keywords_filters_stopwords_and_short_words():
    # "para" es stopword, "yo" es muy corta; "sol" (3 letras) sí se conserva
    assert extract_keywords("Quiero sol para yo") == ["sol"]


def test_extract_keywords_adds_genres_for_moods():
    assert extract_keywords("Estudiar") == ["estudiar", "lo-fi", "clasica", "jazz", "ambient"]


def test_retrieve_orders_by_number_of_matches():
    # "jazz" coincide 1 vez con Take Five; "lofi study" coincide 2 veces con Lofi Study Session
    result = retrieve_songs("jazz lofi study", [JAZZ, PARTY, STUDY])
    assert result == [STUDY, JAZZ]


def test_retrieve_excludes_songs_without_matches_and_respects_limit():
    catalog = [Song(id=i, title=f"Rock {i}", artist="X", genre="Rock", duration_seconds=100) for i in range(10)]
    assert len(retrieve_songs("rock", catalog, limit=3)) == 3
    assert retrieve_songs("gasolina", [STUDY, PARTY]) == [PARTY]


def test_retrieve_returns_catalog_when_nothing_matches():
    assert retrieve_songs("zzz", [STUDY, JAZZ, PARTY], limit=2) == [STUDY, JAZZ]


def test_retrieve_does_not_match_missing_album_text():
    """Una canción sin álbum no debe coincidir con palabras inventadas para el álbum vacío."""
    assert retrieve_songs("none", [JAZZ]) == [JAZZ]  # cae al catálogo, no por coincidencia
    assert retrieve_songs("none take", [PARTY, JAZZ]) == [JAZZ]


def test_build_context_exact_format():
    assert build_context([STUDY, JAZZ]) == (
        '- [id 1] "Lofi Study Session" by Chillhop Beats (genre: Lo-fi, album: Focus, 3:00)\n'
        '- [id 2] "Take Five" by Dave Brubeck (genre: Jazz, 5:24)'
    )


def test_build_context_empty_catalog():
    assert build_context([]) == "(The catalog is empty.)"
