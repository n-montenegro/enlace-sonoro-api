"""
auth_service.py - Casos de uso de autenticación y autorización.

Recibe por CONSTRUCTOR sus 3 dependencias (puertos del dominio):
  users  -> repositorio de usuarios
  hasher -> protege y verifica contraseñas
  tokens -> crea y valida los JWT
"""
from app.domain.identity.errors import (InvalidCredentialsError, InvalidRoleError, InvalidTokenError,
                                        PermissionDeniedError)
from app.domain.identity.ports import PasswordHasher, TokenService, UserRepository
from app.domain.identity.user import ROLES, USER, User


class AuthService:

    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService):
        self.users = users
        self.hasher = hasher
        self.tokens = tokens

    def register(self, username: str, password: str, role: str = USER) -> User:
        if role not in ROLES:
            raise InvalidRoleError(role)
        user = User(username=username.strip().lower(), password_hash=self.hasher.hash(password), role=role)
        return self.users.add(user)

    def login(self, username: str, password: str) -> str:
        user = self.users.get_by_username(username.strip().lower())
        # Mismo error si el usuario no existe o si la contraseña está mal (no revela qué usuarios existen)
        if user is None or not self.hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError()
        return self.tokens.create(user)

    def current_user(self, token: str) -> User:
        data = self.tokens.decode(token)  # el TokenService ya exige que exista "sub"
        user = self.users.get_by_username(data["sub"])
        if user is None:
            raise InvalidTokenError("User in token no longer exists")
        return user

    @staticmethod
    def require_role(user: User, role: str) -> None:
        """ADMIN puede todo; para lo demás el rol debe coincidir."""
        if user.is_admin() or user.role == role:
            return
        raise PermissionDeniedError(role)

    def count_users(self) -> int:
        return self.users.count()
