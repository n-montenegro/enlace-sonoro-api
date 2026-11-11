"""
jsonl_call_log.py - ADAPTADOR del puerto CallLogPort: guarda cada llamada al LLM en un archivo .jsonl.

Cada línea del archivo es un JSON con la fecha, la técnica, la pregunta, la respuesta,
los tokens y la latencia. Sirve como evidencia de las llamadas reales.
"""
import json
import os
from datetime import datetime, timezone
from typing import List

from app.domain.recommendation.ports import CallLogPort


class JsonlCallLog(CallLogPort):

    def __init__(self, path: str):
        self.path = path

    def save(self, entry: dict) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_all(self) -> List[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
