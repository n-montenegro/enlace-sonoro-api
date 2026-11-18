"""
test_domain_details.py - Más pruebas añadidas tras el análisis de mutation testing.

Cubren casos borde que ninguna prueba revisaba: mensajes de error exactos, la playlist
recorrida hacia atrás, el registro de llamadas del asistente y los datos de OpenDataService.
"""
from unittest.mock import Mock

import pytest

from app.application.opendata_service import OpenDataService
from app.application.recommendation_service import RecommendationService
from app.application.song_service import SongService
from app.domain.catalog.errors import DuplicateSongError, SongNotFoundError
from app.domain.catalog.ports import SongRepository
from app.domain.catalog.song import Song
from app.domain.identity.errors import (InvalidCredentialsError, InvalidRoleError, InvalidTokenError,
                                        PermissionDeniedError, UserAlreadyExistsError)
from app.domain.opendata.ports import AnalyticsPort, DatasetStore, OpenDataSource, OpenDataUnavailableError
from app.domain.playback.playlist import Playlist
from app.domain.recommendation.ports import CallLogPort, LLMError, LLMPort, LLMTimeoutError


# ---------------- mensajes de error ----------------

def test_error_messages_are_exact():
    assert str(SongNotFoundError(5)) == "Song with id 5 not found"
    assert SongNotFoundError(5).song_id == 5
    assert str(DuplicateSongError()) == "A song with this title and artist already exists"
    assert str(InvalidCredentialsError()) == "Incorrect username or password"
    assert str(InvalidTokenError()) == "Invalid or expired token"
    assert str(PermissionDeniedError("ADMIN")) == "This action requires the ADMIN role"
    assert PermissionDeniedError("ADMIN").required_role == "ADMIN"
    assert str(UserAlreadyExistsError("laura")) == "Username 'laura' is already taken"
    assert str(InvalidRoleError("ROOT")) == "Unknown role 'ROOT'"


# ---------------- playlist ----------------

def recorrer_hacia_atras(p: Playlist):
    canciones, nodo = [], p.cola
    while nodo is not None:
        canciones.append(nodo.cancion)
        nodo = nodo.anterior
    return canciones


def test_new_playlist_is_empty():
    p = Playlist("Estudio")
    assert p.nombre == "Estudio"
    assert p.cabeza is None and p.cola is None and p.actual is None
    assert p.reproducir() is None
    assert p.anterior() is None


def test_links_work_in_both_directions():
    p = Playlist("Mix")
    p.agregar_al_inicio("B")
    p.agregar_al_inicio("A")
    p.agregar_al_final("C")
    assert p.a_lista() == ["A", "B", "C"]
    assert recorrer_hacia_atras(p) == ["C", "B", "A"]


def test_first_song_added_at_start_is_head_and_tail():
    p = Playlist("Mix")
    p.agregar_al_inicio("A")
    assert p.cabeza.cancion == "A" and p.cola.cancion == "A"


def test_delete_last_song_updates_tail():
    p = Playlist("Mix")
    for c in ["A", "B", "C"]:
        p.agregar_al_final(c)
    p.eliminar("C")
    assert p.cola.cancion == "B"
    assert recorrer_hacia_atras(p) == ["B", "A"]


def test_delete_middle_song_keeps_backward_links():
    p = Playlist("Mix")
    for c in ["A", "B", "C"]:
        p.agregar_al_final(c)
    p.eliminar("B")
    assert recorrer_hacia_atras(p) == ["C", "A"]


def test_deleting_the_current_song_moves_to_the_next():
    p = Playlist("Mix")
    for c in ["A", "B", "C"]:
        p.agregar_al_final(c)
    p.reproducir()
    p.siguiente()          # suena B
    p.eliminar("A")        # borrar otra canción no cambia la actual
    assert p.actual.cancion == "B"
    p.eliminar("B")        # borrar la que suena pasa a la siguiente
    assert p.actual.cancion == "C"


# ---------------- servicios ----------------

def test_song_service_passes_genre_filter_and_returns_found_song():
    repo = Mock(spec=SongRepository)
    repo.list.return_value = []
    song = Song(id=1, title="A", artist="B", genre="Rock", duration_seconds=10)
    repo.get.return_value = song
    service = SongService(repo)
    service.list("Rock")
    repo.list.assert_called_once_with("Rock")
    assert service.get(1) is song


def build_recommendation(llm_error=None):
    repo = Mock(spec=SongRepository)
    repo.list.return_value = [Song(id=1, title="Lofi Study", artist="Chill", genre="Lo-fi", duration_seconds=60)]
    llm = Mock(spec=LLMPort)
    llm.model_name.return_value = "m1"
    if llm_error:
        llm.ask.side_effect = llm_error
    else:
        llm.ask.return_value = {"text": "ok", "input_tokens": 10, "output_tokens": 2, "thinking_tokens": 1,
                                "latency_ms": 50, "model": "m1"}
    log = Mock(spec=CallLogPort)
    return RecommendationService(repo, llm, log), llm, log


def test_successful_call_is_logged_with_every_field():
    service, llm, log = build_recommendation()
    answer = service.ask("musica para estudiar", "zero_shot")
    assert "User request: musica para estudiar" in llm.ask.call_args.args[0]
    assert log.save.call_args.args[0] == {
        "technique": "zero_shot", "question": "musica para estudiar", "model": "m1",
        "retrieved_songs": ["Lofi Study - Chill"], "status": 200, "answer": "ok",
        "input_tokens": 10, "output_tokens": 2, "thinking_tokens": 1, "latency_ms": 50,
    }
    assert answer == {"answer": "ok", "technique": "zero_shot", "model": "m1",
                      "retrieved_songs": ["Lofi Study - Chill"], "input_tokens": 10,
                      "output_tokens": 3, "latency_ms": 50}


