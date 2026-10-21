"""
llm_client.py - Cliente para llamar al LLM (Google Gemini) por su API REST.

No usamos un SDK: hacemos la petición HTTP directamente con httpx.
Así se ve claramente que nuestra API REST consume OTRA API REST.

Configuración (archivo .env, que NUNCA se sube a GitHub):
    GEMINI_API_KEY = la clave creada en aistudio.google.com
    GEMINI_MODEL   = nombre del modelo (por defecto gemini-3.1-flash-lite)

Errores que lanza este módulo (el router los convierte en códigos HTTP):
    LLMConfigError    -> falta la API key                    -> 503
    LLMTimeoutError   -> Gemini tardó demasiado              -> 504
    LLMRateLimitError -> se superó el límite (HTTP 429)      -> 429
    LLMError          -> cualquier otro error de Gemini      -> 502
"""
import os
import time

import httpx

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.1-flash-lite"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 2           # reintentos si Gemini está saturado (HTTP 500/503)
RETRY_WAIT_SECONDS = 3    # espera antes de reintentar (se duplica en cada intento)


class LLMError(Exception):
    """Error general al llamar al LLM."""


class LLMConfigError(LLMError):
    """Falta configurar la API key."""


class LLMTimeoutError(LLMError):
    """El LLM no respondió a tiempo."""


class LLMRateLimitError(LLMError):
    """Se superó el límite de solicitudes (HTTP 429)."""


def get_model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def ask_gemini(prompt: str, system_instruction: str) -> dict:
    """
    Envía un prompt a Gemini y devuelve un diccionario con:
        text, input_tokens, output_tokens, thinking_tokens, latency_ms, model
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMConfigError("GEMINI_API_KEY is not configured. Create a .env file (see .env.example).")

    model = get_model()
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    for attempt in range(MAX_RETRIES + 1):
        start = time.perf_counter()
        try:
            response = httpx.post(GEMINI_URL.format(model=model), json=body, headers=headers, timeout=TIMEOUT_SECONDS)
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Gemini did not respond within {TIMEOUT_SECONDS} seconds")
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not connect to Gemini: {exc}")
        latency_ms = round((time.perf_counter() - start) * 1000)

        # 500/503 = Gemini saturado temporalmente: esperamos y reintentamos
        if response.status_code in (500, 503) and attempt < MAX_RETRIES:
            time.sleep(RETRY_WAIT_SECONDS * (2 ** attempt))
            continue
        break

    if response.status_code == 429:
        raise LLMRateLimitError("Gemini rate limit exceeded (HTTP 429). Wait a minute and try again.")
    if response.status_code != 200:
        # Gemini devuelve el detalle del error en JSON: {"error": {"message": ...}}
        try:
            message = response.json()["error"]["message"]
        except Exception:
            message = response.text[:200]
        raise LLMError(f"Gemini returned HTTP {response.status_code}: {message}")

    data = response.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError):
        raise LLMError("Gemini returned an empty answer (it may have been blocked by safety filters)")

    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "input_tokens": usage.get("promptTokenCount", 0),
        "output_tokens": usage.get("candidatesTokenCount", 0),
        "thinking_tokens": usage.get("thoughtsTokenCount", 0),  # algunos modelos "piensan" antes de responder
        "latency_ms": latency_ms,
        "model": model,
    }
