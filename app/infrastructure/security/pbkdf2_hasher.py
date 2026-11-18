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
MAX_ITERATIONS = 5_000_000  # un valor guardado más alto se rechaza (evita que un hash dañado bloquee la CPU)


class Pbkdf2PasswordHasher(PasswordHasher):

    def __init__(self, iterations: int = DEFAULT_ITERATIONS):
        self.iterations = iterations  # las pruebas usan menos iteraciones para ir rápido

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return f"pbkdf2_sha256${self.iterations}${salt.hex()}${digest.hex()}"

    def verify(self, password: str, stored_hash: str) -> bool:
        # Mejora tomada de la sugerencia de GitHub Copilot (Guía 7): si el valor guardado está dañado
        # (iteraciones que no son número, sal que no es hexadecimal) se responde False en vez de un error 500.
        try:
            algorithm, iterations_text, salt_hex, digest_hex = stored_hash.split("$")
            iterations = int(iterations_text)
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256" or not 1 <= iterations <= MAX_ITERATIONS:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        # compare_digest compara en tiempo constante (evita ataques de tiempo)
        return hmac.compare_digest(digest.hex(), digest_hex)
