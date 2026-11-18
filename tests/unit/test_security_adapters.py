"""test_security_adapters.py - Hasher PBKDF2, servicio JWT y limitador de solicitudes."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from app.api.rate_limit import RateLimiter
from app.domain.identity.errors import InvalidTokenError
from app.domain.identity.user import User
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.pbkdf2_hasher import DEFAULT_ITERATIONS, MAX_ITERATIONS, Pbkdf2PasswordHasher

SECRET = "x" * 40


def test_hash_is_salted_and_verifiable():
    hasher = Pbkdf2PasswordHasher(iterations=1_000)
    first, second = hasher.hash("mi-clave-123"), hasher.hash("mi-clave-123")
    assert first != second                      # sal distinta en cada hash
    assert "mi-clave-123" not in first          # nunca se guarda en texto plano
    assert hasher.verify("mi-clave-123", first)
    assert not hasher.verify("otra-clave", first)
    assert not hasher.verify("mi-clave-123", "formato-invalido")


def test_damaged_stored_hash_is_rejected_without_crashing():
    """Regresión (evaluación de Copilot): antes estos valores lanzaban ValueError y el login daba error 500."""
    hasher = Pbkdf2PasswordHasher(iterations=1_000)
    good = hasher.hash("mi-clave-123")
    _, _, salt_hex, digest_hex = good.split("$")
    assert not hasher.verify("mi-clave-123", f"pbkdf2_sha256$mil${salt_hex}${digest_hex}")    # iteraciones no numéricas
    assert not hasher.verify("mi-clave-123", f"pbkdf2_sha256$1000$zz${digest_hex}")            # sal no hexadecimal
    assert not hasher.verify("mi-clave-123", f"pbkdf2_sha256$0${salt_hex}${digest_hex}")       # cero iteraciones
    assert not hasher.verify("mi-clave-123", f"pbkdf2_sha256${MAX_ITERATIONS + 1}${salt_hex}${digest_hex}")  # demasiado caro
    assert not hasher.verify("mi-clave-123", f"md5$1000${salt_hex}${digest_hex}")              # otro algoritmo


def test_default_iterations_follow_owasp_recommendation():
    assert DEFAULT_ITERATIONS >= 600_000


def test_jwt_roundtrip_contains_username_and_role():
    tokens = JwtTokenService(SECRET)
    data = tokens.decode(tokens.create(User(username="laura", password_hash="h", role="USER")))
    assert data["sub"] == "laura" and data["role"] == "USER"


def test_expired_token_is_rejected():
    past = lambda: datetime.now(timezone.utc) - timedelta(hours=2)  # noqa: E731
    old_token = JwtTokenService(SECRET, expires_minutes=30, now=past).create(User("laura", "h"))
    with pytest.raises(InvalidTokenError, match="expired"):
        JwtTokenService(SECRET).decode(old_token)


def test_token_signed_with_other_secret_is_rejected():
    forged = JwtTokenService("y" * 40).create(User("laura", "h", "ADMIN"))
    with pytest.raises(InvalidTokenError):
        JwtTokenService(SECRET).decode(forged)


def test_alg_none_token_is_rejected():
    """Ataque clásico: un token sin firma ("alg": "none") no debe ser aceptado."""
    unsigned = jwt.encode({"sub": "laura", "role": "ADMIN", "exp": 9999999999}, key=None, algorithm="none")
    with pytest.raises(InvalidTokenError):
        JwtTokenService(SECRET).decode(unsigned)


def test_short_secret_is_not_allowed():
    with pytest.raises(ValueError):
        JwtTokenService("corta")


def test_rate_limiter_blocks_and_then_recovers():
    now = [0.0]
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=lambda: now[0])
    limiter.check("1.2.3.4")
    limiter.check("1.2.3.4")
    with pytest.raises(HTTPException) as exc:
        limiter.check("1.2.3.4")
    assert exc.value.status_code == 429
    limiter.check("5.6.7.8")  # otra IP no se ve afectada
    now[0] = 61               # pasa la ventana de 60 s
    limiter.check("1.2.3.4")
