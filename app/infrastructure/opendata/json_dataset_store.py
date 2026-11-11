"""
json_dataset_store.py - ADAPTADOR de DatasetStore: guarda cada fuente como archivo JSON en la carpeta data/.

Ese JSON es el que luego lee DuckDB, y también sirve de respaldo si la API se cae.
"""
import json
import os
import re
from typing import List, Optional

from app.domain.opendata.ports import DatasetStore


class JsonDatasetStore(DatasetStore):

    def __init__(self, folder: str):
        self.folder = folder

    def _file(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        return os.path.join(self.folder, f"{slug}.json")

    def save(self, name: str, records: List[dict]) -> str:
        os.makedirs(self.folder, exist_ok=True)
        path = self._file(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False)
        return path

    def path_for(self, name: str) -> Optional[str]:
        path = self._file(name)
        return path if os.path.exists(path) else None
