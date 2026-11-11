"""
circuit_breaker.py - Circuit breaker con 3 estados y retry con backoff exponencial.

CIRCUIT BREAKER (como el "taco" de la luz de una casa):
  CLOSED    -> todo normal, las llamadas pasan. Se cuentan los fallos seguidos.
  OPEN      -> hubo demasiados fallos: NO se llama a la API, se rechaza de inmediato.
               Así no seguimos golpeando un servidor caído ni hacemos esperar al usuario.
  HALF_OPEN -> pasó el tiempo de espera: se deja pasar UNA llamada de prueba.
               Si funciona -> CLOSED. Si falla -> OPEN otra vez.

RETRY CON BACKOFF EXPONENCIAL:
  Si una llamada falla por un error temporal, se reintenta esperando cada vez el doble:
  0.5 s, 1 s, 2 s... (base * 2^intento). Así se le da tiempo al servidor de recuperarse.
"""
import logging
import time
from datetime import datetime

from app.domain.opendata.ports import OpenDataUnavailableError

logger = logging.getLogger("enlace_sonoro.resilience")

CLOSED = "CLOSED"
OPEN = "OPEN"
HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(OpenDataUnavailableError):
    """Se rechazó la llamada porque el circuito está abierto."""


class CircuitBreaker:

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30,
                 clock=time.monotonic):
        self.name = name
        self.failure_threshold = failure_threshold  # fallos seguidos para abrir el circuito
        self.recovery_timeout = recovery_timeout    # segundos que se espera antes de probar de nuevo
        self.clock = clock                          # se inyecta para poder probarlo sin esperar de verdad
        self.state = CLOSED
        self.failures = 0
        self.opened_at = None
        self.history = []  # cambios de estado, sirve como evidencia

    def _change_state(self, new_state: str) -> None:
        if new_state != self.state:
            self.history.append({"time": datetime.now().strftime("%H:%M:%S"),
                                 "from": self.state, "to": new_state})
            logger.warning("[%s] circuit breaker: %s -> %s", self.name, self.state, new_state)
            self.state = new_state

    def call(self, func):
        """Ejecuta func() protegida por el circuit breaker."""
        if self.state == OPEN:
            if self.clock() - self.opened_at >= self.recovery_timeout:
                self._change_state(HALF_OPEN)
            else:
                raise CircuitOpenError(f"Circuit for '{self.name}' is OPEN: call rejected without contacting the API")

        try:
            result = func()
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _on_failure(self) -> None:
        self.failures += 1
        if self.state == HALF_OPEN or self.failures >= self.failure_threshold:
            self.opened_at = self.clock()
            self._change_state(OPEN)

    def _on_success(self) -> None:
        self.failures = 0
        self._change_state(CLOSED)

    def status(self) -> dict:
        return {"name": self.name, "state": self.state, "consecutive_failures": self.failures,
                "failure_threshold": self.failure_threshold, "recovery_timeout_s": self.recovery_timeout,
                "history": self.history}


class TemporaryError(Exception):
    """Error que vale la pena reintentar (servidor caído, timeout, HTTP 5xx o 429)."""


def retry_with_backoff(func, retries: int = 3, base_delay: float = 0.5, sleep=time.sleep):
    """
    Llama a func(). Si lanza TemporaryError, reintenta hasta 'retries' veces
    esperando base_delay * 2^intento segundos (0.5, 1, 2...).
    Devuelve el resultado o lanza el último error.
    """
    for attempt in range(retries + 1):
        try:
            return func()
        except TemporaryError as exc:
            if attempt == retries:
                raise
            wait = base_delay * (2 ** attempt)
            logger.warning("Intento %d falló (%s). Reintentando en %.1f s", attempt + 1, exc, wait)
            sleep(wait)
