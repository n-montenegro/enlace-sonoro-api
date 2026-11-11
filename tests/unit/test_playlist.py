"""Pruebas de la playlist como lista doblemente enlazada."""
from app.domain.playback.playlist import Playlist


def test_agregar_y_orden():
    p = Playlist("Para estudiar")
    p.agregar_al_final("Clair de Lune")
    p.agregar_al_final("Weightless")
    p.agregar_al_inicio("Snowman")
    assert p.a_lista() == ["Snowman", "Clair de Lune", "Weightless"]
    assert p.tamano == 3


def test_siguiente_anterior_e_historial():
    p = Playlist("Relajarme")
    for c in ["A", "B", "C"]:
        p.agregar_al_final(c)
    assert p.reproducir() == "A"
    assert p.siguiente() == "B"
    assert p.siguiente() == "C"
    assert p.siguiente() is None      # no hay más canciones
    assert p.anterior() == "B"
    assert p.ver_historial() == ["B", "C", "B", "A"]  # la más reciente primero


def test_eliminar():
    p = Playlist("Mix")
    for c in ["A", "B", "C"]:
        p.agregar_al_final(c)
    assert p.eliminar("B") is True
    assert p.a_lista() == ["A", "C"]
    assert p.eliminar("Z") is False
    p.eliminar("A")
    p.eliminar("C")
    assert p.esta_vacia()
    assert p.cabeza is None and p.cola is None
