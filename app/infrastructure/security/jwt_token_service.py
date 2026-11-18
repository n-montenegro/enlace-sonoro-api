"""
jwt_token_service.py - ADAPTADOR de TokenService con JSON Web Tokens (librería PyJWT).

- Firma HS256 con una clave secreta que viene del archivo .env (JWT_SECRET), nunca del código.
- El token expira (por defecto 30 minutos).
- Al validar se fija el algoritmo permitido (evita el ataque de cambiar "alg" a "none").
"""
from datetime import datetime, timedelta, timezone

import jwt

from app.domain.identity.errors import InvalidTokenError
from app.domain.identity.ports import TokenService
from app.domain.identity.user import User

ALGORITHM = "HS256"


class JwtTokenService(TokenService):

    def __init__(self, secret: str, expires_minutes: int = 30, now=lambda: datetime.now(timezone.utc)):
        if len(secret) < 32:
            raise ValueError("JWT secret must have at least 32 characters")
        self.secret = secret
        self.expires_minutes = expires_minutes
        self.now = now  # se inyecta para poder probar la expiración

    def create(self, user: User) -> str:
        issued = self.now()
        payload = {"sub": user.username, "role": user.role, "iat": issued,
                   "exp": issued + timedelta(minutes=self.expires_minutes)}
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)

    def decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret, algorithms=[ALGORITHM],
                              options={"require": ["sub", "exp"]})
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
