"""
ports.py - Puertos del bounded context "Identity".

  UserRepository  -> dónde se guardan los usuarios (SQLite en infraestructura).
  PasswordHasher  -> cómo se protege la contraseña (PBKDF2 en infraestructura).
  TokenService    -> cómo se crean y validan los tokens (JWT en infraestructura).
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.identity.user import User


class UserRepository(ABC):

    @abstractmethod
    def add(self, user: User) -> User:
        """Guarda el usuario. Lanza UserAlreadyExistsError si el nombre ya existe."""

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Devuelve el usuario o None."""

    @abstractmethod
    def count(self) -> int:
        """Número de usuarios registrados."""


class PasswordHasher(ABC):

    @abstractmethod
    def hash(self, password: str) -> str:
        """Devuelve el hash (con su sal) listo para guardar."""

    @abstractmethod
    def verify(self, password: str, stored_hash: str) -> bool:
        """True si la contraseña corresponde al hash guardado."""


class TokenService(ABC):

    @abstractmethod
    def create(self, user: User) -> str:
        """Crea un token firmado para el usuario."""

    @abstractmethod
    def decode(self, token: str) -> dict:
        """Valida el token y devuelve sus datos (sub, role). Lanza InvalidTokenError si no es válido."""
