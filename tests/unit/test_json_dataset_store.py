import json
from pathlib import Path

from app.infrastructure.opendata.json_dataset_store import JsonDatasetStore


def test_save_creates_folder_and_returns_normalized_json_path(tmp_path: Path):
    folder = tmp_path / "datasets"
    store = JsonDatasetStore(str(folder))

    path = store.save("Datos DANE / Cultura!", [{"title": "Consumo cultural"}])

    assert path == str(folder / "datos_dane_cultura.json")
    assert folder.is_dir()
    assert json.loads((folder / "datos_dane_cultura.json").read_text(encoding="utf-8")) == [
        {"title": "Consumo cultural"}
    ]


def test_save_preserves_unicode_in_json_file(tmp_path: Path):
    store = JsonDatasetStore(str(tmp_path))
    records = [{"municipio": "Bogotá", "nombre": "Chía"}]

    path = store.save("DIVIPOLA", records)
    contents = Path(path).read_text(encoding="utf-8")

    assert "Bogotá" in contents
    assert json.loads(contents) == records


def test_path_for_returns_none_when_dataset_does_not_exist(tmp_path: Path):
    store = JsonDatasetStore(str(tmp_path))

    assert store.path_for("Datos DANE") is None


def test_path_for_returns_path_after_save(tmp_path: Path):
    store = JsonDatasetStore(str(tmp_path))
    saved_path = store.save("DIVIPOLA", [])

    assert store.path_for("DIVIPOLA") == saved_path
    

def test_dataset_name_with_accents_is_readable(tmp_path: Path):
    store = JsonDatasetStore(str(tmp_path))
    path = store.save("DANE - Música", [])
    assert path.endswith("dane_musica.json")