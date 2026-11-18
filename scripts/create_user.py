"""
create_user.py - Crea un usuario desde la terminal (así se crea el primer ADMIN).

La contraseña se escribe de forma oculta (getpass): no queda en el código, ni en el historial
de la terminal, ni en GitHub.

Ejecutar desde la carpeta del proyecto:
    python scripts/create_user.py admin ADMIN
    python scripts/create_user.py laura USER

Con PostgreSQL (docker-compose o Render) se define antes la variable DATABASE_URL, por ejemplo:
    $env:DATABASE_URL="postgresql://enlace:clave@localhost:5432/enlace_sonoro"   (PowerShell)
"""
import getpass
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.application.auth_service import AuthService  # noqa: E402
from app.domain.identity.errors import InvalidRoleError, UserAlreadyExistsError  # noqa: E402
from app.infrastructure.persistence.postgres_user_repository import PostgresUserRepository  # noqa: E402
from app.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository  # noqa: E402
from app.infrastructure.security.jwt_token_service import JwtTokenService  # noqa: E402
from app.infrastructure.security.pbkdf2_hasher import Pbkdf2PasswordHasher  # noqa: E402

if len(sys.argv) != 3:
    raise SystemExit("Uso: python scripts/create_user.py <usuario> <ADMIN|USER>")

username, role = sys.argv[1], sys.argv[2].upper()
password = getpass.getpass("Contraseña (no se ve al escribir): ")
if len(password) < 8:
    raise SystemExit("La contraseña debe tener al menos 8 caracteres.")
if password != getpass.getpass("Repite la contraseña: "):
    raise SystemExit("Las contraseñas no coinciden.")

if os.getenv("DATABASE_URL"):
    repository = PostgresUserRepository(os.environ["DATABASE_URL"])
else:
    repository = SqliteUserRepository(os.getenv("DB_PATH", "enlace_sonoro.db"))
repository.init_schema()
# Aquí no se crean tokens, por eso basta una clave temporal para construir el servicio
service = AuthService(repository, Pbkdf2PasswordHasher(), JwtTokenService(secrets.token_urlsafe(48)))
try:
    user = service.register(username, password, role)
    print(f"Usuario '{user.username}' creado con rol {user.role}.")
except (UserAlreadyExistsError, InvalidRoleError) as exc:
    raise SystemExit(f"Error: {exc}")
