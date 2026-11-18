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
