"""
medir_tiempos.py - Compara agregar canciones AL INICIO usando:
  - nuestra Playlist (lista doblemente enlazada, app/playlist.py)
  - una list normal de Python con insert(0, x)

Ejecutar desde la carpeta del proyecto:  python scripts/medir_tiempos.py
Cada medición se repite 3 veces y se muestra el promedio en milisegundos.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.playlist import Playlist  # noqa: E402

TAMANOS = [1000, 5000, 10000, 50000, 100000]
REPETICIONES = 3


def tiempo_playlist(n):
    p = Playlist("prueba")
    inicio = time.perf_counter()
    for i in range(n):
        p.agregar_al_inicio("cancion " + str(i))
    return (time.perf_counter() - inicio) * 1000


def tiempo_list(n):
    lista = []
    inicio = time.perf_counter()
    for i in range(n):
        lista.insert(0, "cancion " + str(i))
    return (time.perf_counter() - inicio) * 1000


print("canciones | playlist enlazada (ms) | list de Python (ms)")
for n in TAMANOS:
    a = sum(tiempo_playlist(n) for _ in range(REPETICIONES)) / REPETICIONES
    b = sum(tiempo_list(n) for _ in range(REPETICIONES)) / REPETICIONES
    print(f"{n:>9} | {a:>22.2f} | {b:>19.2f}")
