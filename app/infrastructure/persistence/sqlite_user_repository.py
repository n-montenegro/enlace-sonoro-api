"""sqlite_user_repository.py - ADAPTADOR de UserRepository con SQLite (tabla users)."""
import sqlite3
from typing import Optional

from app.domain.identity.errors import UserAlreadyExistsError
from app.domain.identity.ports import UserRepository
from app.domain.identity.user import User


class SqliteUserRepository(UserRepository):

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self._connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK (role IN ('ADMIN', 'USER'))
            )
            """
        )
        conn.commit()
        conn.close()

    def add(self, user: User) -> User:
        conn = self._connect()
        try:
            # Consulta parametrizada (?): evita inyección SQL
            cursor = conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                  (user.username, user.password_hash, user.role))
            conn.commit()
            user.id = cursor.lastrowid
            return user
        except sqlite3.IntegrityError:
            raise UserAlreadyExistsError(user.username)
        finally:
            conn.close()

    def get_by_username(self, username: str) -> Optional[User]:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row is None:
                return None
            return User(**dict(row))  # misma corrección que en SqliteSongRepository
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._connect()
        try:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        finally:
            conn.close()
