"""postgres_user_repository.py - ADAPTADOR de UserRepository con PostgreSQL (tabla users, Guía 8)."""
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from app.domain.identity.errors import UserAlreadyExistsError
from app.domain.identity.ports import UserRepository
from app.domain.identity.user import User


class PostgresUserRepository(UserRepository):

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      TEXT   NOT NULL UNIQUE,
                    password_hash TEXT   NOT NULL,
                    role          TEXT   NOT NULL CHECK (role IN ('ADMIN', 'USER'))
                )
                """
            )

    def add(self, user: User) -> User:
        try:
            with self._connect() as conn:
                # %s = consulta parametrizada: psycopg envía los valores aparte del SQL (evita inyección SQL)
                row = conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
                    (user.username, user.password_hash, user.role),
                ).fetchone()
        except psycopg.errors.UniqueViolation:
            raise UserAlreadyExistsError(user.username)
        user.id = row["id"]
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        with self._connect() as conn:
            row = conn.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s",
                               (username,)).fetchone()
        return User(**row) if row else None

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
