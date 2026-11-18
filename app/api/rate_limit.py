"""
rate_limit.py - Límite de solicitudes por cliente (OWASP API4 y API6).

Ventana deslizante en memoria: cada IP puede hacer como máximo N solicitudes en X segundos.
Se usa en el login (frena ataques de fuerza bruta) y en el asistente de IA (cada llamada cuesta dinero).
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:

    def __init__(self, max_requests: int, window_seconds: float, clock=time.monotonic):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self.hits = defaultdict(deque)  # ip -> momentos de sus últimas solicitudes

    def check(self, key: str) -> None:
        now = self.clock()
        hits = self.hits[key]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()  # se olvidan las solicitudes que ya salieron de la ventana
        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0])) + 1
            raise HTTPException(status_code=429, detail="Too many requests. Try again later.",
                                headers={"Retry-After": str(retry_after)})
        hits.append(now)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def limit(limiter_name: str):
    """Crea una dependencia de FastAPI que aplica el limitador guardado en app.state.limiters."""
    def dependency(request: Request) -> None:
        request.app.state.limiters[limiter_name].check(client_ip(request))
    return dependency
