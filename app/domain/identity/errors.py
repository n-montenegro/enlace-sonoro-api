"""errors.py - Errores del negocio de Identity (el router los traduce a 401/403/409)."""


class InvalidCredentialsError(Exception):
    """Usuario o contraseña incorrectos. El mensaje es el mismo en ambos casos
    para no revelar qué usuarios existen (OWASP API2)."""

    def __init__(self):
        super().__init__("Incorrect username or password")


class InvalidTokenError(Exception):
    """El token no es válido, fue alterado o ya expiró."""

    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(reason)


class PermissionDeniedError(Exception):
    """El usuario está autenticado pero su rol no le permite esta acción."""

    def __init__(self, required_role: str):
        super().__init__(f"This action requires the {required_role} role")
        self.required_role = required_role


class UserAlreadyExistsError(Exception):
    def __init__(self, username: str):
        super().__init__(f"Username '{username}' is already taken")


class InvalidRoleError(Exception):
    def __init__(self, role: str):
        super().__init__(f"Unknown role '{role}'")
