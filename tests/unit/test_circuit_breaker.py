"""
test_circuit_breaker.py - Prueba los 3 estados del circuit breaker.

Se inyecta un reloj falso para "adelantar el tiempo" sin esperar de verdad.
"""
import pytest

from app.infrastructure.resilience.circuit_breaker import (CLOSED, HALF_OPEN, OPEN, CircuitBreaker,
                                                           CircuitOpenError)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def fail():
    raise ConnectionError("API caída")


def ok():
    return "datos"


def test_full_cycle_closed_open_half_open_closed():
    clock = FakeClock()
    cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=30, clock=clock)
    assert cb.state == CLOSED

    for _ in range(3):  # 3 fallos seguidos -> se abre
        with pytest.raises(ConnectionError):
            cb.call(fail)
    assert cb.state == OPEN

    with pytest.raises(CircuitOpenError):  # abierto: se rechaza sin llamar a la función
        cb.call(ok)

    clock.now = 31  # pasa el tiempo de recuperación
    assert cb.call(ok) == "datos"  # llamada de prueba en HALF_OPEN que funciona
    assert cb.state == CLOSED
    assert [h["to"] for h in cb.history] == [OPEN, HALF_OPEN, CLOSED]


def test_failure_in_half_open_opens_again():
    clock = FakeClock()
    cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=10, clock=clock)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            cb.call(fail)
    clock.now = 11
    with pytest.raises(ConnectionError):
        cb.call(fail)  # HALF_OPEN -> falla -> OPEN
    assert cb.state == OPEN
    assert [h["to"] for h in cb.history] == [OPEN, HALF_OPEN, OPEN]


def test_success_resets_failure_counter():
    cb = CircuitBreaker("test", failure_threshold=3)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            cb.call(fail)
    cb.call(ok)
    assert cb.failures == 0 and cb.state == CLOSED
