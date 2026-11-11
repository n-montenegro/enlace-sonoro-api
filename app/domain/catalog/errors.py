"""errors.py - Errores del negocio del catálogo (no son errores HTTP)."""


class SongNotFoundError(Exception):
    def __init__(self, song_id: int):
        super().__init__(f"Song with id {song_id} not found")
        self.song_id = song_id


class DuplicateSongError(Exception):
    def __init__(self):
        super().__init__("A song with this title and artist already exists")
