"""
playlist.py - Bounded context "Reproducción": playlist implementada como LISTA DOBLEMENTE ENLAZADA.

Cada canción se guarda en un Nodo que apunta a la canción siguiente y a la anterior.
Así, pasar a la siguiente o volver a la anterior no requiere recorrer la lista.

Complejidad de las operaciones:
  agregar_al_inicio  -> O(1)
  agregar_al_final   -> O(1)  (guardamos la referencia a la cola)
  siguiente/anterior -> O(1)
  eliminar(titulo)   -> O(n)  (hay que buscar la canción)

El historial de reproducción es una lista enlazada simple donde la canción
más reciente queda de primera (se inserta al inicio en O(1)).
"""


class Nodo:
    def __init__(self, cancion):
        self.cancion = cancion
        self.siguiente = None
        self.anterior = None


class Playlist:
    def __init__(self, nombre):
        self.nombre = nombre
        self.cabeza = None    # primera canción
        self.cola = None      # última canción
        self.actual = None    # canción que está sonando
        self.tamano = 0
        self.historial = None # cabeza de la lista enlazada del historial

    def esta_vacia(self):
        return self.tamano == 0

    def agregar_al_inicio(self, cancion):
        nuevo = Nodo(cancion)
        if self.esta_vacia():
            self.cabeza = self.cola = nuevo
        else:
            nuevo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo
            self.cabeza = nuevo
        self.tamano += 1

    def agregar_al_final(self, cancion):
        nuevo = Nodo(cancion)
        if self.esta_vacia():
            self.cabeza = self.cola = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
            self.cola = nuevo
        self.tamano += 1

    def eliminar(self, cancion):
        """Quita la primera canción igual a 'cancion'. Devuelve True si la encontró."""
        nodo = self.cabeza
        while nodo is not None:
            if nodo.cancion == cancion:
                if nodo.anterior:
                    nodo.anterior.siguiente = nodo.siguiente
                else:
                    self.cabeza = nodo.siguiente
                if nodo.siguiente:
                    nodo.siguiente.anterior = nodo.anterior
                else:
                    self.cola = nodo.anterior
                if self.actual is nodo:
                    self.actual = nodo.siguiente
                self.tamano -= 1
                return True
            nodo = nodo.siguiente
        return False

    def _registrar_en_historial(self, cancion):
        nuevo = Nodo(cancion)
        nuevo.siguiente = self.historial
        self.historial = nuevo

    def reproducir(self):
        """Empieza desde la primera canción si no hay ninguna sonando."""
        if self.actual is None:
            self.actual = self.cabeza
        if self.actual is not None:
            self._registrar_en_historial(self.actual.cancion)
            return self.actual.cancion
        return None

    def siguiente(self):
        if self.actual and self.actual.siguiente:
            self.actual = self.actual.siguiente
            self._registrar_en_historial(self.actual.cancion)
            return self.actual.cancion
        return None  # no hay más canciones

    def anterior(self):
        if self.actual and self.actual.anterior:
            self.actual = self.actual.anterior
            self._registrar_en_historial(self.actual.cancion)
            return self.actual.cancion
        return None

    def a_lista(self):
        """Recorre la playlist y devuelve las canciones en orden (útil para mostrar)."""
        canciones = []
        nodo = self.cabeza
        while nodo is not None:
            canciones.append(nodo.cancion)
            nodo = nodo.siguiente
        return canciones

    def ver_historial(self):
        canciones = []
        nodo = self.historial
        while nodo is not None:
            canciones.append(nodo.cancion)
            nodo = nodo.siguiente
        return canciones
