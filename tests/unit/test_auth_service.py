"""test_auth_service.py - Pruebas UNITARIAS de AuthService con unittest.mock (sin base de datos)."""
from unittest.mock import Mock

import pytest

from app.application.auth_service import AuthService
from app.domain.identity.errors import (InvalidCredentialsError, InvalidRoleError, InvalidTokenError,
                                        PermissionDeniedError)
from app.domain.identity.ports import PasswordHasher, TokenService, UserRepository
from app.domain.identity.user import ADMIN, USER, User


def build():
    users, hasher, tokens = Mock(spec=UserRepository), Mock(spec=PasswordHasher), Mock(spec=TokenService)
    return AuthService(users, hasher, tokens), users, hasher, tokens


def test_register_stores_hash_not_password_and_normalizes_username():
    service, users, hasher, _ = build()
    hasher.hash.return_value = "HASH"
    users.add.side_effect = lambda u: u

    user = service.register("  Laura ", "secreta-123")

    assert user.username == "laura"
    assert user.password_hash == "HASH"
    assert user.role == USER
    hasher.hash.assert_called_once_with("secreta-123")


def test_register_rejects_unknown_role():
    service, users, _, _ = build()
    with pytest.raises(InvalidRoleError):
        service.register("laura", "secreta-123", "SUPERADMIN")
    users.add.assert_not_called()


def test_login_returns_token_when_password_is_right():
    service, users, hasher, tokens = build()
    stored = User(username="laura", password_hash="HASH")
    users.get_by_username.return_value = stored
    hasher.verify.return_value = True
    tokens.create.return_value = "jwt"

    assert service.login("LAURA", "secreta-123") == "jwt"
    users.get_by_username.assert_called_once_with("laura")
    hasher.verify.assert_called_once_with("secreta-123", "HASH")
    tokens.create.assert_called_once_with(stored)


def test_login_fails_for_wrong_password_or_unknown_user():
    service, users, hasher, tokens = build()
    users.get_by_username.return_value = User(username="laura", password_hash="HASH")
    hasher.verify.return_value = False
    with pytest.raises(InvalidCredentialsError):
        service.login("laura", "mala")
    users.get_by_username.return_value = None
    with pytest.raises(InvalidCredentialsError):
        service.login("nadie", "mala")
    tokens.create.assert_not_called()


def test_current_user_from_token():
    service, users, _, tokens = build()
    tokens.decode.return_value = {"sub": "laura", "role": USER}
    users.get_by_username.return_value = User(username="laura", password_hash="H")
    assert service.current_user("jwt").username == "laura"


def test_current_user_fails_if_user_was_deleted():
    service, users, _, tokens = build()
    tokens.decode.return_value = {"sub": "laura"}
    users.get_by_username.return_value = None
    with pytest.raises(InvalidTokenError):
        service.current_user("jwt")


def test_role_rules():
    admin, user = User("a", "h", ADMIN), User("u", "h", USER)
    AuthService.require_role(admin, ADMIN)
    AuthService.require_role(admin, USER)  # ADMIN también puede lo de USER
    AuthService.require_role(user, USER)
    with pytest.raises(PermissionDeniedError):
        AuthService.require_role(user, ADMIN)


def test_count_users_delegates_to_repository():
    service, users, _, _ = build()
    users.count.return_value = 7
    assert service.count_users() == 7


# ---------- Guía 8: primer ADMIN en producción (variables ADMIN_USERNAME / ADMIN_PASSWORD) ----------

def test_ensure_admin_creates_first_admin_when_there_are_no_users():
    service, users, hasher, _ = build()
    users.count.return_value = 0
    hasher.hash.return_value = "HASH"
    users.add.side_effect = lambda u: u

    assert service.ensure_admin("Admin", "una-clave-muy-larga") is True

    created = users.add.call_args.args[0]
    assert (created.username, created.role, created.password_hash) == ("admin", ADMIN, "HASH")


def test_ensure_admin_does_nothing_if_users_already_exist():
    service, users, _, _ = build()
    users.count.return_value = 1
    assert service.ensure_admin("admin", "una-clave-muy-larga") is False
    users.add.assert_not_called()


def test_ensure_admin_does_nothing_without_credentials():
    service, users, _, _ = build()
    users.count.return_value = 0
    assert service.ensure_admin("", "una-clave-muy-larga") is False
    assert service.ensure_admin("admin", "") is False
    users.add.assert_not_called()
    users.count.assert_not_called()  # ni siquiera consulta la base de datos


def test_ensure_admin_requires_a_long_password():
    service, users, hasher, _ = build()
    users.count.return_value = 0
    users.add.side_effect = lambda u: u
    with pytest.raises(ValueError, match="at least 12 characters"):
        service.ensure_admin("admin", "corta-11ch!")       # 11 caracteres
    users.add.assert_not_called()
    assert service.ensure_admin("admin", "justo-12cars") is True  # 12 caracteres: se acepta
