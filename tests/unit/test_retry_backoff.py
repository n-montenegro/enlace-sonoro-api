"""test_retry_backoff.py - El retry espera 0.5, 1, 2... segundos (backoff exponencial)."""
import pytest

from app.infrastructure.resilience.circuit_breaker import TemporaryError, retry_with_backoff


def test_waits_grow_exponentially_and_then_succeeds():
    waits = []
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 4:
            raise TemporaryError("HTTP 503")
        return "ok"

    assert retry_with_backoff(flaky, retries=3, base_delay=0.5, sleep=waits.append) == "ok"
    assert waits == [0.5, 1.0, 2.0]


def test_gives_up_after_max_retries():
    waits = []

    def always_fails():
        raise TemporaryError("timeout")

    with pytest.raises(TemporaryError):
        retry_with_backoff(always_fails, retries=2, base_delay=1, sleep=waits.append)
    assert waits == [1, 2]


def test_non_temporary_errors_are_not_retried():
    waits = []

    def bad_request():
        raise ValueError("404")

    with pytest.raises(ValueError):
        retry_with_backoff(bad_request, retries=3, sleep=waits.append)
    assert waits == []
