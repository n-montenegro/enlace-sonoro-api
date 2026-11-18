"""
auth.py - ADAPTADOR DE ENTRADA (HTTP): registro, login y perfil.

  POST /api/v1/auth/register -> crea una cuenta. SIEMPRE con rol USER (el cliente no puede elegir rol)
  POST /api/v1/auth/login    -> devuelve un JWT (formulario OAuth2, compatible con el botón Authorize)
  GET  /api/v1/auth/me       -> endpoint de prueba para el rol USER: datos del usuario del token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_auth_service
from app.api.rate_limit import limit
from app.api.security import require_role
from app.application.auth_service import AuthService
from app.domain.identity.errors import InvalidCredentialsError, UserAlreadyExistsError
from app.domain.identity.user import USER, User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    # extra="forbid": si alguien envía {"role": "ADMIN"} la petición se rechaza (OWASP API3)
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_.-]+$", examples=["laura"])
    password: str = Field(..., min_length=8, max_length=128, description="At least 8 characters")


class UserOut(BaseModel):
    """Lo que la API muestra de un usuario. El hash de la contraseña NUNCA sale."""
    username: str = Field(..., examples=["laura"])
    role: str = Field(..., examples=["USER"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


def to_out(user: User) -> UserOut:
    return UserOut(username=user.username, role=user.role)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create an account",
             description="Creates a new account with the **USER** role. Clients cannot choose their role.",
             responses={409: {"description": "Username already taken"}},
             dependencies=[Depends(limit("auth"))])
def register(data: RegisterRequest, auth: AuthService = Depends(get_auth_service)):
    try:
        return to_out(auth.register(data.username, data.password, USER))
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/login", response_model=TokenOut, summary="Log in and get a JWT",
             description="OAuth2 password flow. Returns a JWT that expires in 30 minutes. "
                         "Limited to 5 attempts per minute per client.",
             responses={401: {"description": "Incorrect username or password"},
                        429: {"description": "Too many login attempts"}},
             dependencies=[Depends(limit("auth"))])
def login(form: OAuth2PasswordRequestForm = Depends(), auth: AuthService = Depends(get_auth_service)):
    try:
        return TokenOut(access_token=auth.login(form.username, form.password))
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc), headers={"WWW-Authenticate": "Bearer"})


@router.get("/me", response_model=UserOut, summary="Current user (USER role test endpoint)",
            description="Returns the user identified by the token. Requires any valid token (USER or ADMIN).",
            responses={401: {"description": "Missing, invalid or expired token"}})
def me(user: User = Depends(require_role(USER))):
    return to_out(user)
