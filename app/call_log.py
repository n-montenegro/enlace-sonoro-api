"""
call_log.py - Registra cada llamada al LLM en logs/llm_calls.jsonl.

Cada línea del archivo es un JSON con la fecha, la técnica, la pregunta, la respuesta,
los tokens y la latencia. Sirve como EVIDENCIA de las llamadas reales que pide la guía
y como base para la estimación de costos.
La ruta se puede cambiar con la variable LLM_LOG_PATH (las pruebas usan un archivo temporal).
"""
import json
import os
from datetime import datetime, timezone
from typing import List


def get_log_path() -> str:
    return os.getenv("LLM_LOG_PATH", os.path.join("logs", "llm_calls.jsonl"))


def save_call(entry: dict) -> None:
    path = get_log_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_calls() -> List[dict]:
    path = get_log_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
