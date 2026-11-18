"""
pbkdf2_hasher.py - ADAPTADOR de PasswordHasher con PBKDF2-HMAC-SHA256 (librería estándar de Python).

Cada contraseña tiene su propia SAL aleatoria, así dos usuarios con la misma contraseña
tienen hashes distintos. 600.000 iteraciones es lo que recomienda OWASP para PBKDF2-SHA256.
Formato guardado:  pbkdf2_sha256$<iteraciones>$<sal hex>$<hash hex>
"""
import hashlib
import hmac
import secrets

from app.domain.identity.ports import PasswordHasher

DEFAULT_ITERATIONS = 600_000


class Pbkdf2PasswordHasher(PasswordHasher):

    def __init__(self, iterations: int = DEFAULT_ITERATIONS):
        self.iterations = iterations  # las pruebas usan menos iteraciones para ir rápido

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return f"pbkdf2_sha256${self.iterations}${salt.hex()}${digest.hex()}"

    def verify(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        # compare_digest compara en tiempo constante (evita ataques de tiempo)
        return hmac.compare_digest(digest.hex(), digest_hex)