@pytest.mark.parametrize("error, status", [(LLMTimeoutError("t"), 504), (LLMError("e"), 502)])
def test_failed_calls_are_logged_with_their_status(error, status):
    service, _, log = build_recommendation(llm_error=error)
    with pytest.raises(type(error)):
        service.ask("fiesta", "few_shot")
    assert log.save.call_args.args[0] == {
        "technique": "few_shot", "question": "fiesta", "model": "m1",
        "retrieved_songs": ["Lofi Study - Chill"], "status": status, "error": str(error),
    }


def build_opendata(down=False, saved_path=None):
    mun, dane = Mock(spec=OpenDataSource), Mock(spec=OpenDataSource)
    mun.name, dane.name = "MUN", "DANE"
    for source in (mun, dane):
        if down:
            source.fetch.side_effect = OpenDataUnavailableError("down")
        else:
            source.fetch.return_value = [{"x": 1}]
    store, analytics = Mock(spec=DatasetStore), Mock(spec=AnalyticsPort)
    store.save.return_value = "fresh.json"
    store.path_for.return_value = saved_path
    analytics.municipalities_by_department.return_value = ["by"]
    analytics.municipalities_summary.return_value = {"s": 1}
    analytics.culture_studies.return_value = ["st"]
    analytics.culture_studies_summary.return_value = {"c": 2}
    return OpenDataService(mun, dane, store, analytics), analytics


def test_opendata_results_with_fresh_data():
    service, analytics = build_opendata()
    assert service.municipalities_stats() == {"source": "MUN", "from_cache": False,
                                              "by_department": ["by"], "summary": {"s": 1}}
    assert service.culture_studies_stats() == {"source": "DANE", "from_cache": False,
                                               "studies": ["st"], "summary": {"c": 2}}
    analytics.culture_studies.assert_called_once_with("fresh.json")


def test_opendata_uses_saved_copy_path_when_source_is_down():
    service, analytics = build_opendata(down=True, saved_path="old.json")
    assert service.culture_studies_stats()["from_cache"] is True
    analytics.culture_studies_summary.assert_called_once_with("old.json")


# ---------------- segunda ronda: mutantes que sobrevivieron al primer análisis ----------------

def test_retrieve_default_limit_is_eight():
    from app.domain.recommendation.rag import retrieve_songs
    catalog = [Song(id=i, title=f"Rock {i}", artist="X", genre="Rock", duration_seconds=100) for i in range(12)]
    assert len(retrieve_songs("rock", catalog)) == 8


def test_songs_without_album_do_not_match_placeholder_text():
    """Si el álbum es None no debe quedar texto como 'None' dentro de lo que se busca."""
    from app.domain.recommendation.rag import retrieve_songs
    no_album = Song(id=1, title="Take Five", artist="Brubeck", genre="Jazz", duration_seconds=10)
    other = Song(id=2, title="Gasolina", artist="Daddy Yankee", album="Barrio Fino", genre="Reggaeton", duration_seconds=10)
    assert retrieve_songs("none", [no_album, other]) == [no_album, other]   # ninguna coincide: catálogo completo
    assert retrieve_songs("xxxx", [no_album, other]) == [no_album, other]


def test_llm_receives_the_system_instruction():
    from app.domain.recommendation.prompts import SYSTEM_INSTRUCTION
    service, llm, _ = build_recommendation()
    service.ask("fiesta", "zero_shot")
    assert llm.ask.call_args.args[1] == SYSTEM_INSTRUCTION


def test_rate_limit_call_is_logged_with_the_error_message():
    from app.domain.recommendation.ports import LLMRateLimitError
    service, _, log = build_recommendation(llm_error=LLMRateLimitError("limite de Gemini"))
    with pytest.raises(LLMRateLimitError):
        service.ask("fiesta", "few_shot")
    entry = log.save.call_args.args[0]
    assert entry["status"] == 429 and entry["error"] == "limite de Gemini"


def test_service_errors_carry_the_right_details():
    from app.application.auth_service import AuthService
    from app.domain.identity.ports import PasswordHasher, TokenService, UserRepository
    from app.domain.identity.user import User

    repo = Mock(spec=SongRepository)
    repo.get.return_value = None
    with pytest.raises(SongNotFoundError, match="Song with id 99 not found"):
        SongService(repo).get(99)

    users, tokens = Mock(spec=UserRepository), Mock(spec=TokenService)
    auth = AuthService(users, Mock(spec=PasswordHasher), tokens)
    with pytest.raises(InvalidRoleError, match="Unknown role 'ROOT'"):
        auth.register("laura", "clave-larga-1", "ROOT")
    tokens.decode.return_value = {"sub": "fantasma"}
    users.get_by_username.return_value = None
    with pytest.raises(InvalidTokenError) as exc:
        auth.current_user("jwt")
    assert str(exc.value) == "User in token no longer exists"
    users.get_by_username.assert_called_with("fantasma")
    with pytest.raises(PermissionDeniedError, match="requires the ADMIN role"):
        AuthService.require_role(User("u", "h", "USER"), "ADMIN")


def test_is_admin():
    from app.domain.identity.user import User
    assert User("a", "h", "ADMIN").is_admin()
    assert not User("u", "h", "USER").is_admin()
