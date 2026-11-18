"""
security.py - Dependencias de FastAPI para autenticación (JWT) y autorización por roles (RBAC).

  get_current_user  -> lee el token "Authorization: Bearer <jwt>" y devuelve el usuario (401 si no es válido)
  require_role(rol) -> además exige un rol (403 si no lo tiene)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies import get_auth_service
from app.application.auth_service import AuthService
from app.domain.identity.errors import InvalidTokenError, PermissionDeniedError
from app.domain.identity.user import User

# tokenUrl hace que aparezca el botón "Authorize" en Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme),
                     auth: AuthService = Depends(get_auth_service)) -> User:
    try:
        return auth.current_user(token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc),
                            headers={"WWW-Authenticate": "Bearer"})


def require_role(role: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        try:
            AuthService.require_role(user, role)
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
        return user
    return dependency
