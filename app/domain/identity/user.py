"""
user.py - Entidad User del bounded context "Identity" (autenticación y roles).

Roles (RBAC = Role-Based Access Control):
  ADMIN -> administra el catálogo y ve información interna (registro de llamadas a la IA).
  USER  -> consulta el catálogo y usa el asistente musical.
"""
from dataclasses import dataclass
from typing import Optional

ADMIN = "ADMIN"
USER = "USER"
ROLES = (ADMIN, USER)


@dataclass
class User:
    username: str
    password_hash: str  # NUNCA la contraseña en texto plano
    role: str = USER
    id: Optional[int] = None

    def is_admin(self) -> bool:
        return self.role == ADMIN
